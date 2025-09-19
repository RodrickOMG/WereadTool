from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
import json
import uuid
import requests

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db
from models import User, UserBooks
from schemas import WeReadLogin, Token, User as UserSchema, APIResponse
from auth import create_access_token, get_current_user
from weread_api import WeReadAPI
from cookie_manager import cookie_manager
# 现在使用前端微信JS SDK登录，不再需要后端Selenium登录服务
try:
    from config import settings
except ImportError:
    from config_simple import settings

router = APIRouter()

@router.post("/login", response_model=APIResponse)
async def login(login_data: WeReadLogin, db: Session = Depends(get_db)):
    """
    微信读书登录 - 参考mcp-server-weread项目实现
    支持更灵活的Cookie验证和用户体验
    """
    try:
        # 构建Cookie字典（包含所有用户信息）
        cookies = {
            'wr_gid': login_data.wr_gid,
            'wr_vid': login_data.wr_vid,
            'wr_skey': login_data.wr_skey,
            'wr_rt': login_data.wr_rt,
            'wr_name': login_data.wr_name or '',
            'wr_avatar': login_data.wr_avatar or '',
            'wr_localvid': login_data.wr_localvid or '',
            'wr_gender': login_data.wr_gender or '',
            'wr_pf': login_data.wr_pf or '0'
        }
        
        # 1. 基本格式验证
        is_valid_format, format_message = cookie_manager.validate_cookie_format(cookies)
        if not is_valid_format:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cookie格式错误: {format_message}"
            )
        
        # 2. 格式化Cookie
        cookie_string = cookie_manager.format_cookie_for_api(cookies)
        print(f"尝试登录用户: {login_data.wr_vid}")
        
        # 3. 测试Cookie有效性 (参考mcp-server-weread的验证方式)
        is_valid, validation_message, user_info = cookie_manager.test_cookie_validity(cookie_string)

        # 4. 使用WeReadAPI进行更全面的验证
        api_valid = False
        api_message = ""
        try:
            weread_api = WeReadAPI(cookie_string)
            api_valid = weread_api.login_success()
            api_message = "API验证成功" if api_valid else "API验证失败"
            print(f"🔍 WeReadAPI验证结果: {api_message}")
        except Exception as api_error:
            print(f"⚠️ WeReadAPI验证出错: {api_error}")
            api_message = f"API验证出错: {str(api_error)}"

        # 5. 获取书架预览 (进一步验证)
        bookshelf_valid = False
        bookshelf_data = {}
        if is_valid or api_valid:
            bookshelf_valid, bookshelf_message, bookshelf_data = cookie_manager.get_bookshelf_preview(
                cookie_string, login_data.wr_vid
            )
            print(f"📚 书架验证结果: {bookshelf_message}")

        # 6. 决定登录策略
        login_mode = "unknown"
        if api_valid and bookshelf_valid:
            login_mode = "verified"  # 完全验证通过
            print(f"✅ 用户 {login_data.wr_vid} 登录验证完全通过")
        elif api_valid or (is_valid and bookshelf_valid):
            login_mode = "partial"   # 部分验证通过
            print(f"⚠️ 用户 {login_data.wr_vid} 部分验证通过")
        elif is_valid:
            login_mode = "basic"     # 基本验证通过
            print(f"🔶 用户 {login_data.wr_vid} 基本验证通过")
        else:
            login_mode = "dev"       # 开发模式，允许继续
            print(f"🔧 用户 {login_data.wr_vid} 进入开发模式: {validation_message}")

        # 7. 提取或设置用户信息
        if user_info:
            extracted_user_info = cookie_manager.extract_user_info(user_info)
            cookies.update(extracted_user_info)
        
        # 7. 数据库操作
        user = db.query(User).filter(User.wr_vid == login_data.wr_vid).first()
        
        if not user:
            # 创建新用户（优先使用前端传递的信息）
            user = User(
                wr_vid=login_data.wr_vid,
                wr_gid=login_data.wr_gid,
                wr_skey=login_data.wr_skey,
                wr_rt=login_data.wr_rt,
                wr_name=login_data.wr_name or cookies.get('wr_name', ''),
                wr_avatar=login_data.wr_avatar or cookies.get('wr_avatar', ''),
                wr_localvid=login_data.wr_localvid or cookies.get('wr_localvid', ''),
                wr_gender=login_data.wr_gender or cookies.get('wr_gender', '')
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"✨ 创建新用户: {login_data.wr_vid}")
        else:
            # 更新现有用户（优先使用前端传递的信息）
            user.wr_gid = login_data.wr_gid
            user.wr_skey = login_data.wr_skey
            user.wr_rt = login_data.wr_rt
            
            # 更新用户信息，优先使用前端传递的数据
            if login_data.wr_name or cookies.get('wr_name'):
                user.wr_name = login_data.wr_name or cookies.get('wr_name', '')
            if login_data.wr_avatar or cookies.get('wr_avatar'):
                user.wr_avatar = login_data.wr_avatar or cookies.get('wr_avatar', '')
            if login_data.wr_localvid or cookies.get('wr_localvid'):
                user.wr_localvid = login_data.wr_localvid or cookies.get('wr_localvid', '')
            if login_data.wr_gender or cookies.get('wr_gender'):
                user.wr_gender = login_data.wr_gender or cookies.get('wr_gender', '')
                
            db.commit()
            print(f"🔄 更新用户信息: {login_data.wr_vid} - {user.wr_name}")


        # 8. 缓存用户数据 (参考mcp-server-weread的数据获取方式)
        cached_books_count = 0
        cache_success = False
        if bookshelf_valid and bookshelf_data:
            try:
                # 直接使用已获取的书架数据
                user_books = db.query(UserBooks).filter(UserBooks.user_id == user.id).first()
                if not user_books:
                    user_books = UserBooks(user_id=user.id, books_data=bookshelf_data)
                    db.add(user_books)
                else:
                    user_books.books_data = bookshelf_data
                
                db.commit()
                cached_books_count = len(bookshelf_data.get('books', []))
                cache_success = True
                print(f"📚 缓存书架数据成功: {cached_books_count}本书")
                
            except Exception as e:
                print(f"⚠️ 缓存书架数据失败: {e}")
        elif login_mode == "verified" or login_mode == "partial":
            # 尝试通过API获取数据
            try:
                weread_api = WeReadAPI(cookie_string)
                user_data = weread_api.get_user_data(login_data.wr_vid)
                
                user_books = db.query(UserBooks).filter(UserBooks.user_id == user.id).first()
                if not user_books:
                    user_books = UserBooks(user_id=user.id, books_data=user_data)
                    db.add(user_books)
                else:
                    user_books.books_data = user_data
                
                db.commit()
                cached_books_count = len(user_data.get('books', []))
                cache_success = True
                print(f"📚 通过API缓存数据成功: {cached_books_count}本书")
                
            except Exception as e:
                print(f"⚠️ API缓存数据失败: {e}")
        else:
            print(f"⏭️ 跳过数据缓存 - 登录模式: {login_mode}")

        # Create access token
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )

        # 9. 生成登录响应 (参考mcp-server-weread的响应格式)
        login_messages = {
            "verified": "登录成功，微信读书验证通过",
            "partial": "登录成功，部分功能可用", 
            "dev": "登录成功（开发模式）"
        }
        
        response_data = {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "wr_vid": user.wr_vid,
                "wr_name": user.wr_name or "未获取",
                "wr_avatar": user.wr_avatar or ""
            },
            "login_mode": login_mode,
            "weread_verified": login_mode in ["verified", "partial"],
            "cached_books_count": cached_books_count,
            "cache_success": cache_success,
            "validation_message": validation_message if login_mode == "dev" else "验证通过"
        }
        
        return APIResponse(
            success=True,
            message=login_messages.get(login_mode, "登录成功"),
            data=response_data
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.get("/me", response_model=APIResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return APIResponse(
        success=True,
        message="User information retrieved",
        data={
            "id": current_user.id,
            "wr_vid": current_user.wr_vid,
            "wr_name": current_user.wr_name,
            "wr_avatar": current_user.wr_avatar,
            "is_active": current_user.is_active,
            "created_at": current_user.created_at
        }
    )

@router.post("/logout", response_model=APIResponse)
async def logout():
    """Logout user (client should remove token)"""
    return APIResponse(
        success=True,
        message="Logged out successfully"
    )


# WeChat Login APIs
@router.post("/wechat/login", response_model=APIResponse)
async def wechat_login(code_data: dict, db: Session = Depends(get_db)):
    """Handle WeChat OAuth login"""
    try:
        code = code_data.get('code')
        if not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization code is required"
            )

        # 微信读书的AppID和AppSecret（这些需要从微信读书官方获取）
        appid = "wx09c7c5f8e2f8f890"
        appsecret = "your_wechat_app_secret"  # 需要从配置文件中获取

        # 使用授权码获取access_token
        token_url = f"https://api.weixin.qq.com/sns/oauth2/access_token?appid={appid}&secret={appsecret}&code={code}&grant_type=authorization_code"

        response = requests.get(token_url)
        token_data = response.json()

        if 'errcode' in token_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"WeChat OAuth error: {token_data.get('errmsg', 'Unknown error')}"
            )

        access_token = token_data.get('access_token')
        openid = token_data.get('openid')

        if not access_token or not openid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get access token from WeChat"
            )

        # 获取用户信息
        user_url = f"https://api.weixin.qq.com/sns/userinfo?access_token={access_token}&openid={openid}"
        user_response = requests.get(user_url)
        user_data = user_response.json()

        if 'errcode' in user_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"WeChat user info error: {user_data.get('errmsg', 'Unknown error')}"
            )

        # 由于微信读书有自己的用户体系，我们需要将微信用户信息映射到微信读书
        # 这里需要通过微信读书的API进行用户认证
        # 目前先返回用户信息，实际实现需要根据微信读书的具体API

        # 检查用户是否已存在（基于openid）
        user = db.query(User).filter(User.wr_vid == openid).first()

        if not user:
            # 创建新用户
            user = User(
                wr_vid=openid,
                wr_gid="",  # 微信读书相关的cookie信息
                wr_skey="",
                wr_rt="",
                wr_name=user_data.get('nickname', ''),
                wr_avatar=user_data.get('headimgurl', '')
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # 更新用户信息
            user.wr_name = user_data.get('nickname', user.wr_name)
            user.wr_avatar = user_data.get('headimgurl', user.wr_avatar)
            db.commit()

        # 创建访问令牌
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        jwt_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )

        # 获取用户读书数据（如果可能的话）
        try:
            # 这里可以调用微信读书API获取用户数据
            # user_books_data = weread_api.get_user_data(user.wr_vid)
            pass
        except Exception as e:
            print(f"Failed to fetch user books data: {e}")

        return APIResponse(
            success=True,
            message="WeChat login successful",
            data={
                "access_token": jwt_token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "wr_vid": user.wr_vid,
                    "wr_name": user.wr_name,
                    "wr_avatar": user.wr_avatar
                },
                "wechat_info": {
                    "nickname": user_data.get('nickname'),
                    "headimgurl": user_data.get('headimgurl'),
                    "sex": user_data.get('sex'),
                    "province": user_data.get('province'),
                    "city": user_data.get('city'),
                    "country": user_data.get('country')
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"WeChat login failed: {str(e)}"
        )

@router.get("/wechat/callback")
async def wechat_callback(code: str = None, state: str = None):
    """WeChat OAuth callback endpoint (for traditional OAuth flow)"""
    if not code:
        return {"error": "No authorization code provided"}

    return {
        "code": code,
        "state": state,
        "message": "This is a callback endpoint. Use POST /auth/wechat/login for actual login processing."
    }

# 参考 wereader 项目实现的微信读书 cookie 登录功能
@router.post("/weread/cookie-login", response_model=APIResponse)
async def weread_cookie_login(cookie_data: dict, db: Session = Depends(get_db)):
    """WeRead cookie-based login (参考 wereader 项目实现)"""
    try:
        # 从前端提取的cookie中获取微信读书登录信息
        cookies = cookie_data.get('cookies', {})
        
        # 提取必要的微信读书 cookie 参数
        wr_gid = cookies.get('wr_gid', '')
        wr_vid = cookies.get('wr_vid', '')
        wr_skey = cookies.get('wr_skey', '')
        wr_rt = cookies.get('wr_rt', '')
        wr_name = cookies.get('wr_name', '')
        wr_avatar = cookies.get('wr_avatar', '')
        
        if not all([wr_gid, wr_vid, wr_skey, wr_rt]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="缺少必要的微信读书登录信息"
            )
        
        # 格式化 cookies 用于 WeRead API
        formatted_cookies = {
            'wr_gid': wr_gid,
            'wr_vid': wr_vid,
            'wr_skey': wr_skey,
            'wr_pf': '0',
            'wr_rt': wr_rt,
            'wr_localvid': cookies.get('wr_localvid', ''),
            'wr_name': wr_name,
            'wr_avatar': wr_avatar,
            'wr_gender': cookies.get('wr_gender', '')
        }
        
        cookie_string = '; '.join([f'{key}={value}' for key, value in formatted_cookies.items()])
        
        # 测试微信读书 API 登录
        weread_api = WeReadAPI(cookie_string)
        
        if not weread_api.login_success():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="微信读书登录验证失败，请重新登录"
            )
        
        # 检查用户是否存在
        user = db.query(User).filter(User.wr_vid == wr_vid).first()
        
        if not user:
            # 创建新用户
            user = User(
                wr_vid=wr_vid,
                wr_gid=wr_gid,
                wr_skey=wr_skey,
                wr_rt=wr_rt,
                wr_name=wr_name,
                wr_avatar=wr_avatar,
                wr_localvid=cookies.get('wr_localvid', ''),
                wr_gender=cookies.get('wr_gender', '')
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # 更新现有用户凭证
            user.wr_gid = wr_gid
            user.wr_skey = wr_skey
            user.wr_rt = wr_rt
            user.wr_name = wr_name
            user.wr_avatar = wr_avatar
            user.wr_localvid = cookies.get('wr_localvid', '')
            user.wr_gender = cookies.get('wr_gender', '')
            db.commit()
        
        # 尝试获取并缓存用户数据  
        cache_success = False
        try:
            user_data = weread_api.get_user_data(wr_vid)
            
            # 保存或更新用户书籍数据
            user_books = db.query(UserBooks).filter(UserBooks.user_id == user.id).first()
            if not user_books:
                user_books = UserBooks(user_id=user.id, books_data=user_data)
                db.add(user_books)
            else:
                user_books.books_data = user_data
            
            db.commit()
            cache_success = True
            print(f"✅ 成功缓存 {len(user_data.get('books', []))} 本书籍数据")
        except Exception as e:
            print(f"⚠️ 缓存用户数据失败: {e}")
            # 开发模式下允许缓存失败
        
        # 创建访问令牌
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )
        
        return APIResponse(
            success=True,
            message="微信读书登录成功",
            data={
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "wr_vid": user.wr_vid,
                    "wr_name": user.wr_name,
                    "wr_avatar": user.wr_avatar
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"微信读书登录失败: {str(e)}"
        )

# 已移除不再使用的cookie提取API路由，现在使用简化的登录方式