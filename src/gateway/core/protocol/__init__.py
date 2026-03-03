"""协议层模块，处理 Onebot 机器人协议。"""

from .schemas import (
    EventType,
    MessageType,
    BaseEvent,
    HeartbeatEvent,
    LifeCycleEvent,
    MessageEvent,
    MessageSegment,
    Sender,
)

__all__ = [
    "EventType",
    "MessageType",
    "BaseEvent",
    "HeartbeatEvent",
    "LifeCycleEvent",
    "MessageEvent",
    "MessageSegment",
    "Sender",
]
