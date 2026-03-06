#!/bin/bash
# Docker 镜像构建脚本

set -e

echo "🚀 开始构建 ObsidianBot Docker 镜像..."

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 修复日志目录权限
echo -e "${BLUE}📁 准备日志目录...${NC}"
mkdir -p logs
if [ "$EUID" -ne 0 ] && command -v sudo &> /dev/null; then
    sudo chown -R 1000:1000 logs 2>/dev/null || true
    sudo chmod -R 755 logs 2>/dev/null || true
else
    chown -R 1000:1000 logs 2>/dev/null || true
    chmod -R 755 logs 2>/dev/null || true
fi

# 启用 BuildKit
export DOCKER_BUILDKIT=1

# 构建选项
BUILD_TYPE=${1:-alpine}  # alpine, distroless, slim

case $BUILD_TYPE in
  alpine)
    echo -e "${BLUE}📦 构建 Alpine 版本（推荐）${NC}"
    docker build \
      --file Dockerfile \
      --tag obsidianbot:alpine \
      --tag obsidianbot:latest \
      --build-arg BUILDKIT_INLINE_CACHE=1 \
      --progress=plain \
      .
    IMAGE_TAG="alpine"
    ;;

  distroless)
    echo -e "${BLUE}📦 构建 Distroless 版本（最小）${NC}"
    docker build \
      --file Dockerfile.distroless \
      --tag obsidianbot:distroless \
      --build-arg BUILDKIT_INLINE_CACHE=1 \
      --progress=plain \
      .
    IMAGE_TAG="distroless"
    ;;

  *)
    echo -e "${YELLOW}❌ 未知的构建类型: $BUILD_TYPE${NC}"
    echo "用法: $0 [alpine|distroless]"
    exit 1
    ;;
esac

echo -e "${GREEN}✅ 构建完成！${NC}"
echo ""
echo "📊 镜像信息:"
docker images obsidianbot:$IMAGE_TAG --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

echo ""
echo "🔍 镜像层级分析:"
docker history obsidianbot:$IMAGE_TAG --human --no-trunc | head -n 10

echo ""
echo -e "${GREEN}🎉 可以使用以下命令启动:${NC}"
echo "  docker-compose up -d"
echo ""
echo -e "${BLUE}💡 提示:${NC}"
echo "  - Alpine 版本: 体积小，功能完整，推荐生产使用"
echo "  - Distroless 版本: 体积最小，无 shell，适合极致优化场景"
