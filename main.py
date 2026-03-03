# 使用示例
import asyncio

from src.gateway.core.connection.websocket import ReverseWebSocketServer
from src.gateway.filters.base import BotContext
from src.gateway.filters.content import ContentFilter
from src.utils.config import config
from src.utils.logger import logger


async def main():
  """主函数，启动 WebSocket 服务端。"""
  # 从配置文件读取 WebSocket 配置
  ws_config = config.get("ws", {})
  host = ws_config.get("host", "0.0.0.0")
  port = ws_config.get("port", 8080)
  heartbeat_interval = ws_config.get("heartbeat_interval", 30)
  heartbeat_timeout = ws_config.get("heartbeat_timeout", 10)

  # 创建过滤器列表
  filters = [
    ContentFilter(order=10),
  ]

  # 创建 WebSocket 服务端
  server = ReverseWebSocketServer(
    host=host,
    port=port,
    heartbeat_interval=heartbeat_interval,
    heartbeat_timeout=heartbeat_timeout,
    filters=filters,
  )

  # 设置回调
  async def on_message(context: BotContext):
    logger.info(f"[回调] 处理消息: {context.event.post_type}")

  async def on_connect():
    logger.success("[回调] 客户端已连接")

  async def on_disconnect():
    logger.warning("[回调] 客户端已断开")

  server.on_message = on_message
  server.on_connect = on_connect
  server.on_disconnect = on_disconnect

  # 启动服务端
  try:
    await server.start()
  except KeyboardInterrupt:
    logger.info("收到中断信号，正在关闭...")
    await server.stop()


if __name__ == "__main__":
  asyncio.run(main())
