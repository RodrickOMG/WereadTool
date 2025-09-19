# WeRead Tool 云服务器部署指南

## 系统要求

- Linux 服务器（Ubuntu 20.04+ / CentOS 7+ 推荐）
- Docker 和 Docker Compose
- Nginx（已安装）
- 至少 1GB RAM
- 至少 2GB 磁盘空间

## 快速部署

### 1. 准备服务器环境

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Docker（如果未安装）
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 安装 Docker Compose（如果未安装）
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 重新登录以应用 docker 组权限
```

### 2. 部署应用

```bash
# 1. 上传项目文件到服务器
# 可以使用 git clone, scp, 或其他方式

# 2. 进入项目目录
cd /path/to/WereadTool

# 3. 使用简化版 docker-compose
cd deploy
cp docker-compose.simple.yml docker-compose.yml

# 4. 修改环境变量（可选）
# 编辑 docker-compose.yml 中的 SECRET_KEY

# 5. 启动服务
docker-compose up -d

# 6. 查看日志确认启动成功
docker-compose logs -f
```

### 3. 配置 Nginx

```bash
# 1. 创建 nginx 配置文件
sudo nano /etc/nginx/sites-available/weread-tool

# 2. 复制 nginx-config-example.conf 内容到文件中
# 并修改 server_name 为您的域名

# 3. 启用配置
sudo ln -s /etc/nginx/sites-available/weread-tool /etc/nginx/sites-enabled/

# 4. 测试配置
sudo nginx -t

# 5. 重载 nginx
sudo systemctl reload nginx
```

### 4. 验证部署

访问您的域名，应该能看到 WeRead Tool 登录页面。

- 前端：`http://your-domain.com`
- API 文档：`http://your-domain.com/docs`
- 健康检查：`http://your-domain.com/api/health`

## 替代部署方案

### 方案一：不使用容器（直接部署）

```bash
# 1. 安装 Python 3.11+
sudo apt install python3.11 python3.11-venv python3.11-dev

# 2. 部署后端
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 创建 systemd 服务
sudo nano /etc/systemd/system/weread-backend.service
```

systemd 服务配置：
```ini
[Unit]
Description=WeRead Tool Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/WereadTool/backend
Environment=PATH=/path/to/WereadTool/backend/venv/bin
ExecStart=/path/to/WereadTool/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
# 启动后端服务
sudo systemctl enable weread-backend
sudo systemctl start weread-backend

# 3. 部署前端
cd ../frontend
npm install
npm run build

# 将 dist 目录复制到 nginx 目录
sudo cp -r dist/* /var/www/weread-tool/
```

### 方案二：直接构建部署

```bash
# 1. 构建后端镜像
cd backend
docker build -f Dockerfile.simple -t weread-backend .

# 2. 构建前端镜像
cd ../frontend
docker build -t weread-frontend .

# 3. 运行容器
docker run -d --name weread-backend -p 8000:8000 weread-backend
docker run -d --name weread-frontend -p 3000:80 weread-frontend
```

## 数据持久化

应用使用 SQLite 数据库存储：
- 用户登录信息
- 书籍缓存数据

数据文件位置：
- Docker 部署：存储在 Docker volume `weread_data`
- 直接部署：`backend/weread.db`

### 备份数据

```bash
# Docker 部署备份
docker cp weread-backend:/app/weread.db ./backup/weread-$(date +%Y%m%d).db

# 直接部署备份
cp backend/weread.db backup/weread-$(date +%Y%m%d).db
```

## 环境变量配置

在 `docker-compose.yml` 或系统环境中设置：

```yaml
environment:
  - SECRET_KEY=your-very-secure-secret-key-here
  - DATABASE_URL=sqlite:///./weread.db
  - CORS_ORIGINS=http://your-domain.com,https://your-domain.com
```

## 常见问题

### 1. 容器启动失败
```bash
# 查看日志
docker-compose logs backend
docker-compose logs frontend

# 检查端口占用
sudo netstat -tlnp | grep :8000
sudo netstat -tlnp | grep :3000
```

### 2. Nginx 配置错误
```bash
# 测试配置
sudo nginx -t

# 查看错误日志
sudo tail -f /var/log/nginx/error.log
```

### 3. 无法访问 API
```bash
# 检查防火墙
sudo ufw status
sudo ufw allow 8000
sudo ufw allow 3000

# 检查容器网络
docker network ls
docker-compose ps
```

### 4. 微信读书登录失败
- 确保 cookies 信息正确
- 检查网络连接
- 确认微信读书账号状态

## 监控和维护

### 查看服务状态
```bash
# Docker 方式
docker-compose ps
docker-compose logs -f

# 系统服务方式
sudo systemctl status weread-backend
sudo journalctl -u weread-backend -f
```

### 更新应用
```bash
# 1. 停止服务
docker-compose down

# 2. 更新代码
git pull origin main

# 3. 重新构建并启动
docker-compose up -d --build
```

### 性能优化
- 启用 Nginx gzip 压缩
- 配置静态文件缓存
- 定期清理日志文件
- 监控磁盘空间使用

## SSL/HTTPS 配置

使用 Let's Encrypt 免费 SSL 证书：

```bash
# 安装 certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo crontab -e
# 添加：0 12 * * * /usr/bin/certbot renew --quiet
```