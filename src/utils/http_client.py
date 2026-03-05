import httpx
from typing import Optional, Dict, Any
from loguru import logger


class HttpClient:
    """
    基于 HTTPX 的无状态 HTTP 客户端管理器。
    支持同步/异步请求，可配置超时和重试。
    """
    _instance: Optional['HttpClient'] = None
    _client: Optional[httpx.Client] = None
    _async_client: Optional[httpx.AsyncClient] = None

    def __new__(cls) -> 'HttpClient':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # 默认配置
        self.config = {
            "timeout": 30.0,
            "follow_redirects": True,
            "verify": True,
            "headers": {}
        }

    def setup(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        使用配置初始化 HTTP 客户端。
        应在应用程序启动时调用。
        """
        if config:
            self.config.update(config)

        # 初始化同步客户端
        self._client = httpx.Client(
            timeout=self.config["timeout"],
            follow_redirects=self.config["follow_redirects"],
            verify=self.config["verify"],
            headers=self.config["headers"]
        )

        # 初始化异步客户端
        self._async_client = httpx.AsyncClient(
            timeout=self.config["timeout"],
            follow_redirects=self.config["follow_redirects"],
            verify=self.config["verify"],
            headers=self.config["headers"]
        )

        logger.info(f"HTTP 客户端已初始化。超时时间：{self.config['timeout']}s")

    def _ensure_client(self) -> httpx.Client:
        """确保同步客户端已初始化"""
        if self._client is None:
            self.setup()
        return self._client

    def _ensure_async_client(self) -> httpx.AsyncClient:
        """确保异步客户端已初始化"""
        if self._async_client is None:
            self.setup()
        return self._async_client

    def get(self, url: str, **kwargs) -> httpx.Response:
        """同步 GET 请求"""
        return self._ensure_client().get(url, **kwargs)

    def post(self, url: str, **kwargs) -> httpx.Response:
        """同步 POST 请求"""
        return self._ensure_client().post(url, **kwargs)

    def put(self, url: str, **kwargs) -> httpx.Response:
        """同步 PUT 请求"""
        return self._ensure_client().put(url, **kwargs)

    def delete(self, url: str, **kwargs) -> httpx.Response:
        """同步 DELETE 请求"""
        return self._ensure_client().delete(url, **kwargs)

    def patch(self, url: str, **kwargs) -> httpx.Response:
        """同步 PATCH 请求"""
        return self._ensure_client().patch(url, **kwargs)

    async def async_get(self, url: str, **kwargs) -> httpx.Response:
        """异步 GET 请求"""
        return await self._ensure_async_client().get(url, **kwargs)

    async def async_post(self, url: str, **kwargs) -> httpx.Response:
        """异步 POST 请求"""
        return await self._ensure_async_client().post(url, **kwargs)

    async def async_put(self, url: str, **kwargs) -> httpx.Response:
        """异步 PUT 请求"""
        return await self._ensure_async_client().put(url, **kwargs)

    async def async_delete(self, url: str, **kwargs) -> httpx.Response:
        """异步 DELETE 请求"""
        return await self._ensure_async_client().delete(url, **kwargs)

    async def async_patch(self, url: str, **kwargs) -> httpx.Response:
        """异步 PATCH 请求"""
        return await self._ensure_async_client().patch(url, **kwargs)

    def close(self) -> None:
        """关闭同步客户端"""
        if self._client:
            self._client.close()
            self._client = None

    async def async_close(self) -> None:
        """关闭异步客户端"""
        if self._async_client:
            await self._async_client.aclose()
            self._async_client = None


# --------------------------
# 导出全局单例
# --------------------------
http = HttpClient()
