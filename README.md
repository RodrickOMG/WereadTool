# WeRead Tool - 微信读书助手

现代化的微信读书工具，支持书架管理、笔记导出、书籍搜索等功能。

## 功能特性

- 🔐 **安全的微信读书登录验证**
  - ✅ 前端微信官方JS SDK二维码登录（无需Selenium）
  - ✅ 后端JWT令牌认证
  - ✅ 支持表单手动登录（兼容性保障）
- 📚 个人书架浏览与管理
- 📝 读书笔记提取与导出（Markdown格式）
- 🔍 书籍搜索功能
- 📖 书籍详情查看
- 💭 想法/评论管理
- 🔥 热门标注查看

## 技术栈

### 后端
- **FastAPI** - 现代化 Python Web 框架
- **SQLAlchemy** - ORM 数据库操作
- **Pydantic** - 数据验证和序列化
- **JWT** - 用户认证
- **SQLite/PostgreSQL** - 数据存储

### 前端
- **React 18** - 用户界面框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **Tailwind CSS** - 样式框架
- **React Query** - 数据获取和缓存

### 部署
- **Docker** - 容器化部署
- **Docker Compose** - 多容器编排
- **Nginx** - 反向代理

## 快速开始

### 开发环境

1. 克隆项目
```bash
git clone <repository-url>
cd WereadTool
```

2. 后端开发
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

3. 前端开发
```bash
cd frontend
npm install
npm run dev
```

### Docker 部署

```bash
docker-compose up -d
```

访问 http://localhost:3000

## 项目结构

```
WereadTool/
├── .gitignore           # Git忽略文件配置
├── README.md            # 项目说明文档
├── docker-compose.yml   # Docker容器编排配置
├── nginx.conf           # Nginx反向代理配置
├── backend/             # 后端服务
│   ├── main.py         # FastAPI应用入口
│   ├── routers/        # API路由模块
│   ├── models.py       # 数据模型
│   ├── schemas.py      # Pydantic数据验证
│   ├── weread_api.py   # 微信读书API封装
│   ├── cookie_manager.py # Cookie管理工具
│   ├── database.py     # 数据库操作
│   ├── config.py       # 配置文件
│   └── requirements.txt # Python依赖
├── frontend/            # 前端应用
│   ├── src/
│   │   ├── App.tsx     # 主应用组件
│   │   ├── pages/      # 页面组件
│   │   ├── components/ # 通用组件
│   │   ├── stores/     # 状态管理
│   │   └── lib/        # 工具库
│   ├── package.json    # Node.js依赖
│   ├── vite.config.ts  # Vite构建配置
│   └── tailwind.config.js # Tailwind样式配置
└── deploy/              # 部署相关文件
    ├── docker-compose.simple.yml
    ├── nginx-config-example.conf
    ├── start.sh
    └── stop.sh
```

## 版本控制

项目已配置完整的 `.gitignore` 文件，自动忽略以下类型文件：

### Python相关
- `__pycache__/` - Python缓存文件
- `*.pyc`, `*.pyo` - 编译后的字节码文件
- 虚拟环境目录（`venv/`, `.env/`等）
- 测试覆盖率文件（`.coverage`, `htmlcov/`等）

### Node.js相关
- `node_modules/` - Node.js依赖包
- `npm-debug.log*`, `yarn-error.log*` - npm/yarn日志
- 构建产物（`dist/`, `build/`等）
- 缓存文件（`.cache/`, `.parcel-cache/`等）

### 数据库和日志
- `*.db`, `*.sqlite*` - 数据库文件
- `*.log` - 日志文件
- `logs/` - 日志目录

### IDE和系统文件
- `.vscode/`, `.idea/` - IDE配置文件
- `.DS_Store`, `Thumbs.db` - 系统生成文件
- `*.swp`, `*.tmp` - 临时文件

### 项目特定
- `weread.db` - 微信读书数据库文件
- `frontend/dist/`, `backend/dist/` - 构建目录
- `.env*` - 环境变量文件

