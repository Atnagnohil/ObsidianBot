"""OneBot 协议适配器实现。"""

from typing import List, Dict, Any, Optional

from src.gateway.core.protocol.schemas import BaseBotAdapter, MessageSegment
from src.utils.config import config
from src.utils.http_client import http
from src.utils.logger import logger


class OneBotBotAdapter(BaseBotAdapter):
  """
  OneBot Bot 适配器（单例模式）。

  实现 OneBot 协议的消息发送功能。
  """

  _instance: Optional["OneBotBotAdapter"] = None
  _initialized: bool = False

  def __new__(cls, base_url: Optional[str] = None, access_token: Optional[str] = None):
    """
    单例模式实现。

    Args:
        base_url: OneBot HTTP API 地址，如果不提供则从配置读取
        access_token: 访问令牌，如果不提供则从配置读取

    Returns:
        OneBotBotAdapter 单例实例
    """
    if cls._instance is None:
      cls._instance = super().__new__(cls)
    return cls._instance

  def __init__(self, base_url: Optional[str] = None, access_token: Optional[str] = None):
    """
    初始化 OneBot 适配器。

    只在第一次创建时初始化，后续调用会跳过。

    Args:
        base_url: OneBot HTTP API 地址，如果不提供则从配置读取
        access_token: 访问令牌，如果不提供则从配置读取
    """
    # 如果已经初始化过，直接返回
    if self._initialized:
      return

    # 从配置读取 OneBot 配置
    onebot_config = config.get("onebot", {})

    self.base_url = base_url or onebot_config.get("base_url", "http://localhost:3000")
    self.access_token = access_token or onebot_config.get("access_token", "")

    # 移除末尾的斜杠
    self.base_url = self.base_url.rstrip("/")

    self._initialized = True
    logger.info(f"OneBot 适配器已初始化（单例）: {self.base_url}")

  def _get_headers(self) -> Dict[str, str]:
    """
    获取请求头。

    Returns:
        请求头字典
    """
    headers = {"Content-Type": "application/json"}

    if self.access_token:
      headers["Authorization"] = f"Bearer {self.access_token}"

    return headers

  def _build_message_payload(
    self, message: List[MessageSegment]
  ) -> List[Dict[str, Any]]:
    """
    构建消息载荷。

    Args:
        message: 消息段列表

    Returns:
        消息载荷列表
    """
    payload = []
    for segment in message:
      payload.append({"type": segment.type.value, "data": segment.data})

    return payload

  async def send_group_msg(
    self, group_id: int, message: List[MessageSegment]
  ) -> Dict[str, Any]:
    """
    发送群消息。

    Args:
        group_id: 群号
        message: 消息段列表

    Returns:
        API 响应结果
    """
    url = f"{self.base_url}/send_group_msg"
    payload = {
      "group_id": group_id,
      "message": self._build_message_payload(message),
    }

    try:
      logger.debug(f"发送群消息到 {group_id}: {payload}")
      response = await http.async_post(url, json=payload, headers=self._get_headers())

      # 检查 HTTP 状态码
      if response.status_code != 200:
        logger.error(
          f"HTTP 请求失败: status_code={response.status_code}, body={response.text}"
        )
        return {
          "status": "failed",
          "retcode": response.status_code,
          "message": f"HTTP {response.status_code}: {response.text}",
        }

      # 尝试解析 JSON
      try:
        result = response.json()
      except Exception as json_error:
        logger.error(f"JSON 解析失败: {json_error}, 响应内容: {response.text}")
        return {
          "status": "failed",
          "retcode": -1,
          "message": f"JSON 解析失败: {response.text[:200]}",
        }

      if result.get("status") == "ok":
        logger.debug(
          f"群消息发送成功: {group_id}, message_id={result.get('data', {}).get('message_id')}"
        )
      else:
        logger.error(f"群消息发送失败: {result}")

      return result

    except Exception as e:
      logger.error(f"发送群消息异常: {e}", exc_info=True)
      return {"status": "failed", "retcode": -1, "message": str(e)}

  async def send_private_msg(
    self, user_id: int, message: List[MessageSegment]
  ) -> Dict[str, Any]:
    """
    发送私聊消息。

    Args:
        user_id: 用户 QQ 号
        message: 消息段列表

    Returns:
        API 响应结果
    """
    url = f"{self.base_url}/send_private_msg"
    payload = {
      "user_id": user_id,
      "message": self._build_message_payload(message),
    }

    try:
      logger.debug(f"发送私聊消息到 {user_id}: {payload}")
      response = await http.async_post(url, json=payload, headers=self._get_headers())

      # 检查 HTTP 状态码
      if response.status_code != 200:
        logger.error(
          f"HTTP 请求失败: status_code={response.status_code}, body={response.text}"
        )
        return {
          "status": "failed",
          "retcode": response.status_code,
          "message": f"HTTP {response.status_code}: {response.text}",
        }

      # 尝试解析 JSON
      try:
        result = response.json()
      except Exception as json_error:
        logger.error(f"JSON 解析失败: {json_error}, 响应内容: {response.text}")
        return {
          "status": "failed",
          "retcode": -1,
          "message": f"JSON 解析失败: {response.text[:200]}",
        }

      if result.get("status") == "ok":
        logger.debug(
          f"私聊消息发送成功: {user_id}, message_id={result.get('data', {}).get('message_id')}"
        )
      else:
        logger.error(f"私聊消息发送失败: {result}")

      return result

    except Exception as e:
      logger.error(f"发送私聊消息异常: {e}", exc_info=True)
      return {"status": "failed", "retcode": -1, "message": str(e)}

  async def send_text_message(
    self, target_id: int, text: str, is_group: bool = False
  ) -> Dict[str, Any]:
    """
    发送纯文本消息的便捷方法。

    Args:
        target_id: 目标 ID（群号或用户 QQ 号）
        text: 文本内容
        is_group: 是否为群消息

    Returns:
        API 响应结果
    """
    from src.gateway.core.protocol.schemas import MessageType

    message = [MessageSegment(type=MessageType.TEXT, data={"text": text})]

    if is_group:
      return await self.send_group_msg(target_id, message)
    else:
      return await self.send_private_msg(target_id, message)

  async def check_health(self) -> bool:
    """
    检查 OneBot 服务健康状态。

    Returns:
        True 服务正常，False 服务异常
    """
    try:
      # 尝试获取登录信息
      url = f"{self.base_url}/get_login_info"
      response = await http.async_get(url, headers=self._get_headers())

      if response.status_code == 200:
        try:
          result = response.json()
          if result.get("status") == "ok":
            data = result.get("data", {})
            logger.success(
              f"OneBot 服务连接成功: user_id={data.get('user_id')}, nickname={data.get('nickname')}"
            )
            return True
          else:
            logger.warning(f"OneBot 服务响应异常: {result}")
            return False
        except Exception as e:
          logger.error(f"解析健康检查响应失败: {e}")
          return False
      else:
        logger.error(
          f"OneBot 服务健康检查失败: HTTP {response.status_code}, {response.text}"
        )
        return False

    except Exception as e:
      logger.error(f"OneBot 服务连接失败: {e}")
      logger.warning(
        f"请检查配置: base_url={self.base_url}, 确保 OneBot HTTP 服务已启动"
      )
      return False


# 导出全局单例实例
bot_adapter = OneBotBotAdapter()
