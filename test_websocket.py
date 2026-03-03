"""测试反向 WebSocket 服务端。"""

import asyncio
from src.gateway.core.connection.websocket import ReverseWebSocketServer
from src.utils.logger import logger


async def main():
    """启动 WebSocket 服务端进行测试。"""
    # 使用 8081 端口避免冲突
    server = ReverseWebSocketServer(host="0.0.0.0", port=8081)
    
    # 设置回调函数
    async def on_message(data):
        logger.info(f"[回调] 收到消息类型: {data.get('post_type', 'unknown')}")
    
    async def on_connect():
        logger.success("[回调] 客户端已连接！")
    
    async def on_disconnect():
        logger.warning("[回调] 客户端已断开连接")
    
    server.on_message = on_message
    server.on_connect = on_connect
    server.on_disconnect = on_disconnect
    
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭...")
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
