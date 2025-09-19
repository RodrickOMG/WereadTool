#!/usr/bin/env python3
"""
最简测试启动脚本
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试各个模块的导入"""
    print("🔍 测试模块导入...")

    try:
        print("  📦 测试 FastAPI...")
        from fastapi import FastAPI
        print("  ✅ FastAPI 导入成功")
    except Exception as e:
        print(f"  ❌ FastAPI 导入失败: {e}")
        return False

    try:
        print("  📦 测试配置...")
        from config_simple import settings
        print("  ✅ 配置导入成功")
    except Exception as e:
        print(f"  ❌ 配置导入失败: {e}")
        return False

    try:
        print("  📦 测试数据库...")
        from database import get_db
        print("  ✅ 数据库导入成功")
    except Exception as e:
        print(f"  ❌ 数据库导入失败: {e}")
        return False

    try:
        print("  📦 测试认证...")
        from auth import create_access_token
        print("  ✅ 认证模块导入成功")
    except Exception as e:
        print(f"  ❌ 认证模块导入失败: {e}")
        return False

    try:
        print("  📦 测试路由...")
        from routers import auth
        print("  ✅ 路由导入成功")
    except Exception as e:
        print(f"  ❌ 路由导入失败: {e}")
        print(f"     详细错误: {str(e)}")
        return False

    return True

def start_simple_server():
    """启动简化服务器"""
    try:
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        import uvicorn
        from datetime import datetime

        app = FastAPI(title="WeRead Tool API - Test")

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @app.get("/")
        async def root():
            return {"message": "WeRead Tool API Test is running"}

        @app.get("/health")
        async def health():
            return {"status": "healthy", "timestamp": datetime.now()}

        print("🚀 启动测试服务器...")
        uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return False

if __name__ == "__main__":
    print("🧪 WeRead Tool 导入测试")
    print("=" * 40)

    if test_imports():
        print("\n✅ 所有模块导入成功！")
        print("🚀 尝试启动完整服务器...")

        try:
            from start_simple import app
            import uvicorn
            uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
        except Exception as e:
            print(f"⚠️  完整服务器启动失败: {e}")
            print("🔄 启动简化服务器...")
            start_simple_server()
    else:
        print("\n❌ 模块导入失败")
        print("🔄 启动最小服务器...")
        start_simple_server()