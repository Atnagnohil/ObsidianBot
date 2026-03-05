from typing import List, AsyncGenerator, Any

from cachetools import LRUCache
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from src.engine.provider.llm.base import BaseLLMProvider
from src.engine.provider.llm.scheams import LLMChatRequest, LLMChatResponse
from src.utils.http_client import http
from src.utils.message_converter import convert_to_langchain_messages
from src.utils.response_builder import build_llm_response
from src.utils.config import config


class OpenAIProvider(BaseLLMProvider):
  """
  OpenAI 兼容的 LLM 提供商，使用 LangChain。

  支持流式和非流式对话补全。
  模型实例会被缓存以提高性能。
  配置从 config.yaml 的 llm.providers.openai 中加载。
  """

  MODELS_URI = "/models"

  def __init__(self, provider_name: str = "openai"):
    """
    使用 config.yaml 中的配置初始化提供商。

    Args:
        provider_name: config.yaml 中的提供商名称（默认："openai"）
    """
    self.model_instances = LRUCache(maxsize=50)
    self._config = config.get_provider_config(provider_name)

    if not self._config:
      raise ValueError(f"配置中未找到提供商 '{provider_name}'")

    self._base_url = self._config.get("base_url")
    self._api_key = self._config.get("api_key")

    if not self._base_url or not self._api_key:
      raise ValueError(f"提供商 '{provider_name}' 缺少 base_url 或 api_key")

  async def list_models(self) -> List[str]:
    """从 API 端点获取可用模型列表。"""
    response = await http.async_get(
      self._base_url + self.MODELS_URI,
      headers={"Authorization": f"Bearer {self._api_key}"}
    )
    return [model["id"] for model in response.json()["data"]]

  async def _get_model(self, request: LLMChatRequest) -> BaseChatModel:
    """
    获取或创建缓存的 ChatOpenAI 模型实例。

    如果模型不支持则抛出 ValueError。
    """
    if not await self.supports_model(request.model):
      raise ValueError(f"不支持模型 {request.model}")

    if request.model in self.model_instances:
      return self.model_instances[request.model]

    chat_model = ChatOpenAI(
      model=request.model,
      base_url=self._base_url,
      api_key=self._api_key,
      streaming=True,
      temperature=request.temperature,
      max_tokens=request.max_tokens,
      stop_sequences=request.stop,
      top_p=request.top_p,
      frequency_penalty=request.frequency_penalty,
      presence_penalty=request.presence_penalty
    )
    self.model_instances[request.model] = chat_model
    return chat_model

  async def chat(self, request: LLMChatRequest, **kwargs) -> AsyncGenerator[LLMChatResponse, Any]:
    """
    执行流式或非流式对话补全。

    始终返回异步生成器以保持接口一致性。
    """
    model = await self._get_model(request)
    messages = convert_to_langchain_messages(request.message)

    if request.stream:
      index = 0
      async for chunk in model.astream(input=messages):
        yield build_llm_response(chunk, request, index)
        index += 1
    else:
      response = await model.ainvoke(input=messages)
      yield build_llm_response(response, request, 0)