## 登录方式说明

### 微信读书扫码登录（推荐）

参考 [wereader 项目](https://github.com/arry-lee/wereader) 实现的扫码登录功能，具有以下优势：

- 🚀 **自动获取Cookie** - 扫码登录后自动提取微信读书登录凭证
- 🔒 **安全可靠** - 直接使用微信读书官方登录，无需第三方授权
- ⚡ **操作简便** - 一键登录，无需手动复制cookie
- 📱 **用户体验佳** - 内嵌微信读书页面，登录体验原生化

### 登录流程（参考 wereader 项目）

1. 用户点击"扫码登录"
2. 系统显示内嵌的微信读书登录页面
3. 用户在页面中使用微信扫码登录
4. 登录完成后点击"获取登录凭证"按钮
5. 系统自动提取微信读书 cookies
6. 后端验证 cookies 有效性并创建JWT令牌
7. 用户成功登录

### 技术实现特点

本项目参考了 [arry-lee/wereader](https://github.com/arry-lee/wereader) 的实现思路：

- **内嵌浏览器** - 使用iframe直接加载微信读书页面
- **Cookie自动提取** - 登录成功后自动获取必要的认证cookie
- **智能验证** - 后端自动验证cookie有效性
- **无需Selenium** - 纯前端实现，无需后端浏览器自动化

### 兼容性保障

如果扫码登录不可用，系统提供表单登录方式作为备选：

1. 访问微信读书官网手动获取登录cookies
2. 在表单中填入 `wr_gid`、`wr_vid`、`wr_skey`、`wr_rt` 参数
3. 提交表单完成登录

### Cookie参数说明

系统需要以下微信读书cookie参数：

- `wr_gid` - 用户组ID
- `wr_vid` - 用户ID  
- `wr_skey` - 会话密钥
- `wr_rt` - 刷新令牌
- `wr_name` - 用户昵称（可选）
- `wr_avatar` - 用户头像（可选）

## API 文档

开发环境下访问 http://localhost:8000/docs 查看自动生成的 API 文档。

## 更新日志

### v2.2.0 - 2025年用户信息和书架解析全面增强

基于用户反馈，全面改进了Cookie解析和用户信息提取功能，解决了用户名、头像无法显示和书架信息提取失败的问题：

#### 🔧 前端Cookie解析增强
- **完整字段支持** - 前端现在支持解析所有用户相关Cookie字段（wr_name、wr_avatar、wr_localvid、wr_gender等）
- **智能URL解码** - 自动解码URL编码的用户名和头像信息，确保中文用户名正确显示
- **类型安全改进** - 更新TypeScript类型定义，支持可选的用户信息字段

#### 🛠️ 后端用户信息提取优化  
- **安全URL解码** - 新增`safe_unquote`函数，支持UTF-8和GBK多种编码方式的安全解码
- **多重解码策略** - 当UTF-8解码失败时自动尝试GBK编码，兼容各种用户名格式
- **用户信息扩展** - `extract_user_info`方法现在提取更多用户相关信息，包括所有Cookie字段

#### 📚 HTML书架解析重构
- **多层次解析策略** - 新增JavaScript数据、HTML元素、JSON脚本三种解析方法
- **智能模式匹配** - 支持多种书籍数据模式识别（books、bookList、shelfData等）
- **微信读书特化** - 针对微信读书页面结构特点，支持window.__INITIAL_STATE__等特殊模式
- **调试信息完善** - 当解析失败时提供详细的调试信息和HTML预览
- **数据标准化** - 新增`_normalize_book_data`方法，统一不同来源的书籍数据格式

#### 🎯 用户体验改进
- **即时信息显示** - 登录后立即显示用户头像和昵称，无需刷新页面
- **优雅降级** - 当头像不可用时显示默认图标，当昵称为空时显示用户ID
- **详细日志** - 改进后端日志输出，方便问题排查和调试

#### 🔄 API兼容性提升
- **向后兼容** - 新的解析逻辑完全兼容现有的登录流程
- **扩展性设计** - 新增的字段为可选项，不影响现有用户的使用体验

### v2.1.0 - 2025年API稳定性修复

针对微信读书API变更进行全面修复，提升系统稳定性和错误处理能力：

#### 核心修复
- 🔧 **API多端点备用机制** - 新增5个备用API端点，当主端点失败时自动切换
- 🛡️ **智能登录验证** - 改进login_success方法，支持关键/非关键端点分类验证
- ⚡ **增强错误处理** - API调用失败时返回用户友好的错误信息，而不是崩溃
- 🔄 **自动降级策略** - 当API不可用时，优先使用缓存数据，确保功能可用性

#### 技术改进
- **WeReadAPI类增强** - get_user_data、get_book_info、get_bookmarks方法均支持多端点fallback
- **认证逻辑优化** - 登录时进行多层次验证，提高成功率
- **响应式错误处理** - 区分认证过期和其他错误类型，提供针对性解决方案
- **缓存策略改进** - API失败时不清除缓存，优先使用已有数据

#### API稳定性提升
- 书架数据获取：新增`/web/bookshelf`、`/user/bookshelf`等备用端点，支持HTML页面解析
- 书籍信息获取：支持`/web/book/info`、`/book/detail`等多个端点，处理HTML响应
- 书签数据获取：兼容`/web/book/bookmarklist`等新端点格式，支持HTML页面降级
- 登录状态验证：支持`/web/user`、`/user/profile`等多端点验证，HTML页面视为成功
- HTML数据解析：新增从网页中提取书籍数据的智能解析功能

#### 核心技术改进
- **HTML响应处理** - 识别微信读书API返回HTML页面的新特性，将其视为有效响应
- **智能数据提取** - 从HTML页面中解析JavaScript变量和API调用，提取书籍信息
- **降级策略优化** - 当API返回HTML时，提供基础数据结构，确保系统功能可用
- **验证逻辑重构** - 重新设计登录验证流程，适应微信读书API的新响应格式
- **双域名架构** - 区分API域名(i.weread.qq.com)和Web域名(weread.qq.com)，使用正确的请求头
- **浏览器兼容** - 模拟真实浏览器请求头，包括Sec-Ch-Ua等现代安全头
- **Cookie增强解析** - 支持URL编码的用户名和头像信息自动解码
- **验证方式简化** - 去除无效的API端点验证，专注网页访问权限验证

#### 升级指南
1. 自动升级，无需手动操作
2. 系统会自动检测并使用可用的API端点
3. 当遇到"登录超时"错误时，建议用户重新登录获取新的Cookie

### v2.0.0 - 2024年登录功能重构

参考 [arry-lee/wereader](https://github.com/arry-lee/wereader) 项目，实现了全新的扫码登录功能：

#### 新增功能
- 🔄 **全新扫码登录** - 参考wereader项目，实现内嵌微信读书页面登录
- 🍪 **自动Cookie提取** - 登录成功后自动获取必要的认证信息
- 🔧 **Cookie提取工具** - 新增`cookie_extractor.py`模块，提供完整的cookie处理功能
- 🌐 **改进的API接口** - 新增`/auth/weread/cookie-login`和`/auth/extract-cookies`接口

#### 技术改进
- **前端组件升级** - `WechatQrLogin`组件完全重构，支持iframe内嵌登录
- **后端API扩展** - 新增微信读书cookie验证和用户信息获取功能
- **WeReadAPI增强** - 添加cookie格式化和解析工具方法
- **更好的错误处理** - 完善的登录状态检查和错误提示

#### 移除的功能
- 原有的微信OAuth登录方式（保留代码但不推荐使用）
- 复杂的第三方授权流程

#### 升级指南
1. 更新前端和后端代码
2. 新用户可直接使用扫码登录功能
3. 现有用户数据和API保持兼容

## 致谢

特别感谢 [arry-lee/wereader](https://github.com/arry-lee/wereader) 项目提供的技术思路和实现参考。

## 许可证

MIT License