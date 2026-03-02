"""协议基础定义，包含标准事件上下文数据类。"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, List


class EventType(str, Enum):
  """消息类型枚举"""

  # 机器人离线
  BOT_OFFLINE = "bot_offline"
  # 消息接收
  MESSAGE_RECEIVE = "message_receive"
  # 消息撤回
  MESSAGE_RECALL = "message_recall"
  # 好友请求
  FRIEND_REQUEST = "friend_request"
  # 入群请求
  GROUP_JOIN_REQUEST = "group_join_request"
  # 群成员邀请他人入群请求
  GROUP_INVITED_JOIN_REQUEST = "group_invited_join_request"
  # 他人邀请自身入群
  GROUP_INVITATION = "group_invitation"
  # 好友戳一戳
  FRIEND_NUDGE = "friend_nudge"
  # 群好友文件上传
  FRIEND_FILE_UPLOAD = "friend_file_upload"
  # 群管理员变更
  GROUP_ADMIN_CHANGE = "group_admin_change"
  # 群精华消息变更
  GROUP_ESSENCE_MESSAGE_CHANGE = "group_essence_message_change"
  # 群成员增加
  GROUP_MEMBER_INCREASE = "group_member_increase"
  # 群成员减少
  GROUP_MEMBER_DECREASE = "group_member_decrease"
  # 群名称变更
  GROUP_NAME_CHANGE = "group_name_change"
  # 群消息表情撤回
  GROUP_MESSAGE_REACTION = "group_message_reaction"
  # 群禁言
  GROUP_MUTE = "group_mute"
  # 群全体禁言
  GROUP_WHOLE_MUTE = "group_whole_mute"
  # 群戳一戳
  GROUP_NUDGE = "group_nudge"
  # 群文件上传
  GROUP_FILE_UPLOAD = "group_file_upload"
  # UNKNOWN
  UNKNOWN = "unknown"

  @classmethod
  def from_event(cls, event_type: str) -> Optional["EventType"]:
    """从事件数据中解析消息类型

    Args:
        event_type: Milky 协议的原始事件类型

    Returns:
        对应的消息类型枚举，如果无法识别则返回 None
    """
    for mt in EventType:
      if mt.value == event_type:
        return mt
    return None


class ProtocolType(str, Enum):
  ONEBOT = "onebot"
  MILKY = "milky"

  @classmethod
  def from_event(cls, protocol_type: str) -> Optional["ProtocolType"]:
    """从字符串中解析协议类型

    Args:
        protocol_type: 协议类型

    Returns:
        对应的协议类型枚举，如果无法识别则返回 None
    """
    for pt in ProtocolType:
      if pt.value == protocol_type:
        return pt
    return None


class MessageType(str, Enum):
  """消息类型枚举"""

  TEXT = "text"
  MENTION = "mention"
  MENTION_ALL = "mention_all"
  FACE = "face"
  REPLY = "reply"
  IMAGE = "image"
  RECORD = "record"
  VIDEO = "video"
  FILE = "file"
  UNKNOWN = "unknown"


@dataclass
class OutgoingSegment:
  """发送消息的抽象类"""
  type: Optional[MessageType] = None
  data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EventContext:
  """标准化的事件上下文数据类

  用于在过滤器链和处理器之间传递事件数据
  屏蔽底层协议差异，提供统一的数据结构
  """

  # 原始事件数据
  raw_event: Dict[str, Any] = field(default_factory=dict)

  # 协议信息
  protocol: Optional[ProtocolType] = None  # 协议类型（milky/onebot等）
  event_type: Optional[EventType] = None  # 事件类型

  # 时间戳
  time: Optional[int] = None

  # 机器人信息
  self_id: Optional[str] = None  # 机器人 ID

  # 与EventType有关
  data: Dict[str, Any] = field(default_factory=dict)

  def to_dict(self) -> Dict[str, Any]:
    """转换为字典格式。

    Returns:
        字典格式的上下文数据。
    """
    return {
      "raw_event": self.raw_event,
      "protocol": self.protocol.value if self.protocol else None,
      "event_type": self.event_type.value if self.event_type else None,
      "time": self.time,
      "self_id": self.self_id,
      "data": self.data,
    }

  @classmethod
  def from_dict(cls, data: Dict[str, Any]) -> "EventContext":
    """从字典创建 EventContext 实例

    Args:
        data: 字典格式的上下文数据

    Returns:
        EventContext 实例
    """
    protocol_str = data.get("protocol")
    event_type_str = data.get("event_type")

    return cls(
      raw_event=data.get("raw_event", {}),
      protocol=ProtocolType.from_event(protocol_str) if protocol_str else None,
      event_type=EventType.from_event(event_type_str) if event_type_str else None,
      time=data.get("time"),
      self_id=data.get("self_id"),
      data=data.get("data", {}),
    )


class BaseAdapter(ABC):
  """适配器基类"""

  # ============系统api(https://milky.ntqqrev.org/api/system)============
  # 获取登录信息
  @abstractmethod
  def get_login_info(self) -> Dict[str, Any]:
    """获取登录信息

    Returns:
        登录信息
    """
    pass

  # 获取协议端信息
  @abstractmethod
  def get_protocol_info(self) -> Dict[str, Any]:
    """获取协议端信息

    Returns:
        协议端信息
    """
    pass

  # 获取用户个人信息
  @abstractmethod
  def get_user_info(self, user_id: str) -> Dict[str, Any]:
    """获取用户个人信息

    Args:
        user_id: 用户 ID

    Returns:
        用户个人信息
    """
    pass

  # 获取好友列表
  @abstractmethod
  def get_friend_list(self) -> List[Dict[str, Any]]:
    """获取好友列表

    Returns:
        好友列表
    """
    pass

  # 获取好友信息
  @abstractmethod
  def get_friend_info(self, user_id: str) -> Dict[str, Any]:
    """获取好友信息

    Args:
        user_id: 用户 ID

    Returns:
        好友信息
    """
    pass

  # 获取群列表
  @abstractmethod
  def get_group_list(self) -> List[Dict[str, Any]]:
    """获取群列表

    Returns:
        群列表
    """
    pass

  # 获取群信息
  @abstractmethod
  def get_group_info(self, group_id: str) -> Dict[str, Any]:
    """获取群信息

    Args:
        group_id: 群 ID

    Returns:
        群信息
    """
    pass

  # 获取群成员列表
  @abstractmethod
  def get_group_member_list(self, group_id: str) -> List[Dict[str, Any]]:
    """获取群成员列表

    Args:
        group_id: 群 ID

    Returns:
        群成员列表
    """
    pass

  # 获取群成员信息
  @abstractmethod
  def get_group_member_info(self, group_id: str, user_id: str) -> Dict[str, Any]:
    """获取群成员信息

    Args:
        group_id: 群 ID
        user_id: 用户 ID

    Returns:
        群成员信息
    """
    pass

  # ============消息api(https://milky.ntqqrev.org/api/message)============
  # 发送私聊消息
  @abstractmethod
  def send_private_message(self, user_id: str, message: List[OutgoingSegment]) -> Dict[str, Any]:
    """发送私聊消息

    Args:
        user_id: 用户 ID
        message: 消息内容

    Returns:
        发送结果
    """
    pass

  # 发送群消息
  @abstractmethod
  def send_group_message(self, group_id: str, message: List[OutgoingSegment]) -> Dict[str, Any]:
    """发送群消息

    Args:
        group_id: 群 ID
        message: 消息内容

    Returns:
        发送结果
    """
    pass

  # 撤回私聊消息
  @abstractmethod
  def recall_private_message(self, user_id: str, message_id: str) -> Dict[str, Any]:
    """撤回私聊消息

    Args:
        user_id: 用户 ID
        message_id: 消息 ID

    Returns:
        撤回结果
    """
    pass

  # 撤回群消息
  @abstractmethod
  def recall_group_message(self, group_id: str, message_id: str) -> Dict[str, Any]:
    """撤回群消息

    Args:
        group_id: 群 ID
        message_id: 消息 ID

    Returns:
        撤回结果
    """
    pass
    # 获取消息

  @abstractmethod
  def get_message(self, message_scene: str, peer_id, message_id: str) -> Dict[str, Any]:
    """获取消息

    Args:
        message_scene: 消息场景
        peer_id: 好友 QQ 号或群号
        message_id: 消息 ID

    Returns:
        消息内容
    """
    pass

  # 获取历史消息
  @abstractmethod
  def get_history_message(self, message_scene: str, peer_id, start_message_id: str, limit: int) -> List[Dict[str, Any]]:
    """获取历史消息

    Args:
        message_scene: 消息场景
        peer_id: 群号或好友 QQ 号
        start_message_id: 起始消息 ID
        limit: 最大返回数量

    Returns:
        消息列表
    """
    pass
  
