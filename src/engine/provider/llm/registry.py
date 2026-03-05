from typing import Dict, Type, Optional

from src.engine.provider.llm.base import BaseLLMProvider


class LLMProviderRegistry:
  """
  LLM 提供商注册表。

  将提供商类型映射到其实现类。
  相同类型的多个提供商共享同一个类。
  """

  _instance: Optional['LLMProviderRegistry'] = None
  _providers: Dict[str, Type[BaseLLMProvider]] = {}

  def __new__(cls) -> 'LLMProviderRegistry':
    if cls._instance is None:
      cls._instance = super().__new__(cls)
    return cls._instance

  def register(self, provider_type: str, provider_class: Type[BaseLLMProvider]) -> None:
    """
    为特定类型注册提供商类。

    配置中相同类型的多个条目将使用同一个类。
    """
    self._providers[provider_type] = provider_class

  def get(self, provider_type: str) -> Type[BaseLLMProvider]:
    """
    根据类型获取提供商类。

    如果未找到 provider_type 则抛出 KeyError。
    """
    if provider_type not in self._providers:
      raise KeyError(f"注册表中未找到提供商类型 '{provider_type}'")

    return self._providers[provider_type]

  def create(self, provider_name: str) -> BaseLLMProvider:
    """
    从配置创建提供商实例。

    从 config.yaml 读取提供商配置，获取类型，
    并实例化相应的提供商类。

    Args:
        provider_name: config.yaml 中的提供商名称（例如："openai"、"my-custom-openai"）

    Returns:
        实例化的提供商对象
    """
    from src.utils import config

    provider_config = config.get_provider_config(provider_name)
    if not provider_config:
      raise ValueError(f"配置中未找到提供商 '{provider_name}'")

    provider_type = provider_config.get("type")
    if not provider_type:
      raise ValueError(f"提供商 '{provider_name}' 配置中缺少 'type' 字段")

    provider_class = self.get(provider_type)
    return provider_class(provider_name=provider_name)

  def list_types(self) -> list[str]:
    """列出所有已注册的提供商类型。"""
    return list(self._providers.keys())

  def is_registered(self, provider_type: str) -> bool:
    """检查提供商类型是否已注册。"""
    return provider_type in self._providers


registry = LLMProviderRegistry()
