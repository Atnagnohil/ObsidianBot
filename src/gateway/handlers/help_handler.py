"""帮助命令处理器。"""

from src.gateway.core.protocol import MessageEvent, EventType
from src.gateway.core.protocol.onebot import bot_adapter
from src.gateway.core.protocol.schemas import MessageType, MessageSegment
from src.gateway.filters.base import BotContext
from src.gateway.handlers.base import BaseHandler, HandlerResponse, HandlerResult
from src.utils.logger import logger


class HelpHandler(BaseHandler):
  """
  帮助命令处理器。

  当消息为 "help"、"帮助"、"/help" 时，返回帮助信息。
  """

  def __init__(self, priority: int = 10):
    """优先级设置为 10，比其他处理器更高"""
    super().__init__(priority)

  async def can_handle(self, context: BotContext) -> bool:
    """
    判断是否可以处理。

    只处理帮助命令。
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

    # 检查是否为帮助命令
    return text_content.lower() in ["help", "帮助", "/help", "？", "?"]

  async def handle(self, context: BotContext) -> HandlerResponse:
    """
    处理帮助命令。

    返回可用命令列表。
    """
    event = context.event
    if not isinstance(event, MessageEvent):
      return HandlerResponse(
        result=HandlerResult.FAILED, message="事件类型不匹配"
      )

    help_text = """🤖 可用命令：

1. help / 帮助 - 显示此帮助信息
2. echo <内容> - 回声消息
3. 回声 <内容> - 回声消息

更多功能开发中..."""

    logger.debug(f"用户 {event.user_id} 请求帮助")

    # 构建回复消息
    reply_message = [MessageSegment(type=MessageType.TEXT, data={"text": help_text})]

    # 发送消息
    try:
      if event.message_type == "group":
        result = await bot_adapter.send_group_msg(event.group_id, reply_message)
      else:
        result = await bot_adapter.send_private_msg(event.user_id, reply_message)

      if result.get("status") == "ok":
        return HandlerResponse(
          result=HandlerResult.SUCCESS,
          message=help_text,
          data={"user_id": event.user_id},
        )
      else:
        error_msg = result.get("message", "未知错误")
        logger.warning(f"发送帮助消息失败: {error_msg}")
        return HandlerResponse(
          result=HandlerResult.FAILED,
          message=f"发送失败: {error_msg}",
          data={"error": result},
        )

    except Exception as e:
      logger.error(f"发送帮助消息异常: {e}", exc_info=True)
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
