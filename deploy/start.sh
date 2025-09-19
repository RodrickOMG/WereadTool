#!/bin/bash

# WeRead Tool 启动脚本

set -e

echo "🚀 启动 WeRead Tool..."

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

# 检查 Docker Compose 是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 创建必要的目录
mkdir -p data/backups

# 设置权限
chmod +x deploy/*.sh

echo "📋 检查配置文件..."

# 检查配置文件是否存在
if [ ! -f "deploy/docker-compose.yml" ]; then
    echo "📝 复制默认配置文件..."
    cp deploy/docker-compose.simple.yml deploy/docker-compose.yml
fi

# 进入部署目录
cd deploy

echo "🔧 启动服务..."

# 停止可能存在的旧服务
docker-compose down 2>/dev/null || true

# 启动服务
docker-compose up -d

echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "📊 检查服务状态..."
docker-compose ps

# 等待后端服务启动
echo "🔍 等待后端服务就绪..."
timeout=60
count=0
while [ $count -lt $timeout ]; do
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        echo "✅ 后端服务已就绪"
        break
    fi
    sleep 1
    count=$((count + 1))
done

if [ $count -eq $timeout ]; then
    echo "❌ 后端服务启动超时"
    echo "📋 查看后端日志："
    docker-compose logs backend
    exit 1
fi

# 检查前端服务
echo "🔍 检查前端服务..."
if curl -f http://localhost:3000 >/dev/null 2>&1; then
    echo "✅ 前端服务已就绪"
else
    echo "⚠️  前端服务可能未完全启动，查看日志："
    docker-compose logs frontend
fi

echo ""
echo "🎉 WeRead Tool 启动完成！"
echo ""
echo "📊 服务信息："
echo "   - 前端地址：http://localhost:3000"
echo "   - 后端地址：http://localhost:8000"
echo "   - API 文档：http://localhost:8000/docs"
echo ""
echo "📋 常用命令："
echo "   - 查看日志：cd deploy && docker-compose logs -f"
echo "   - 停止服务：cd deploy && docker-compose down"
echo "   - 重启服务：cd deploy && docker-compose restart"
echo ""
echo "⚠️  请记得配置 Nginx 反向代理！"
echo "   配置示例：deploy/nginx-config-example.conf"