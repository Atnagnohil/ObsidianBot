"""总结查询处理器。"""

from src.engine.content.base import ContentLayer
from src.engine.content.local import LocalContentProvider
from src.gateway.core.protocol import MessageEvent, EventType
from src.gateway.core.protocol.onebot import bot_adapter
from src.gateway.core.protocol.schemas import MessageType, MessageSegment
from src.gateway.filters.base import BotContext
from src.gateway.handlers.base import BaseHandler, HandlerResponse, HandlerResult
from src.utils.logger import logger


class SummaryHandler(BaseHandler):
  """
  总结查询处理器。

  处理 "总结" 或 "summary" 指令，返回用户或群组的对话总结。
  """

  def __init__(self, priority: int = 20):
    """
    初始化总结查询处理器。

    Args:
        priority: 优先级（设置为 20，高于普通处理器）
    """
    super().__init__(priority)
    self.content_manager = LocalContentProvider()

  async def can_handle(self, context: BotContext) -> bool:
    """
    判断是否可以处理。

    只处理 "总结" 或 "summary" 指令。
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

    # 检查是否为总结指令
    text_lower = text_content.lower().strip()
    return text_lower in ["总结", "summary", "/summary", "/总结"]

  async def handle(self, context: BotContext) -> HandlerResponse:
    """
    处理总结查询请求。

    返回用户或群组的对话总结信息。
    """
    event = context.event
    if not isinstance(event, MessageEvent):
      return HandlerResponse(
        result=HandlerResult.FAILED, message="事件类型不匹配"
      )

    # 确定层级
    if event.group_id:
      layer = ContentLayer.GROUP
      target_id = str(event.group_id)
      target_type = "群组"
    else:
      layer = ContentLayer.USER
      target_id = str(event.user_id)
      target_type = "用户"

    logger.info(f"查询{target_type}总结: {target_id}")

    # 获取总结信息
    if layer == ContentLayer.GROUP:
      summary_data = self.content_manager.group_info.get(target_id)
    else:
      summary_data = self.content_manager.user_info.get(target_id)

    # 构建回复消息
    if summary_data:
      reply_text = self._format_summary(summary_data, target_type)
    else:
      reply_text = f"暂无{target_type}总结信息，可能是：\n1. 对话数量不足\n2. 尚未触发自动总结\n3. 总结功能未完全启用"

    reply_message = [
      MessageSegment(type=MessageType.TEXT, data={"text": reply_text})
    ]

    # 发送消息
    try:
      if event.message_type == "group":
        result = await bot_adapter.send_group_msg(event.group_id, reply_message)
      else:
        result = await bot_adapter.send_private_msg(event.user_id, reply_message)

      if result.get("status") == "ok":
        return HandlerResponse(
          result=HandlerResult.SUCCESS,
          message=reply_text,
          data={"summary": summary_data, "target_id": target_id},
        )
      else:
        error_msg = result.get("message", "未知错误")
        logger.warning(f"发送总结消息失败: {error_msg}")
        return HandlerResponse(
          result=HandlerResult.FAILED,
          message=f"发送失败: {error_msg}",
          data={"error": result},
        )

    except Exception as e:
      logger.error(f"发送总结消息异常: {e}", exc_info=True)
      return HandlerResponse(
        result=HandlerResult.FAILED, message=f"发送异常: {e}"
      )

  def _format_summary(self, summary_data: dict, target_type: str) -> str:
    """
    格式化总结数据为可读文本。

    Args:
        summary_data: 总结数据（JSON 格式）
        target_type: 目标类型（用户/群组）

    Returns:
        格式化后的文本
    """
    lines = [f"📊 {target_type}对话总结\n"]

    # 主要话题
    if "main_topics" in summary_data and summary_data["main_topics"]:
      lines.append("🔖 主要话题：")
      for topic in summary_data["main_topics"]:
        lines.append(f"  • {topic}")
      lines.append("")

    # 重要信息
    if "key_information" in summary_data and summary_data["key_information"]:
      lines.append("💡 重要信息：")
      for info in summary_data["key_information"]:
        lines.append(f"  • {info}")
      lines.append("")

    # 用户偏好或群组氛围
    if target_type == "用户":
      if "user_preferences" in summary_data and summary_data["user_preferences"]:
        lines.append("👤 用户特征：")
        for pref in summary_data["user_preferences"]:
          lines.append(f"  • {pref}")
        lines.append("")
    else:
      if "group_atmosphere" in summary_data and summary_data["group_atmosphere"]:
        lines.append("🌟 群组氛围：")
        for atm in summary_data["group_atmosphere"]:
          lines.append(f"  • {atm}")
        lines.append("")

    # 待办事项
    if "pending_items" in summary_data and summary_data["pending_items"]:
      lines.append("📝 待办事项：")
      for item in summary_data["pending_items"]:
        lines.append(f"  • {item}")

    return "\n".join(lines).strip()

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
