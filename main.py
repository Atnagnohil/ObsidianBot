# 使用示例
import asyncio

from src.gateway.core.connection.websocket import ReverseWebSocketServer
from src.gateway.core.protocol.onebot import bot_adapter
from src.gateway.dispatcher import MessageDispatcher
from src.gateway.filters.base import BotContext
from src.gateway.filters.content import ContentFilter
from src.gateway.handlers.echo_handler import EchoHandler
from src.gateway.handlers.help_handler import HelpHandler
from src.utils.config import config
from src.utils.logger import logger


async def main():
  """主函数，启动 WebSocket 服务端。"""
  # 加载配置
  # 检查 OneBot 服务连接
  logger.info("正在检查 OneBot 服务连接...")
  if await bot_adapter.check_health():
    logger.success("OneBot 服务连接正常")
  else:
    logger.error("OneBot 服务连接失败，消息发送功能可能无法使用")
    logger.warning("程序将继续运行，但建议检查 OneBot 配置")

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

  # 创建处理器列表
  handlers = [
    HelpHandler(priority=10),  # 帮助命令，优先级最高
    EchoHandler(priority=50),  # 回声处理器
  ]

  # 创建消息分派器
  dispatcher = MessageDispatcher(handlers=handlers)
  logger.info(f"已注册 {len(handlers)} 个处理器")

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
    logger.debug(f"[回调] 处理消息: {context.event.post_type}")

    # 分派消息到处理器
    response = await dispatcher.dispatch(context)
    logger.info(f"处理结果: {response.result.value} - {response.message}")

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
  finally:
    # 清理 HTTP 客户端
    from src.utils.http_client import http
    await http.async_close()
    logger.info("资源清理完成")


if __name__ == "__main__":
  asyncio.run(main())
