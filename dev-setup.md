# 开发环境快速设置

## 后端设置 (conda 环境)

```bash
# 1. 创建 conda 环境（如果还没有）
conda create -n weread python=3.11
conda activate weread

# 2. 安装依赖
cd backend
pip install -r requirements.txt

# 3. 启动后端服务
python main.py
# 或者
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 前端设置

```bash
# 1. 安装依赖
cd frontend
npm install

# 2. 启动前端开发服务器
npm run dev
```

## 访问地址

- 前端：http://localhost:3000
- 后端API：http://localhost:8000
- API文档：http://localhost:8000/docs

## 常见问题解决

### 1. pydantic 导入错误
```bash
pip install --upgrade pydantic pydantic-settings
```

### 2. 依赖版本冲突
```bash
pip install --force-reinstall -r requirements.txt
```

### 3. 前端依赖问题
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## 开发建议

1. 后端使用 `uvicorn main:app --reload` 启动，支持热重载
2. 前端使用 `npm run dev` 启动，支持热重载
3. 修改代码后会自动重启服务
4. 查看 API 文档：http://localhost:8000/docs