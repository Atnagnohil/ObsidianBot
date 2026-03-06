"""上下文内容管理基类。"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List

from src.engine.provider.llm.scheams import MessageRole


class ContentLayer(str, Enum):
  """记忆层级枚举，实际上是不同场景的会话"""
  GROUP = "group"
  USER = "user"


@dataclass
class ContentItem:
  """
  上下文内容项
  """
  msg_id: str
  user_id: str
  group_id: Optional[str]
  role: MessageRole
  content: str
  timestamp: int
  extra_info: Optional[Dict[str, Any]] = None


class BaseContentManager(ABC):
  """
  上下文内容管理基类

  提供上下文内容管理功能，如获取、添加、删除上下文内容，不含系统提示词
  """

  @abstractmethod
  async def add_content(self, content_item: ContentItem, layer: ContentLayer):
    """
    添加上下文内容

    Args:
        content_item: 上下文内容项
        layer: 上下文层级
    """
    pass

  @abstractmethod
  async def get_content(self, user_id: str, group_id: Optional[str], layer: ContentLayer, limit: int = 10) -> List[
    ContentItem]:
    """
    获取上下文内容

    Args:
        user_id: 用户 ID
        group_id: 群组 ID
        layer: 上下文层级
        limit: 最大返回数量

    Returns:
        上下文内容项列表
    """
    pass

  @abstractmethod
  async def clear_content(self, user_id: str, group_id: Optional[str], layer: ContentLayer):
    """
    清除上下文内容

    Args:
        user_id: 用户 ID
        group_id: 群组 ID
        layer: 记忆层级
    """

  pass

  @abstractmethod
  async def extract_content(self, user_id: str, group_id: Optional[str], layer: ContentLayer):
    """
    提取上下文内容

    Args:
        user_id: 用户 ID
        group_id: 群组 ID
        layer: 记忆层级
    """
    pass
