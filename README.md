# WeRead Tool

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

现代化的微信读书工具，支持智能书架管理、笔记导出和书籍搜索等功能。

## ✨ 功能特性

- 🔐 **安全登录** - 支持微信读书Cookie登录
- 📚 **智能书架** - 渐进式加载，现代化界面设计
- 📱 **响应式设计** - 完美适配各种设备和屏幕尺寸
- 🖼️ **视觉化评分** - 精美图片展示书籍评分
- 📝 **笔记导出** - 支持Markdown格式的读书笔记导出
- 🔍 **书籍搜索** - 快速搜索和发现书籍
- 📖 **书籍详情** - 完整的书籍信息展示

## 🛠️ 技术栈

### 后端
- **FastAPI** - 高性能异步Web框架
- **SQLAlchemy** - 数据库ORM
- **Pydantic** - 数据验证
- **JWT** - 用户认证

### 前端
- **React 18** - 用户界面框架
- **TypeScript** - 类型安全
- **Vite** - 快速构建工具
- **Tailwind CSS** - 实用优先的CSS框架
- **React Query** - 数据获取和缓存

### 部署
- **Docker** - 容器化部署
- **Nginx** - 反向代理服务器

## 🚀 快速开始

### 开发环境

1. **克隆项目**
```bash
git clone <repository-url>
cd WereadTool
```

2. **后端启动**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

3. **前端启动**
```bash
cd frontend
npm install
npm run dev
```

### Docker 部署

```bash
docker-compose up -d
```

访问: http://localhost:3000

## 📝 使用方法

### 登录
1. 访问应用首页
2. 点击"扫码登录"按钮
3. 使用微信扫描二维码登录
4. 系统自动跳转到书架页面

### 浏览书架
- **智能加载** - 系统自动分批加载书籍数据
- **响应式显示** - 根据屏幕大小自动调整每页书籍数量
- **现代化界面** - 享受毛玻璃效果和流畅动画

### 搜索书籍
- 支持书名、作者等关键词搜索
- 实时搜索建议和结果高亮

## 📁 项目结构

```
WereadTool/
├── backend/             # 后端服务 (FastAPI)
├── frontend/            # 前端应用 (React + TypeScript)
├── docker-compose.yml   # Docker部署配置
├── nginx.conf          # Nginx配置
└── README.md           # 项目文档
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License