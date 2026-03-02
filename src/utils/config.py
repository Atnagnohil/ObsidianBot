from pathlib import Path
from typing import Optional, Dict, Any

import yaml
from loguru import logger


class ConfigManager:
    """
    应用程序的全局配置管理器。

    从 config.yaml 文件加载和管理配置。
    """

    _instance: Optional['ConfigManager'] = None
    _config: Dict[str, Any] = {}
    _initialized: bool = False

    def __new__(cls) -> 'ConfigManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self, config_path: str = "config.yaml") -> None:
        """
        从 YAML 文件加载配置。

        应在应用程序启动时调用。
        """
        path = Path(config_path)

        if not path.exists():
            logger.warning(f"Config file not found: {config_path}, using empty config")
            self._config = {}
            self._initialized = True
            return

        with open(path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f) or {}

        self._initialized = True
        logger.info(f"Configuration loaded from {config_path}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        通过键获取配置值。

        支持使用点号表示法的嵌套键（例如 'llm.providers.openai'）。
        """
        if not self._initialized:
            self.load()

        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

            if value is None:
                return default

        return value

    def get_provider_config(self, provider_type: str) -> Dict[str, Any]:
        """获取特定 LLM 提供商的配置。"""
        return self.get(f'llm.providers.{provider_type}', {})

    def get_all(self) -> Dict[str, Any]:
        """获取完整的配置字典。"""
        if not self._initialized:
            self.load()
        return self._config.copy()


config = ConfigManager()
