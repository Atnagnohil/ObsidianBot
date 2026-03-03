from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from src.gateway.core.protocol import BaseEvent


class FilterResult(str, Enum):
  """过滤器执行结果"""
  PASS = "pass"  # 通过，继续执行下一个过滤器
  DROP = "drop"  # 丢弃事件，不再执行任何后续逻辑


@dataclass
class BotContext:
  """上下文对象"""
  event: BaseEvent  # 原始事件对象
  is_dropped: bool = False  # 是否被丢弃
  drop_reason: str = ""  # 丢弃原因
  metadata: dict = None  # 额外的元数据

  def __post_init__(self):
    """初始化后处理"""
    if self.metadata is None:
      self.metadata = {}

  def drop(self, reason: str = ""):
    """
    丢弃事件，不再执行后续逻辑
    :param reason: 丢弃原因
    """
    self.is_dropped = True
    self.drop_reason = reason

  def set_metadata(self, key: str, value):
    """
    设置元数据
    :param key: 键
    :param value: 值
    """
    self.metadata[key] = value

  def get_metadata(self, key: str, default=None):
    """
    获取元数据
    :param key: 键
    :param default: 默认值
    :return: 元数据值
    """
    return self.metadata.get(key, default)


class Filter(ABC):
  """过滤器抽象类"""

  def __init__(self, order: int = 100):
    self.order = order
    self.name = self.__class__.__name__

  @abstractmethod
  async def do_filter(self, context: BotContext, chain: FilterChain) -> FilterResult:
    """
    执行过滤器
    :param context: 上下文对象
    :param chain: 过滤器链
    :return: FilterResult.PASS 继续执行，FilterResult.DROP 丢弃事件
    """
    pass


class FilterChain:
  """过滤器链"""

  def __init__(self, filters: list[Filter]):
    """
    初始化过滤器链
    :param filters: 过滤器列表
    """
    self.filters = sorted(filters, key=lambda f: f.order)
    self.index = 0

  async def do_filter(self, context: BotContext) -> bool:
    """
    执行过滤器链
    :param context: 上下文对象
    :return: True 所有过滤器通过，False 事件被丢弃
    """
    # 如果已经被丢弃，直接返回 False
    if context.is_dropped:
      return False

    # 还有过滤器需要执行
    if self.index < len(self.filters):
      current = self.filters[self.index]
      self.index += 1

      try:
        # 执行当前过滤器
        result = await current.do_filter(context, self)

        # 如果过滤器返回 DROP，标记为丢弃并停止执行
        if result == FilterResult.DROP:
          if not context.is_dropped:
            context.drop(f"Filter {current.name} dropped")
          return False

        # 如果返回 PASS，继续执行下一个过滤器
        return await self.do_filter(context)
      except Exception as e:
        # 过滤器异常，记录并丢弃
        context.drop(f"Filter {current.name} exception: {e}")
        raise
    else:
      # 所有过滤器都通过
      return True

  def reset(self):
    """重置过滤器链索引，用于复用"""
    self.index = 0
