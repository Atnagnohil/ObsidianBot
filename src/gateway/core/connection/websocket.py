"""反向 WebSocket 服务端实现。

用于接收来自 QQ 机器人协议端（如 Milky）的消息推送。
实现了心跳检测和指数退避重连策略。
"""

import asyncio
import json
from typing import Optional, Callable, Any, Dict
from datetime import datetime

from websockets.asyncio.server import serve, ServerConnection
from websockets.exceptions import ConnectionClosed

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
    ):
        """初始化反向 WebSocket 服务端。
        
        Args:
            host: 监听地址
            port: 监听端口
            heartbeat_interval: 心跳间隔（秒）
            heartbeat_timeout: 心跳超时时间（秒）
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
        
        # 消息处理回调
        self.on_message: Optional[Callable[[Dict[str, Any]], None]] = None
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
            logger.info(f"收到消息: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            # 触发消息处理回调
            if self.on_message:
                try:
                    await self.on_message(data)
                except Exception as e:
                    logger.error(f"消息处理回调执行失败: {e}", exc_info=True)
        
        except json.JSONDecodeError as e:
            logger.error(f"消息解析失败: {e}, 原始消息: {message}")
        except Exception as e:
            logger.error(f"处理消息时出错: {e}", exc_info=True)
    
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


# 使用示例
async def main():
    """测试示例。"""
    server = ReverseWebSocketServer(host="0.0.0.0", port=8080)
    
    # 设置回调
    async def on_message(data: Dict[str, Any]):
        logger.info(f"[回调] 处理消息: {data.get('post_type', 'unknown')}")
    
    async def on_connect():
        logger.info("[回调] 客户端已连接")
    
    async def on_disconnect():
        logger.info("[回调] 客户端已断开")
    
    server.on_message = on_message
    server.on_connect = on_connect
    server.on_disconnect = on_disconnect
    
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())
