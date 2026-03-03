"""WebSocket 客户端测试工具。"""

import asyncio
import json
from websockets.asyncio.client import connect


async def test_client():
    """测试连接到 WebSocket 服务端。"""
    uri = "ws://localhost:8081"
    
    print(f"正在连接到 {uri}...")
    
    async with connect(uri) as websocket:
        print("✓ 已连接到服务端")
        
        # 发送测试消息
        test_messages = [
            {"post_type": "message", "message": "Hello, Server!"},
            {"post_type": "notice", "notice_type": "group_increase"},
            {"post_type": "request", "request_type": "friend"},
        ]
        
        for msg in test_messages:
            print(f"\n发送: {json.dumps(msg, ensure_ascii=False)}")
            await websocket.send(json.dumps(msg))
            await asyncio.sleep(1)
        
        print("\n✓ 测试完成，保持连接 10 秒...")
        await asyncio.sleep(10)


if __name__ == "__main__":
    try:
        asyncio.run(test_client())
    except KeyboardInterrupt:
        print("\n中断测试")
    except Exception as e:
        print(f"\n✗ 错误: {e}")
