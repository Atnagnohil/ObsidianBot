from abc import ABC, abstractmethod
from typing import List

from langchain_core.language_models import BaseChatModel

from src.engine.provider.llm.scheams import LLMChatRequest, LLMChatResponse


class BaseLLMProvider(ABC):
  @abstractmethod
  async def list_models(self) -> List[str]:
    """
    列出可用的模型。

    :return: 可用模型列表。
    """
    pass

  async def supports_model(self, model: str) -> bool:
    """
    检查 LLM 提供商是否支持指定模型。

    :return: 如果支持返回 True，否则返回 False。
    """
    supported_models = await self.list_models()
    if model in supported_models:
      return True
    return False

  @abstractmethod
  async def _get_model(self, model: str) -> BaseChatModel:
    """
    根据模型名称获取模型实例。

    :param model: 模型名称。
    :return: BaseChatModel 实例。
    """
    pass

  @abstractmethod
  async def chat(self, request: LLMChatRequest, **kwargs) -> LLMChatResponse:
    """
    与 LLM 进行对话。

    :param request: 对话请求。
    :param kwargs: 额外参数。
    :return: 对话响应。
    """
    pass
