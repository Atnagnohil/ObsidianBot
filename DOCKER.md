# Docker 部署指南

## 🚀 快速开始

### 方式 1: 使用构建脚本（推荐）

```bash
# 赋予执行权限
chmod +x build.sh

# 构建 Alpine 版本（推荐）
./build.sh alpine

# 或构建 Distroless 版本（最小）
./build.sh distroless

# 启动服务
docker-compose up -d
```

### 方式 2: 使用 Docker Compose

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止
docker-compose down

# 重启
docker-compose restart
```

### 方式 3: 使用 Docker 命令

```bash
# 构建镜像（Alpine 版本）
DOCKER_BUILDKIT=1 docker build -t obsidianbot:alpine .

# 运行容器
docker run -d \
  --name obsidianbot \
  -p 8081:8081 \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -v $(pwd)/logs:/app/logs \
  --restart unless-stopped \
  --memory=512m \
  --cpus=1 \
  --read-only \
  --tmpfs /tmp:size=10M \
  --security-opt no-new-privileges:true \
  obsidianbot:alpine
```

## 📦 镜像版本选择

| 版本           | 大小   | 特点               | 推荐场景        |
| -------------- | ------ | ------------------ | --------------- |
| **Alpine**     | ~150MB | 功能完整，有 shell | ✅ 生产环境推荐 |
| **Distroless** | ~120MB | 最小化，无 shell   | 极致优化场景    |

## ⚙️ 配置说明

### 配置文件挂载

配置文件 `config.yaml` 通过 volume 挂载到容器中：

```bash
# 修改配置后重启
docker-compose restart
```

### 环境变量

支持通过环境变量覆盖配置：

```yaml
environment:
  - TZ=Asia/Shanghai
  - PYTHONUNBUFFERED=1
```

### 日志目录

日志保存在 `./logs` 目录，自动挂载到容器：

```bash
# 查看日志
tail -f logs/app_*.log
```

## 🔒 安全特性

本镜像实现了多层安全加固：

- ✅ 非 root 用户运行（UID 1000）
- ✅ 只读文件系统
- ✅ 禁止权限提升
- ✅ 最小化基础镜像
- ✅ 资源限制（CPU/内存）
- ✅ 健康检查

## 📊 资源限制

默认资源配置（已优化）：

```yaml
resources:
  limits:
    cpus: "1" # 最大 1 核
    memory: 512M # 最大 512MB
  reservations:
    cpus: "0.25" # 预留 0.25 核
    memory: 128M # 预留 128MB
```

## 🏥 健康检查

由于 WebSocket 服务的特殊性，简单的 TCP 连接检查会导致握手失败错误。建议通过以下方式监控服务状态：

### 方式 1: 查看容器状态

```bash
# 查看容器是否运行
docker ps | grep obsidianbot

# 查看容器日志
docker logs --tail 50 obsidianbot
```

### 方式 2: 监控进程

```bash
# 检查进程是否存在
docker exec obsidianbot ps aux | grep python
```

### 方式 3: 外部监控

使用外部监控工具（如 Prometheus + Grafana）监控 WebSocket 连接状态。

> **注意**: 已移除 Docker 内置健康检查，因为它会导致 WebSocket 握手失败的错误日志。

## 🐛 故障排查

### 查看容器日志

```bash
# 实时日志
docker-compose logs -f

# 最近 100 行
docker logs --tail 100 obsidianbot

# 带时间戳
docker logs -t obsidianbot
```

### 进入容器调试

```bash
# Alpine 版本（有 shell）
docker exec -it obsidianbot sh

# 查看进程
docker exec obsidianbot ps aux

# 查看网络连接
docker exec obsidianbot netstat -tlnp
```

### 检查配置

```bash
# 查看配置文件
docker exec obsidianbot cat /app/config.yaml

# 查看环境变量
docker exec obsidianbot env
```

### 重新构建

```bash
# 清理缓存重新构建
docker-compose build --no-cache
docker-compose up -d
```

## 📈 性能监控

### 实时监控

```bash
# 查看资源使用
docker stats obsidianbot

# 查看详细信息
docker inspect obsidianbot
```

### 日志分析

```bash
# 查看错误日志
grep ERROR logs/error_*.log

# 统计请求数
grep "处理消息" logs/app_*.log | wc -l
```

## 🔧 高级配置

### 使用 Distroless 镜像

```yaml
# docker-compose.yml
build:
  dockerfile: Dockerfile.distroless
```

### 自定义资源限制

```yaml
deploy:
  resources:
    limits:
      cpus: "2"
      memory: 1G
```

### 网络优化

```yaml
sysctls:
  - net.ipv4.tcp_keepalive_time=600
  - net.core.somaxconn=1024
```

## 🌐 生产环境部署

### 1. 使用 Secrets 管理敏感信息

```yaml
# docker-compose.yml
secrets:
  api_key:
    file: ./secrets/api_key.txt

services:
  obsidianbot:
    secrets:
      - api_key
```

### 2. 配置日志驱动

```yaml
logging:
  driver: "syslog"
  options:
    syslog-address: "tcp://192.168.0.42:514"
```

### 3. 使用私有镜像仓库

```bash
# 推送到私有仓库
docker tag obsidianbot:alpine registry.example.com/obsidianbot:alpine
docker push registry.example.com/obsidianbot:alpine
```

### 4. 配置自动更新

```bash
# 使用 Watchtower 自动更新
docker run -d \
  --name watchtower \
  -v /var/run/docker.sock:/var/run/docker.sock \
  containrrr/watchtower \
  obsidianbot
```

## 📚 更多文档

- [Docker 极致优化指南](DOCKER_OPTIMIZATION.md) - 详细的优化技术和性能对比
- [配置文件示例](config-example.yaml) - 完整的配置选项说明

## 💡 最佳实践

1. ✅ 使用 Alpine 镜像（生产环境）
2. ✅ 启用只读文件系统
3. ✅ 配置资源限制
4. ✅ 定期更新镜像
5. ✅ 使用健康检查
6. ✅ 配置日志轮转
7. ✅ 使用非 root 用户
8. ✅ 定期扫描漏洞

## 🆘 获取帮助

如遇问题，请检查：

1. 配置文件是否正确
2. 端口是否被占用
3. 资源是否充足
4. 日志中的错误信息

```bash
# 完整诊断命令
docker-compose ps
docker-compose logs --tail 50
docker stats obsidianbot
docker inspect obsidianbot
```
