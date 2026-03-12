# ObsidianBot

<div align="center">

![Python](https://img.shields.io/badge/Python-3.14+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![OneBot](https://img.shields.io/badge/OneBot-v11-orange.svg)
![WebSocket](https://img.shields.io/badge/WebSocket-Supported-brightgreen.svg)

*A sophisticated, enterprise-grade QQ bot framework built with modern Python architecture*

[Features](#features) • [Quick Start](#quick-start) • [Architecture](#architecture) • [Documentation](#documentation) • [Contributing](#contributing)

</div>

---

## Overview

ObsidianBot is a production-ready, scalable QQ bot framework engineered with enterprise-grade architecture principles. Built on modern Python async/await patterns and leveraging the OneBot v11 protocol, it provides a robust foundation for developing intelligent conversational agents with advanced AI capabilities.

## Features

### 🚀 **Core Capabilities**
- **AI-Powered Conversations**: Deep integration with LangChain ecosystem supporting multiple LLM providers
- **OneBot v11 Compliance**: Full compatibility with standard OneBot protocol specifications
- **High-Performance WebSocket**: Production-grade reverse WebSocket server with advanced connection management

### 🏗️ **Architecture Excellence**
- **Modular Design**: Clean separation of concerns with pluggable components
- **Event-Driven Processing**: Sophisticated message filtering and routing pipeline
- **Extensible Handler System**: Priority-based message processing with customizable handlers
- **Content Intelligence**: Advanced content extraction and summarization capabilities

### 🛡️ **Enterprise Features**
- **Resilient Connectivity**: Intelligent heartbeat monitoring with exponential backoff retry strategies
- **Comprehensive Logging**: Structured logging with rotation, compression, and retention policies
- **Configuration Management**: YAML-based configuration with environment-specific overrides
- **Error Handling**: Graceful degradation and comprehensive exception management

## Quick Start

### Prerequisites

- **Python 3.14+** (Latest stable release recommended)
- **uv** - Modern Python package manager ([Installation Guide](https://docs.astral.sh/uv/getting-started/installation/))

### Installation

```bash
# Clone the repository
git clone https://github.com/Atnagnohil/ObsidianBot.git
cd ObsidianBot

# Initialize project dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate  # Unix/macOS
# or
.venv\Scripts\activate     # Windows
```

### Configuration

1. **Initialize configuration from template:**
   ```bash
   cp config-example.yaml config.yaml
   ```

2. **Configure core services:**
   ```yaml
   # WebSocket Server Configuration
   ws:
     host: 0.0.0.0
     port: 8081
     heartbeat_interval: 30
     heartbeat_timeout: 60

   # OneBot Protocol Configuration
   onebot:
     base_url: http://localhost:3000
     access_token: "${ONEBOT_ACCESS_TOKEN}"

   # LLM Provider Configuration
   llm:
     providers:
       openai:
         type: openai
         api_key: "${OPENAI_API_KEY}"
         base_url: "https://api.openai.com/v1"
   ```

### Deployment

```bash
# Development mode
python main.py

# Production deployment (with Docker)
docker-compose up -d

# Or using the build script
./build.sh
```

## Architecture

### System Design

ObsidianBot employs a layered architecture pattern with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
├─────────────────────────────────────────────────────────────┤
│  Gateway Layer    │  Engine Layer     │  Utils Layer       │
│  ┌─────────────┐  │  ┌─────────────┐  │  ┌─────────────┐   │
│  │ Handlers    │  │  │ Content     │  │  │ Config      │   │
│  │ Dispatcher  │  │  │ Providers   │  │  │ Logger      │   │
│  │ Filters     │  │  │ LLM         │  │  │ HTTP Client │   │
│  └─────────────┘  │  └─────────────┘  │  └─────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                    Protocol Layer                           │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐   │
│  │ WebSocket   │     │ OneBot      │     │ Events      │   │
│  │ Connection  │     │ Protocol    │     │ Schemas     │   │
│  └─────────────┘     └─────────────┘     └─────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Message Processing Pipeline

```
WebSocket Reception → Event Parsing → Filter Chain → Message Dispatch → Handler Execution
       ↓                   ↓              ↓              ↓                ↓
   Raw JSON         BaseEvent      BotContext    HandlerResponse    OneBot API
```

### Core Components

#### **Gateway Module**
- **Connection Management**: Robust WebSocket server with connection pooling
- **Event Processing**: Efficient event parsing and context creation  
- **Filter Chain**: Configurable message filtering pipeline
- **Handler System**: Priority-based message routing and processing

#### **Engine Module**
- **Content Processing**: Advanced text analysis and summarization
- **LLM Integration**: Multi-provider AI service abstraction
- **Provider Registry**: Dynamic LLM provider registration and management

#### **Protocol Layer**
- **OneBot Compliance**: Full OneBot v11 specification implementation
- **Event Schemas**: Strongly-typed event data models
- **Message Serialization**: Efficient JSON serialization/deserialization

## Documentation

### API Reference

#### Handler Development

```python
from src.gateway.handlers.base import BaseHandler, HandlerResponse, HandlerResult
from src.gateway.filters.base import BotContext

class CustomHandler(BaseHandler):
    """Custom message handler implementation."""
    
    def __init__(self, priority: int = 100):
        super().__init__(priority)
    
    async def can_handle(self, context: BotContext) -> bool:
        """Determine if this handler can process the message."""
        return context.event.raw_message.startswith("/custom")
    
    async def handle(self, context: BotContext) -> HandlerResponse:
        """Process the message and return response."""
        # Implementation logic here
        return HandlerResponse(
            result=HandlerResult.SUCCESS,
            message="Command processed successfully"
        )
```

#### Filter Development

```python
from src.gateway.filters.base import Filter, FilterResult, FilterChain

class SecurityFilter(Filter):
    """Security-focused message filter."""
    
    def __init__(self, order: int = 5):
        super().__init__(order)
    
    async def do_filter(self, context: BotContext, chain: FilterChain) -> FilterResult:
        """Apply security filtering logic."""
        if self._is_suspicious(context.event):
            context.drop("Security policy violation")
            return FilterResult.DROP
        
        return FilterResult.PASS
    
    def _is_suspicious(self, event) -> bool:
        # Security validation logic
        return False
```

### Configuration Reference

#### WebSocket Configuration
```yaml
ws:
  host: "0.0.0.0"              # Bind address
  port: 8081                   # Listen port
  heartbeat_interval: 30       # Heartbeat check interval (seconds)
  heartbeat_timeout: 60        # Connection timeout threshold (seconds)
```

#### OneBot Configuration
```yaml
onebot:
  base_url: "http://localhost:3000"  # OneBot HTTP API endpoint
  access_token: "${ACCESS_TOKEN}"    # Authentication token (optional)
  timeout: 30                        # Request timeout (seconds)
```

#### Logging Configuration
```yaml
logger:
  path: "logs"                 # Log directory
  level: "INFO"               # Log level (DEBUG, INFO, WARNING, ERROR)
  rotation: "100 MB"          # Log rotation size
  retention: "14 days"        # Log retention period
  compression: "zip"          # Compression format
  console: true               # Console output enabled
```

### Project Structure

```
ObsidianBot/
├── src/
│   ├── engine/                    # Core processing engine
│   │   ├── content/              # Content analysis modules
│   │   │   ├── base.py          # Abstract content processor
│   │   │   ├── local.py         # Local content handler
│   │   │   └── __init__.py
│   │   └── provider/            # LLM provider implementations
│   │       ├── llm/            # Language model providers
│   │       │   ├── base.py     # Provider base class
│   │       │   ├── openai_provider.py
│   │       │   ├── registry.py # Provider registry
│   │       │   └── schemas.py  # Provider schemas
│   │       └── __init__.py
│   ├── gateway/                  # Message gateway system
│   │   ├── core/                # Core gateway components
│   │   │   ├── connection/      # Connection management
│   │   │   └── protocol/        # Protocol implementations
│   │   ├── dispatcher/          # Message dispatching
│   │   ├── filters/             # Message filtering
│   │   ├── handlers/            # Message handlers
│   │   └── __init__.py
│   ├── utils/                   # Utility modules
│   │   ├── config.py           # Configuration management
│   │   ├── logger.py           # Logging utilities
│   │   ├── http_client.py      # HTTP client wrapper
│   │   └── __init__.py
│   └── __init__.py
├── logs/                        # Application logs
├── docker-compose.yml          # Docker composition
├── Dockerfile                  # Container definition
├── main.py                     # Application entry point
├── config-example.yaml         # Configuration template
├── pyproject.toml             # Project metadata
├── uv.lock                    # Dependency lock file
└── README.md                  # Project documentation
```

## Development Guidelines

### Code Standards

- **Python 3.14+**: Leverage latest language features and performance improvements
- **Type Safety**: Comprehensive type annotations using `typing` module
- **Async/Await**: Consistent use of async patterns for I/O operations
- **PEP 8 Compliance**: Strict adherence to Python style guidelines
- **Documentation**: Comprehensive docstrings following Google/NumPy style

### Testing Strategy

```bash
# Run unit tests
python -m pytest tests/unit/

# Run integration tests
python -m pytest tests/integration/

# Generate coverage report
python -m pytest --cov=src tests/
```

### Performance Considerations

- **Connection Pooling**: Efficient WebSocket connection management
- **Memory Management**: Proper cleanup of resources and event handlers
- **Async Processing**: Non-blocking I/O operations throughout the pipeline
- **Caching Strategy**: Intelligent caching of frequently accessed data

## Deployment

### Docker Deployment

```bash
# Build container image
docker build -t obsidianbot:latest .

# Run with Docker Compose
docker-compose up -d

# Scale horizontally
docker-compose up -d --scale bot=3
```

### Production Configuration

```yaml
# production.yaml
ws:
  host: "0.0.0.0"
  port: 8081

logger:
  level: "WARNING"
  console: false

onebot:
  base_url: "${ONEBOT_ENDPOINT}"
  access_token: "${ONEBOT_TOKEN}"
```

## Contributing

We welcome contributions from the community! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting pull requests.

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/your-username/ObsidianBot.git
cd ObsidianBot

# Install development dependencies
uv sync --dev

# Install pre-commit hooks
pre-commit install

# Run tests
python -m pytest
```

### Contribution Process

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [OneBot](https://onebot.dev/) - Standard bot protocol specification
- [LangChain](https://langchain.com/) - AI application development framework
- [WebSockets](https://websockets.readthedocs.io/) - WebSocket implementation for Python

---

<div align="center">

**[⬆ Back to Top](#obsidianbot)**

Made with ❤️ by the ObsidianBot Team

</div>
