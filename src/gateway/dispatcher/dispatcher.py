"""消息分派器实现。"""

from typing import List, Optional

from src.gateway.filters.base import BotContext
from src.gateway.handlers.base import BaseHandler, HandlerResult, HandlerResponse
from src.utils.logger import logger


class MessageDispatcher:
  """
  消息分派器。

  根据处理器的优先级和 can_handle 判断，将消息分派给合适的处理器。
  """

  def __init__(self, handlers: Optional[List[BaseHandler]] = None):
    """
    初始化分派器。

    Args:
        handlers: 处理器列表
    """
    self.handlers = sorted(handlers or [], key=lambda h: h.priority)

  def register_handler(self, handler: BaseHandler) -> None:
    """
    注册处理器。

    Args:
        handler: 处理器实例
    """
    self.handlers.append(handler)
    self.handlers.sort(key=lambda h: h.priority)
    logger.info(f"注册处理器: {handler.name} (优先级: {handler.priority})")

  def unregister_handler(self, handler_name: str) -> bool:
    """
    注销处理器。

    Args:
        handler_name: 处理器名称

    Returns:
        是否成功注销
    """
    for i, handler in enumerate(self.handlers):
      if handler.name == handler_name:
        self.handlers.pop(i)
        logger.info(f"注销处理器: {handler_name}")
        return True
    return False

  async def dispatch(self, context: BotContext) -> HandlerResponse:
    """
    分派消息到合适的处理器。

    按优先级顺序遍历处理器，找到第一个可以处理的处理器并执行。

    Args:
        context: 上下文对象

    Returns:
        处理响应
    """
    logger.debug(f"开始分派消息，共 {len(self.handlers)} 个处理器")

    for handler in self.handlers:
      try:
        # 检查是否可以处理
        if await handler.can_handle(context):
          logger.info(f"使用处理器: {handler.name}")

          # 执行处理
          response = await handler.handle(context)

          logger.info(
            f"处理器 {handler.name} 执行完成: {response.result.value}"
          )
          return response

      except Exception as e:
        logger.error(f"处理器 {handler.name} 执行异常: {e}", exc_info=True)
        return HandlerResponse(
          result=HandlerResult.FAILED, message=f"处理器异常: {e}"
        )

    # 没有找到合适的处理器
    logger.warning("未找到合适的处理器")
    return HandlerResponse(result=HandlerResult.SKIPPED, message="未找到合适的处理器")

  def list_handlers(self) -> List[str]:
    """
    列出所有已注册的处理器。

    Returns:
        处理器名称列表
    """
    return [handler.name for handler in self.handlers]
