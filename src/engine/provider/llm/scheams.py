import time
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class LLMChatRequest(BaseModel):
  message: list[LLMMessage] = Field(..., min_length=1, description="发送给 LLM 的消息")
  # 模型名称：provider/model
  model: str = Field(..., min_length=1, description="使用的模型")
  temperature: float = Field(0.7, description="温度参数")
  max_tokens: int = Field(1024, description="生成的最大 token 数")
  stream: bool = Field(True, description="是否流式返回响应")
  stop: Optional[list[str]] = Field(None, description="停止序列")
  top_p: float = Field(1.0, description="Top P 参数")
  frequency_penalty: float = Field(0.0, description="频率惩罚")
  presence_penalty: float = Field(0.0, description="存在惩罚")


class FinishReason(str, Enum):
  stop = "stop"
  eos = "eos"
  length = "length"
  tool_calls = "tool_calls"


class TokenUsage(BaseModel):
  completion_tokens: int = Field(0, description="补全 token 数")
  prompt_tokens: int = Field(0, description="提示 token 数")
  total_tokens: int = Field(0, description="总 token 数")


class ChatChoice(BaseModel):
  message: str = Field(..., description="消息内容")
  finish_reason: Optional[FinishReason] = Field(None, description="结束原因")
  index: int = Field(..., description="索引")


class LLMChatResponse(BaseModel):
  id: str = Field(..., description="对话 ID")
  timestamp: int = Field(..., description="对话时间戳")
  model: str = Field(..., description="使用的模型")
  choice: ChatChoice = Field(..., description="选择结果")
  usage: Optional[TokenUsage] = Field(None, description="使用情况")


class MessageRole(str, Enum):
  SYSTEM = "system"
  USER = "user"
  ASSISTANT = "assistant"
  TOOL = "tool"


class LLMMessage(BaseModel):
  id: str = Field(default_factory=lambda: str(uuid4()), description="消息 ID")
  role: MessageRole = Field(..., description="消息角色")
  content: str = Field(..., min_length=1, description="消息内容")
  tool_calls: Optional[list[dict]] = Field(None, description="工具调用")
  tool_call_id: Optional[str] = Field(None, description="工具调用 ID")
  timestamp: int = Field(default_factory=lambda: int(time.time()), description="消息时间戳")
