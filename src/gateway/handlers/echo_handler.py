"""回声处理器示例。"""

from src.gateway.filters.base import BotContext
from src.gateway.handlers.base import BaseHandler, HandlerResponse, HandlerResult
from src.gateway.core.protocol import MessageEvent, EventType
from src.gateway.core.protocol.schemas import MessageType
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

    logger.info(f"回声消息: {echo_text}")

    # 这里应该调用 API 发送消息，暂时只记录日志
    # TODO: 实现消息发送功能

    return HandlerResponse(
      result=HandlerResult.SUCCESS,
      message=f"回声: {echo_text}",
      data={"echo_text": echo_text, "user_id": event.user_id},
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
