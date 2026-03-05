"""回声处理器示例。"""

from src.gateway.core.protocol import MessageEvent, EventType
from src.gateway.core.protocol.onebot import bot_adapter
from src.gateway.core.protocol.schemas import MessageType, MessageSegment
from src.gateway.filters.base import BotContext
from src.gateway.handlers.base import BaseHandler, HandlerResponse, HandlerResult
from src.utils.logger import logger


class EchoHandler(BaseHandler):
  """
  回声处理器。

  当消息以 "echo " 或 "回声 " 开头时，回复相同的内容。
  """

  def __init__(self, priority: int = 50):
    super().__init__(priority)

  async def can_handle(self, context: BotContext) -> bool:
    """
    判断是否可以处理。

    只处理以 "echo " 或 "回声 " 开头的文本消息。
    """
    # 检查是否为消息事件
    if context.event.post_type not in (EventType.MESSAGE, EventType.MESSAGE_SENT):
      return False

    # 检查是否为 MessageEvent
    if not isinstance(context.event, MessageEvent):
      return False

    # 提取文本内容
    text_content = self._extract_text(context.event)
    if not text_content:
      return False

    # 检查是否以指定前缀开头
    return text_content.startswith("echo ") or text_content.startswith("回声 ")

  async def handle(self, context: BotContext) -> HandlerResponse:
    """
    处理回声消息。

    提取 "echo " 或 "回声 " 后面的内容并返回。
    """
    event = context.event
    if not isinstance(event, MessageEvent):
      return HandlerResponse(
        result=HandlerResult.FAILED, message="事件类型不匹配"
      )

    # 提取文本内容
    text_content = self._extract_text(event)

    # 提取要回声的内容
    if text_content.startswith("echo "):
      echo_text = text_content[5:]
    elif text_content.startswith("回声 "):
      echo_text = text_content[3:]
    else:
      echo_text = text_content

    logger.debug(f"回声消息: {echo_text}")

    # 构建回复消息
    reply_message = [MessageSegment(type=MessageType.TEXT, data={"text": echo_text})]

    # 发送消息
    try:
      if event.message_type == "group":
        result = await bot_adapter.send_group_msg(event.group_id, reply_message)
      else:
        result = await bot_adapter.send_private_msg(event.user_id, reply_message)

      if result.get("status") == "ok":
        return HandlerResponse(
          result=HandlerResult.SUCCESS,
          message=f"回声: {echo_text}",
          data={"echo_text": echo_text, "user_id": event.user_id},
        )
      else:
        error_msg = result.get("message", "未知错误")
        logger.warning(f"发送回声消息失败: {error_msg}")
        return HandlerResponse(
          result=HandlerResult.FAILED,
          message=f"发送失败: {error_msg}",
          data={"error": result},
        )

    except Exception as e:
      logger.error(f"发送回声消息异常: {e}", exc_info=True)
      return HandlerResponse(
        result=HandlerResult.FAILED, message=f"发送异常: {e}"
      )

  def _extract_text(self, event: MessageEvent) -> str:
    """
    从消息事件中提取文本内容。

    Args:
        event: 消息事件

    Returns:
        文本内容
    """
    text_parts = []
    for segment in event.message:
      if segment.type == MessageType.TEXT:
        text_parts.append(segment.data.get("text", ""))

    return "".join(text_parts).strip()
