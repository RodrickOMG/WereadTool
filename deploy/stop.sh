#!/bin/bash

# WeRead Tool 停止脚本

set -e

echo "🛑 停止 WeRead Tool..."

# 进入部署目录
cd deploy

# 停止服务
echo "📋 停止 Docker 服务..."
docker-compose down

echo "🧹 清理资源..."
# 可选：清理未使用的镜像（谨慎使用）
# docker image prune -f

echo "✅ WeRead Tool 已停止"
echo ""
echo "📋 其他操作："
echo "   - 查看已停止的容器：docker ps -a"
echo "   - 重新启动：./start.sh"
echo "   - 完全清理：docker-compose down -v （会删除数据）"