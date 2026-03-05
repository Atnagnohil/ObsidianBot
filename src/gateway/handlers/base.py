"""处理器基类定义。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from src.gateway.filters.base import BotContext


class HandlerResult(str, Enum):
  """处理器执行结果"""

  SUCCESS = "success"  # 处理成功
  FAILED = "failed"  # 处理失败
  SKIPPED = "skipped"  # 跳过处理


@dataclass
class HandlerResponse:
  """处理器响应"""

  result: HandlerResult  # 处理结果
  message: str = ""  # 响应消息
  data: Optional[dict] = None  # 额外数据


class BaseHandler(ABC):
  """处理器抽象基类"""

  def __init__(self, priority: int = 100):
    """
    初始化处理器。

    Args:
        priority: 优先级，数值越小优先级越高
    """
    self.priority = priority
    self.name = self.__class__.__name__

  @abstractmethod
  async def can_handle(self, context: BotContext) -> bool:
    """
    判断是否可以处理该上下文。

    Args:
        context: 上下文对象

    Returns:
        True 可以处理，False 不能处理
    """
    pass

  @abstractmethod
  async def handle(self, context: BotContext) -> HandlerResponse:
    """
    处理消息。

    Args:
        context: 上下文对象

    Returns:
        处理响应
    """
    pass
