"""反向 WebSocket 服务端实现。

用于接收来自 QQ 机器人协议端（如 Milky）的消息推送。
实现了心跳检测和指数退避重连策略。
"""

import asyncio
import json
from datetime import datetime
from typing import Optional, Callable, Any, Dict, List

from websockets.asyncio.server import serve, ServerConnection
from websockets.exceptions import ConnectionClosed

from src.gateway.core.protocol import BaseEvent
from src.gateway.filters.base import Filter, FilterChain, BotContext
from src.utils.logger import logger


class ReverseWebSocketServer:
  """反向 WebSocket 服务端。

  用于接收 QQ 机器人协议端的连接和消息推送。
  """

  def __init__(
    self,
    host: str = "0.0.0.0",
    port: int = 8080,
    heartbeat_interval: int = 30,
    heartbeat_timeout: int = 10,
    filters: Optional[List[Filter]] = None,
  ):
    """初始化反向 WebSocket 服务端。

    Args:
        host: 监听地址
        port: 监听端口
        heartbeat_interval: 心跳间隔（秒）
        heartbeat_timeout: 心跳超时时间（秒）
        filters: 过滤器列表
    """
    self.host = host
    self.port = port
    self.heartbeat_interval = heartbeat_interval
    self.heartbeat_timeout = heartbeat_timeout

    self.server = None
    self.client: Optional[ServerConnection] = None
    self.is_running = False

    # 心跳相关
    self._last_heartbeat: Optional[datetime] = None
    self._heartbeat_task: Optional[asyncio.Task] = None

    # 过滤器链
    self.filter_chain = FilterChain(filters or [])

    # 消息处理回调
    self.on_message: Optional[Callable[[BotContext], None]] = None
    self.on_connect: Optional[Callable[[], None]] = None
    self.on_disconnect: Optional[Callable[[], None]] = None

  async def start(self) -> None:
    """启动 WebSocket 服务端。"""
    if self.is_running:
      logger.warning("WebSocket 服务端已在运行")
      return

    logger.info(f"启动反向 WebSocket 服务端: {self.host}:{self.port}")
    self.is_running = True

    try:
      async with serve(self._handle_client, self.host, self.port):
        logger.success(f"WebSocket 服务端已启动: ws://{self.host}:{self.port}")
        await asyncio.Future()  # 保持运行
    except Exception as e:
      logger.error(f"WebSocket 服务端启动失败: {e}")
      self.is_running = False
      raise

  async def stop(self) -> None:
    """停止 WebSocket 服务端。"""
    logger.info("正在停止 WebSocket 服务端...")
    self.is_running = False

    if self._heartbeat_task:
      self._heartbeat_task.cancel()

    if self.client:
      await self.client.close()

    logger.info("WebSocket 服务端已停止")

  async def _handle_client(self, websocket: ServerConnection) -> None:
    """处理客户端连接。

    Args:
        websocket: WebSocket 连接对象
    """
    client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"

    # 如果已有客户端连接，拒绝新连接
    if self.client is not None:
      logger.warning(f"拒绝新连接 {client_info}，已有活跃连接")
      await websocket.close(1008, "已有活跃连接")
      return

    self.client = websocket
    self._last_heartbeat = datetime.now()

    logger.success(f"客户端已连接: {client_info}")

    # 触发连接回调
    if self.on_connect:
      try:
        await self.on_connect()
      except Exception as e:
        logger.error(f"连接回调执行失败: {e}")

    # 启动心跳检测
    self._heartbeat_task = asyncio.create_task(self._heartbeat_monitor())

    try:
      async for message in websocket:
        await self._handle_message(message)
    except ConnectionClosed as e:
      logger.warning(f"客户端连接关闭: {client_info} (code={e.code}, reason={e.reason})")
    except Exception as e:
      logger.error(f"处理客户端消息时出错: {e}", exc_info=True)
    finally:
      await self._cleanup_client()

  async def _handle_message(self, message: str) -> None:
    """处理接收到的消息。

    Args:
        message: 接收到的消息内容
    """
    try:
      # 更新心跳时间
      self._last_heartbeat = datetime.now()

      # 解析 JSON 消息
      data = json.loads(message)

      # 打印接收到的消息
      logger.debug(f"收到消息: {json.dumps(data, ensure_ascii=False, indent=2)}")

      # 将消息转换为事件对象
      event = self._parse_event(data)
      if not event:
        logger.warning("无法解析事件，跳过处理")
        return

      # 创建上下文对象
      context = BotContext(event=event)

      # 执行过滤器链
      self.filter_chain.reset()  # 重置过滤器链索引
      passed = await self.filter_chain.do_filter(context)

      if not passed:
        logger.debug(f"事件被过滤器丢弃: {context.drop_reason}")
        return

      # 过滤器通过，触发消息处理回调
      if self.on_message:
        try:
          await self.on_message(context)
        except Exception as e:
          logger.error(f"消息处理回调执行失败: {e}", exc_info=True)

    except json.JSONDecodeError as e:
      logger.error(f"消息解析失败: {e}, 原始消息: {message}")
    except Exception as e:
      logger.error(f"处理消息时出错: {e}", exc_info=True)

  def _parse_event(self, data: Dict[str, Any]) -> Optional[BaseEvent]:
    """解析事件数据。

    Args:
        data: 原始事件数据

    Returns:
        解析后的事件对象，解析失败返回 None
    """
    try:
      from src.gateway.core.protocol import (
        EventType,
        MessageEvent,
        HeartbeatEvent,
        LifeCycleEvent,
      )
      from src.gateway.core.protocol.schemas import Sender, MessageSegment, MessageType

      post_type = data.get("post_type")
      if not post_type:
        return None

      # 解析基础字段
      time = data.get("time", 0)
      self_id = data.get("self_id", 0)

      # 根据事件类型解析
      if post_type in ("message", "message_sent"):
        # 解析消息事件
        sender_data = data.get("sender", {})
        sender = Sender(
          user_id=sender_data.get("user_id", 0),
          nickname=sender_data.get("nickname", ""),
          card=sender_data.get("card", ""),
          sex=sender_data.get("sex", ""),
          age=sender_data.get("age", 0),
          level=sender_data.get("level", ""),
          role=sender_data.get("role", ""),
          title=sender_data.get("title", ""),
          group_id=sender_data.get("group_id", 0),
        )

        # 解析消息段
        message_segments = []
        for seg in data.get("message", []):
          message_segments.append(
            MessageSegment(
              type=MessageType(seg.get("type", "text")),
              data=seg.get("data", {}),
            )
          )

        return MessageEvent(
          time=time,
          self_id=self_id,
          post_type=(
            EventType.MESSAGE
            if post_type == "message"
            else EventType.MESSAGE_SENT
          ),
          message_id=data.get("message_id", 0),
          message_seq=data.get("message_seq", 0),
          real_id=data.get("real_id", 0),
          user_id=data.get("user_id", 0),
          group_id=data.get("group_id", 0),
          message_type=data.get("message_type", ""),
          sub_type=data.get("sub_type", ""),
          sender=sender,
          message=message_segments,
          message_format=data.get("message_format", ""),
          raw_message=data.get("raw_message", ""),
          font=data.get("font", 0),
          target_id=data.get("target_id", 0),
          temp_source=data.get("temp_source", 0),
        )

      elif post_type == "meta_event":
        meta_event_type = data.get("meta_event_type")
        if meta_event_type == "heartbeat":
          return HeartbeatEvent(
            time=time,
            self_id=self_id,
            post_type=EventType.META_EVENT,
            status=data.get("status", {}),
            interval=data.get("interval", 0),
          )
        elif meta_event_type == "lifecycle":
          return LifeCycleEvent(
            time=time,
            self_id=self_id,
            post_type=EventType.META_EVENT,
            meta_event_type=meta_event_type,
            sub_type=data.get("sub_type", ""),
          )

      # 其他事件类型，返回基础事件
      return BaseEvent(
        time=time,
        self_id=self_id,
        post_type=EventType(post_type),
      )

    except Exception as e:
      logger.error(f"解析事件失败: {e}", exc_info=True)
      return None

  async def _heartbeat_monitor(self) -> None:
    """心跳监控任务。"""
    logger.debug("心跳监控已启动")

    try:
      while self.is_running and self.client:
        await asyncio.sleep(self.heartbeat_interval)

        if not self._last_heartbeat:
          continue

        # 检查心跳超时
        elapsed = (datetime.now() - self._last_heartbeat).total_seconds()
        if elapsed > self.heartbeat_timeout + self.heartbeat_interval:
          logger.warning(f"心跳超时 ({elapsed:.1f}s)，关闭连接")
          await self.client.close(1001, "心跳超时")
          break

        logger.debug(f"心跳正常 (距上次: {elapsed:.1f}s)")

    except asyncio.CancelledError:
      logger.debug("心跳监控已取消")
    except Exception as e:
      logger.error(f"心跳监控出错: {e}", exc_info=True)

  async def _cleanup_client(self) -> None:
    """清理客户端连接。"""
    if self._heartbeat_task:
      self._heartbeat_task.cancel()
      self._heartbeat_task = None

    self.client = None
    self._last_heartbeat = None

    logger.info("客户端连接已清理")

    # 触发断开回调
    if self.on_disconnect:
      try:
        await self.on_disconnect()
      except Exception as e:
        logger.error(f"断开回调执行失败: {e}")

  async def send(self, data: Dict[str, Any]) -> bool:
    """发送消息给客户端。

    Args:
        data: 要发送的数据（字典格式）

    Returns:
        是否发送成功
    """
    if not self.client:
      logger.warning("无活跃连接，无法发送消息")
      return False

    try:
      message = json.dumps(data, ensure_ascii=False)
      await self.client.send(message)
      logger.debug(f"发送消息: {message}")
      return True
    except Exception as e:
      logger.error(f"发送消息失败: {e}")
      return False
