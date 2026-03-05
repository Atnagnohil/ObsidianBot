from typing import List

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage

from src.engine.provider.llm.scheams import LLMMessage


def convert_to_langchain_messages(messages: List[LLMMessage | dict]) -> List[BaseMessage]:
  """
  将自定义 LLMMessage 或字典格式转换为 LangChain 消息格式。

  支持 system、user 和 assistant 角色。
  """
  langchain_messages = []

  for msg in messages:
    if isinstance(msg, dict):
      role = msg.get("role")
      content = msg.get("content")
    else:
      role = msg.role
      content = msg.content

    if role == "system":
      langchain_messages.append(SystemMessage(content=content))
    elif role == "user":
      langchain_messages.append(HumanMessage(content=content))
    elif role == "assistant":
      langchain_messages.append(AIMessage(content=content))

  return langchain_messages
