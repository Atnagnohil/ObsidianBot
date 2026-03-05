# Gateway 架构说明

## 概述

Gateway 模块负责接收、过滤、分派和处理来自 QQ 机器人的消息。

## 架构流程

```
WebSocket 接收消息
    ↓
解析为事件对象 (MessageEvent, HeartbeatEvent 等)
    ↓
创建 BotContext
    ↓
FilterChain 过滤器链
    ├─ ContentFilter (过滤非文本消息)
    ├─ 其他过滤器...
    └─ 任何过滤器返回 DROP → 丢弃消息
    ↓
MessageDispatcher 消息分派器
    ├─ 按优先级遍历 Handler
    ├─ 调用 can_handle() 判断
    └─ 找到第一个可处理的 Handler
    ↓
Handler 处理器执行
    ├─ HelpHandler (帮助命令)
    ├─ EchoHandler (回声消息)
    └─ 其他处理器...
    ↓
返回 HandlerResponse
```

## 模块说明

### 1. Connection (连接层)

- `websocket.py`: 反向 WebSocket 服务端
  - 接收来自 QQ 机器人的连接
  - 解析 JSON 消息为事件对象
  - 心跳检测和连接管理

### 2. Protocol (协议层)

- `schemas.py`: 事件数据模型
  - `EventType`: 事件类型枚举
  - `MessageEvent`: 消息事件
  - `HeartbeatEvent`: 心跳事件
  - `MessageSegment`: 消息段
  - `MessageType`: 消息类型枚举

### 3. Filters (过滤器层)

- `base.py`: 过滤器基类
  - `Filter`: 过滤器抽象类
  - `FilterChain`: 过滤器链
  - `BotContext`: 上下文对象
  - `FilterResult`: 过滤结果 (PASS/DROP)

- `content.py`: 内容过滤器
  - 过滤非消息事件
  - 过滤非文本消息

### 4. Dispatcher (分派器层)

- `dispatcher.py`: 消息分派器
  - 管理处理器列表
  - 按优先级分派消息
  - 找到第一个可处理的 Handler

### 5. Handlers (处理器层)

- `base.py`: 处理器基类
  - `BaseHandler`: 处理器抽象类
  - `HandlerResponse`: 处理响应
  - `HandlerResult`: 处理结果 (SUCCESS/FAILED/SKIPPED)

- `help_handler.py`: 帮助命令处理器
  - 响应 "help"、"帮助" 命令
  - 优先级: 10

- `echo_handler.py`: 回声处理器
  - 响应 "echo <内容>" 命令
  - 优先级: 50

## 如何添加新的过滤器

```python
from src.gateway.filters.base import Filter, BotContext, FilterResult, FilterChain

class MyFilter(Filter):
    def __init__(self, order: int = 100):
        super().__init__(order)

    async def do_filter(self, context: BotContext, chain: FilterChain) -> FilterResult:
        # 判断逻辑
        if should_drop:
            context.drop("原因")
            return FilterResult.DROP
        return FilterResult.PASS
```

在 `main.py` 中注册：

```python
filters = [
    ContentFilter(order=10),
    MyFilter(order=20),  # 添加新过滤器
]
```

## 如何添加新的处理器

```python
from src.gateway.handlers.base import BaseHandler, HandlerResponse, HandlerResult
from src.gateway.filters.base import BotContext

class MyHandler(BaseHandler):
    def __init__(self, priority: int = 100):
        super().__init__(priority)

    async def can_handle(self, context: BotContext) -> bool:
        # 判断是否可以处理
        return True

    async def handle(self, context: BotContext) -> HandlerResponse:
        # 处理逻辑
        return HandlerResponse(
            result=HandlerResult.SUCCESS,
            message="处理成功"
        )
```

在 `main.py` 中注册：

```python
handlers = [
    HelpHandler(priority=10),
    EchoHandler(priority=50),
    MyHandler(priority=100),  # 添加新处理器
]
```

## 优先级说明

### 过滤器 (order)

- 数值越小，越先执行
- 建议范围: 1-100
- 示例:
  - 10: 基础过滤 (ContentFilter)
  - 20: 权限过滤
  - 30: 频率限制

### 处理器 (priority)

- 数值越小，优先级越高
- 建议范围: 1-100
- 示例:
  - 10: 系统命令 (HelpHandler)
  - 50: 功能命令 (EchoHandler)
  - 100: 默认处理器

## 配置文件

在 `config.yaml` 中配置 WebSocket 参数：

```yaml
ws:
  host: 0.0.0.0
  port: 8080
  heartbeat_interval: 30
  heartbeat_timeout: 10
```
