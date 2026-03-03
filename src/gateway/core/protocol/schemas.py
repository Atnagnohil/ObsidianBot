from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, List


class EventType(str, Enum):
  """事件类型枚举"""
  MESSAGE = "message"  # 消息事件
  MESSAGE_SENT = "message_sent"  # 消息发送事件
  NOTICE = "notice"  # 通知事件
  REQUEST = "request"  # 请求事件
  META_EVENT = "meta_event"  # 元事件


@dataclass
class BaseEvent:
  """事件基类"""
  time: int  # 时间戳
  self_id: int  # 机器人 QQ 号
  post_type: EventType  # 事件类型


@dataclass
class HeartbeatEvent(BaseEvent):
  """心跳事件"""
  status: Dict[str, Any]  # 状态信息
  interval: int  # 心跳间隔（ms）


@dataclass
class LifeCycleEvent(BaseEvent):
  """生命周期事件"""
  meta_event_type: str  # 生命周期事件类型
  sub_type: str  # 生命周期子类型


@dataclass
class Sender:
  """消息发送者"""
  user_id: int  # 发送者 QQ 号
  nickname: str  # 昵称
  card: str  # 群名片/昵称（群消息）
  sex: str  # 性别
  age: int  # 年龄
  level: str  # 群等级（群消息）
  role: str  # 群角色（群消息）
  title: str  # 专属群头衔（群消息）
  group_id: int  # 群号（来自群临时聊天）


class MessageType(str, Enum):
  """消息类型枚举"""
  TEXT = "text"  # 文本
  VIDEO = "video"  # 视频
  RECORD = "record"  # 音频
  FILE = "file"  # 文件
  AT = "at"  # At
  REPLY = "reply"  # 回复
  JSON = "json"  # JSON
  FACE = "face"  # 表情
  M_FACE = "m_face"  # 表情包
  MARKDOWN = "markdown"  # Markdown
  FORWARD = "forward"  # 转发
  DICE = "dice"  # 骰子
  RPS = "rps"  # 猜拳
  KEYBOARD = "keyboard"  # 键盘


@dataclass
class MessageSegment:
  """消息段"""
  type: MessageType
  data: Dict[str, Any]


@dataclass
class MessageEvent(BaseEvent):
  """消息事件"""
  message_id: int  # 消息 ID
  message_seq: int  # 消息序号
  real_id: int  # 消息真实 ID，只在 get_msg 接口存在
  user_id: int  # 发送者 QQ 号
  group_id: int  # 群号（仅在群消息）
  message_type: str  # 消息类型（private/group）
  sub_type: str  # 消息子类型（friend/group/normal）
  sender: Sender  # 发送者信息
  message: List[MessageSegment]  # 消息内容
  message_format: str  # 消息格式
  raw_message: str  # 原始消息内容（CQ 码格式）
  font: int  # 字体 ID
  target_id: int  # 接收者 ID（仅发送的消息）
  temp_source: int  # 临时会话来源（群临时会话 0=群聊）
