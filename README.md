# Weread Tool - 微信读书工具箱

Weread Tool 是一个基于 Web 的微信读书工具箱

## ✨ 主要功能

- **全量书架同步**：通过解析 Web 端数据和调用同步接口，获取您微信读书账户下的所有书籍，包括文件夹深处的书籍。

  ![image-20250920232025843](D:\projects\WereadTool\assets\image-20250920232025843.png)

- **书籍信息展示**：以卡片形式清晰展示您的书架，包含封面、书名、作者、阅读进度和推荐值。

  ![image-20250920232110141](D:\projects\WereadTool\assets\image-20250920232110141.png)

- **笔记导出**：将任意一本书的划线和想法导出为 Markdown 或 HTML 格式，方便本地保存和查阅。

  ![image-20250920232140072](D:\projects\WereadTool\assets\image-20250920232140072.png)

- **书籍搜索**：在您的书架中快速搜索特定书籍。

  ![image-20250920233115420](D:\projects\WereadTool\assets\image-20250920233115420.png)

- **安全认证**：通过用户在浏览器中获取的 Cookie 进行认证，保障账户安全。

  ![image-20250920232409058](D:\projects\WereadTool\assets\image-20250920232409058.png)

## 🚀 技术栈

- **后端**:
  - [Python 3.11](https://www.python.org/)
  - [FastAPI](https://fastapi.tiangolo.com/): 高性能的 Web 框架
  - [Pydantic](https://docs.pydantic.dev/): 数据验证和设置管理
- **前端**:
  - [React](https://reactjs.org/)
  - [Vite](https://vitejs.dev/): 极速的现代前端构建工具
  - [TypeScript](https://www.typescriptlang.org/)
  - [Tailwind CSS](https://tailwindcss.com/): 功能类优先的 CSS 框架
- **部署**:
  - [Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/)
  - [Nginx](https://www.nginx.com/): 反向代理和静态文件服务

## 📂 项目结构

```
.
├── backend/         # FastAPI 后端应用
│   ├── routers/     # API 路由
│   ├── weread_api.py # 微信读书 API 核心封装
│   ├── main.py      # 应用主入口
│   └── ...
├── frontend/        # React 前端应用
│   ├── src/
│   │   ├── pages/   # 页面组件
│   │   ├── components/ # 可复用组件
│   │   └── App.tsx  # 主应用组件
│   └── ...
├── deploy/          # 部署相关脚本和配置
├── docker-compose.yml # Docker 编排文件
└── README.md        # 本文档
```

## 🛠️ 开发环境设置

请参考 `dev-setup.md` 文件进行详细的本地开发环境配置。

### 后端

```bash
# 1. 进入后端目录
cd backend

# 2. (推荐) 创建并激活 Conda 环境
conda create -n weread python=3.11
conda activate weread

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动开发服务器 (支持热重载)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
后端 API 文档地址: [http://localhost:8000/docs](http://localhost:8000/docs)

### 前端

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
npm install

# 3. 启动开发服务器
npm run dev
```
前端访问地址: [http://localhost:3000](http://localhost:3000)

## 🐳 Docker 部署

本项目提供了 `docker-compose.yml` 文件，可以一键启动整个应用。

```bash
# 在项目根目录运行
docker-compose up -d
```
该命令会构建并启动前端、后端和 Nginx 服务。应用将通过 Nginx 代理在 `80` 端口访问。

## 🔑 微信读书 API 规范

本项目通过模拟浏览器行为来调用微信读书的 Web API。核心认证方式是**基于 Cookie**。

### 1. 如何获取 Cookie

1.  在浏览器中打开并登录 [微信读书网页版](https://weread.qq.com/)。
2.  按 `F12` 打开开发者工具，切换到 **网络 (Network)** 标签。
3.  刷新页面，在请求列表中找到任意一个对 `weread.qq.com` 的请求（例如 `shelf` 或 `book`）。
4.  在右侧的 **标头 (Headers)** 面板中，找到 **请求标头 (Request Headers)** 部分。
5.  复制 `Cookie` 字段的完整值。

### 2. 核心 Cookie 字段

登录时，需要提供以下几个关键的 Cookie 值：

| 字段名      | 描述                               |
| :---------- | :--------------------------------- |
| `wr_gid`    | 用户组 ID                          |
| `wr_vid`    | 用户唯一标识符 (VID)               |
| `wr_skey`   | 会话密钥 (Session Key)，有有效期   |
| `wr_rt`     | 刷新令牌 (Refresh Token)，有有效期 |
| `wr_name`   | 用户昵称 (URL 编码)                |
| `wr_avatar` | 用户头像 URL (URL 编码)            |

### 3. 主要调用的 API 端点

本工具主要与以下几个微信读书的非官方 API 端点交互：

| HTTP 方法 | 端点路径                      | 主要用途                                                     |
| :-------- | :---------------------------- | :----------------------------------------------------------- |
| `GET`     | `/web/shelf`                  | **获取书架HTML**: 这是获取全量书籍ID最关键的一步。页面 `window.__INITIAL_STATE__` 中包含了 `rawBooks` (部分书籍详情) 和 `rawIndexes` (全量书籍ID索引)。 |
| `POST`    | `/web/shelf/syncBook`         | **批量同步书籍信息**: 通过传入书籍ID列表，可以高效获取这些书籍的详细信息，弥补 `/web/shelf` 未返回的详情。 |
| `GET`     | `/web/book/info`              | **获取单本书籍详情**: 获取指定 `bookId` 的书籍的详细元数据，如简介、出版社、ISBN等。 |
| `GET`     | `/web/book/bookmarklist`      | **获取书籍的划线和笔记**: 获取指定 `bookId` 的所有划线、想法等笔记内容。 |
| `POST`    | `/web/book/chapterInfos`      | **获取书籍章节列表**: 获取书籍的目录结构。                    |

### 4. 数据获取流程

1.  **登录**: 用户提交 Cookie，后端验证其有效性。
2.  **获取书架**:
    - 后端携带用户 Cookie 请求 `/web/shelf`，获取到包含书架数据的 HTML。
    - 解析 HTML 中的 `window.__INITIAL_STATE__`，提取出 `rawBooks` (已有部分详情的书籍) 和 `rawIndexes` (全量书籍ID)。
    - 对于仅有 ID 的书籍，分批调用 `/web/shelf/syncBook` 接口获取它们的详细信息。
    - 将两部分数据合并，得到完整的书架列表并缓存。
3.  **获取笔记**:
    - 当用户请求某本书的笔记时，后端携带 Cookie 调用 `/web/book/bookmarklist` 和 `/web/book/chapterInfos`。
    - 组合章节信息和笔记信息，格式化为 Markdown 或 HTML 返回给前端。

### 5. 参考

- [mcp-server-weread](https://github.com/ChenyqThu/mcp-server-weread)
- [wereader](https://github.com/arry-lee/wereader)

## 💡下一步计划

- 还没想好……

> **免责声明**: 本项目调用的所有 API接口随时可能发生变化，导致功能失效。请仅用于个人学习和研究，不要用于商业目的。
