# ============================================
# 阶段 1: 构建阶段 - 安装依赖
# ============================================
FROM python:3.14-alpine AS builder

# 安装构建依赖
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    cargo \
    rust

# 设置工作目录
WORKDIR /build

# 安装 uv（极速包管理器）
RUN pip install --no-cache-dir uv

# 复制依赖文件
COPY pyproject.toml uv.lock ./

# 创建虚拟环境并安装依赖
RUN uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv pip install --no-cache -r pyproject.toml

# ============================================
# 阶段 2: 运行阶段 - 最小化镜像
# ============================================
FROM python:3.14-alpine

# 只安装运行时必需的库
RUN apk add --no-cache \
    libffi \
    openssl \
    ca-certificates && \
    rm -rf /var/cache/apk/*

# 创建非 root 用户
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser

# 设置工作目录
WORKDIR /app

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv

# 复制应用代码（只复制必要文件）
COPY --chown=appuser:appuser main.py ./
COPY --chown=appuser:appuser src ./src
COPY --chown=appuser:appuser config-example.yaml ./

# 创建日志目录
RUN mkdir -p logs && chown -R appuser:appuser logs

# 设置环境变量
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONOPTIMIZE=2

# 切换到非 root 用户
USER appuser

# 暴露端口
EXPOSE 8081

# 启动应用
CMD ["python", "-O", "main.py"]
