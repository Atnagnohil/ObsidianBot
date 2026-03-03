from src.gateway.core.protocol import EventType
from src.utils.logger import logger
from .base import Filter, BotContext, FilterResult, FilterChain


class ContentFilter(Filter):
  """
  内容过滤器，过滤掉非
  """

  async def do_filter(self, context: BotContext, chain: FilterChain) -> FilterResult:
    logger.debug(f"[过滤器] 内容过滤器: {context.event.post_type}")
    # 如果不是消息事件，直接 DROP
    if context.event.post_type not in (EventType.MESSAGE, EventType.MESSAGE_SENT):
      context.drop(f"非消息事件: {context.event.post_type}")
      return FilterResult.DROP

    # 类型转换为 MessageEvent
    from src.gateway.core.protocol.schemas import MessageEvent, MessageType

    if not isinstance(context.event, MessageEvent):
      context.drop("事件类型不匹配")
      return FilterResult.DROP

    # 检查消息段中是否包含文本消息
    has_text = any(segment.type == MessageType.TEXT for segment in context.event.message)

    if not has_text:
      context.drop("非文本消息")
      return FilterResult.DROP

    # 是文本消息，通过
    return FilterResult.PASS
