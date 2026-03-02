"""过滤器基类和过滤器链实现。

用于 QQ 机器人网关层，处理来自 Milky 反向 WebSocket 协议的事件。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.utils.logger import logger


class BaseFilter(ABC):
    """过滤器基类。

    所有过滤器都应继承此类并实现 process 方法。
    过滤器可以对 QQ 事件进行预处理、验证、增强、过滤等操作。
    """

    def __init__(self, name: Optional[str] = None, priority: int = 100):
        """初始化过滤器。

        Args:
            name: 过滤器名称，用于日志和调试。如果未提供，使用类名。
            priority: 过滤器优先级，数值越小优先级越高。默认为 100。
        """
        self.name = name or self.__class__.__name__
        self.priority = priority
        self.enabled = True

    @abstractmethod
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理 QQ 事件数据。

        Args:
            context: 事件上下文字典，包含事件数据和元信息。
                    典型结构：
                    {
                        "event": {...},           # Milky 协议的原始事件数据
                        "event_type": "message",  # 事件类型（message/notice/request等）
                        "bot_id": "123456",       # 机器人 QQ 号
                        "user_id": "789012",      # 用户 QQ 号（如果有）
                        "group_id": "345678",     # 群号（如果有）
                        "message": "...",         # 消息内容（如果是消息事件）
                        "metadata": {...},        # 自定义元数据
                        "stop": False,            # 是否停止后续过滤器执行
                        "skip_handler": False     # 是否跳过事件处理器
                    }

        Returns:
            处理后的上下文字典。可以修改、增强或过滤事件数据。

        Raises:
            Exception: 处理过程中的任何异常。
        """
        pass

    def enable(self) -> None:
        """启用过滤器。"""
        self.enabled = True
        logger.debug(f"过滤器 {self.name} 已启用")

    def disable(self) -> None:
        """禁用过滤器。"""
        self.enabled = False
        logger.debug(f"过滤器 {self.name} 已禁用")


class FilterChain:
    """过滤器链，按优先级顺序执行多个过滤器。"""

    def __init__(self, name: str = "default"):
        """初始化过滤器链。

        Args:
            name: 过滤器链名称。
        """
        self.name = name
        self.filters: List[BaseFilter] = []

    def add_filter(self, filter_instance: BaseFilter) -> "FilterChain":
        """添加过滤器到链中，并按优先级自动排序。

        Args:
            filter_instance: 过滤器实例。

        Returns:
            返回自身，支持链式调用。
        """
        self.filters.append(filter_instance)
        # 按优先级排序，数值越小优先级越高
        self.filters.sort(key=lambda f: f.priority)
        logger.debug(
            f"过滤器链 {self.name} 添加过滤器: {filter_instance.name} "
            f"(优先级: {filter_instance.priority})"
        )
        return self

    def remove_filter(self, filter_name: str) -> bool:
        """从链中移除指定名称的过滤器。

        Args:
            filter_name: 过滤器名称。

        Returns:
            是否成功移除。
        """
        for i, f in enumerate(self.filters):
            if f.name == filter_name:
                self.filters.pop(i)
                logger.debug(f"过滤器链 {self.name} 移除过滤器: {filter_name}")
                return True
        return False

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行过滤器链，按优先级顺序处理事件。

        Args:
            context: 初始事件上下文。

        Returns:
            经过所有过滤器处理后的上下文。
        """
        event_type = context.get("event_type", "unknown")
        logger.debug(f"开始执行过滤器链: {self.name} (事件类型: {event_type})")

        for filter_instance in self.filters:
            if not filter_instance.enabled:
                logger.debug(f"跳过已禁用的过滤器: {filter_instance.name}")
                continue

            try:
                logger.debug(
                    f"执行过滤器: {filter_instance.name} "
                    f"(优先级: {filter_instance.priority})"
                )
                context = await filter_instance.process(context)

                # 检查是否需要停止后续过滤器执行
                if context.get("stop", False):
                    logger.info(
                        f"过滤器 {filter_instance.name} 请求停止链执行 "
                        f"(skip_handler: {context.get('skip_handler', False)})"
                    )
                    break

            except Exception as e:
                logger.error(
                    f"过滤器 {filter_instance.name} 执行失败: {e}",
                    exc_info=True
                )
                context["error"] = str(e)
                context["failed_filter"] = filter_instance.name
                context["stop"] = True
                break

        logger.debug(f"过滤器链 {self.name} 执行完成")
        return context

    def clear(self) -> None:
        """清空过滤器链。"""
        self.filters.clear()
        logger.debug(f"过滤器链 {self.name} 已清空")

    def get_filters(self) -> List[str]:
        """获取所有过滤器名称列表。

        Returns:
            过滤器名称列表。
        """
        return [f.name for f in self.filters]
