#!/usr/bin/env python3
"""
简化版启动脚本 - 适用于有依赖问题的环境
"""

import os
import sys

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from fastapi import FastAPI, HTTPException, status
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    import uvicorn
    from datetime import datetime

    print("✅ 基础依赖加载成功")

    # 创建应用
    app = FastAPI(
        title="WeRead Tool API",
        description="微信读书助手 API",
        version="1.0.0"
    )

    # 配置 CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    async def root():
        return {"message": "WeRead Tool API is running", "docs": "/docs"}

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "timestamp": datetime.now()}

    # 尝试加载完整功能
    try:
        from database import get_db, engine
        from models import Base
        from routers import auth, books, notes, search

        # 创建数据库表
        Base.metadata.create_all(bind=engine)

        # 包含路由
        app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
        app.include_router(books.router, prefix="/api/books", tags=["books"])
        app.include_router(notes.router, prefix="/api/notes", tags=["notes"])
        app.include_router(search.router, prefix="/api/search", tags=["search"])

        print("✅ 完整功能加载成功")

    except Exception as e:
        print(f"⚠️  部分功能加载失败: {e}")
        print("⚠️  运行在基础模式下")

        @app.get("/api/status")
        async def status():
            return {"status": "running in basic mode", "error": str(e)}

    if __name__ == "__main__":
        print("🚀 启动 WeRead Tool API...")
        print("📊 服务信息：")
        print("   - 地址: http://localhost:8000")
        print("   - 文档: http://localhost:8000/docs")
        print("   - 健康检查: http://localhost:8000/health")
        print("")

        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=True
        )

except ImportError as e:
    print(f"❌ 缺少依赖: {e}")
    print("")
    print("请安装以下依赖:")
    print("pip install fastapi uvicorn")
    sys.exit(1)
except Exception as e:
    print(f"❌ 启动失败: {e}")
    sys.exit(1)