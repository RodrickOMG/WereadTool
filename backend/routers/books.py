from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import math

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db
from models import User, UserBooks, BookCache
from schemas import BooksResponse, BookInfo, BookDetail, APIResponse
from auth import get_current_user
from weread_api import WeReadAPI

router = APIRouter()

def get_user_cookies(user: User) -> str:
    """Get formatted cookie string for user"""
    cookies = {
        'wr_gid': user.wr_gid,
        'wr_vid': user.wr_vid,
        'wr_skey': user.wr_skey,
        'wr_pf': '0',
        'wr_rt': user.wr_rt,
        'wr_localvid': user.wr_localvid or '',
        'wr_name': user.wr_name or '',
        'wr_avatar': user.wr_avatar or '',
        'wr_gender': user.wr_gender or ''
    }
    return '; '.join([f'{key}={value}' for key, value in cookies.items()])

@router.get("", response_model=APIResponse)
async def get_books(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's books with pagination"""
    try:
        # Get user books data from cache
        user_books = db.query(UserBooks).filter(UserBooks.user_id == current_user.id).first()

        if not user_books or not user_books.books_data:
            # If no cached data, fetch from WeRead API
            try:
                cookies = get_user_cookies(current_user)
                weread_api = WeReadAPI(cookies)

                # 先验证登录状态
                if not weread_api.login_success():
                    print("❌ 用户登录状态无效，需要重新登录")
                    return APIResponse(
                        success=False,
                        message="登录已过期，请重新登录",
                        data={
                            "books": [],
                            "total": 0,
                            "page": page,
                            "page_size": page_size,
                            "total_pages": 0,
                            "error": "LOGIN_EXPIRED",
                            "requires_login": True
                        }
                    )

                user_data = weread_api.get_user_data(current_user.wr_vid)

                # 检查返回的数据是否有效
                if not user_data or not isinstance(user_data, dict):
                    print("⚠️ API返回的数据无效")
                    return APIResponse(
                        success=True,
                        message="当前无法获取最新书籍数据，显示缓存数据",
                        data={
                            "books": [],
                            "total": 0,
                            "page": page,
                            "page_size": page_size,
                            "total_pages": 0,
                            "error": "API返回数据无效"
                        }
                    )

                # 检查是否有书籍数据
                books_list = user_data.get('books', [])
                if not books_list:
                    print("⚠️ 用户书架为空")
                    user_data = {"books": [], "user_vid": current_user.wr_vid, "empty": True}

                # Save to cache
                if user_books:
                    user_books.books_data = user_data
                else:
                    user_books = UserBooks(user_id=current_user.id, books_data=user_data)
                    db.add(user_books)
                db.commit()

            except Exception as api_error:
                error_str = str(api_error)
                print(f"⚠️ 微信读书API调用失败: {error_str}")

                # 检查是否是认证相关错误
                if "登录超时" in error_str or "errcode" in error_str:
                    return APIResponse(
                        success=False,
                        message="登录已过期，请重新登录",
                        data={
                            "books": [],
                            "total": 0,
                            "page": page,
                            "page_size": page_size,
                            "total_pages": 0,
                            "error": "LOGIN_EXPIRED",
                            "requires_login": True
                        }
                    )
                else:
                    # 返回空数据而不是抛出异常
                    return APIResponse(
                        success=True,
                        message="当前无法获取最新书籍数据，可能需要重新登录",
                        data={
                            "books": [],
                            "total": 0,
                            "page": page,
                            "page_size": page_size,
                            "total_pages": 0,
                            "error": "API调用失败，请检查网络连接"
                        }
                    )
        else:
            user_data = user_books.books_data

        # Get books list
        books_data = user_data.get('books', [])

        # Sort by reading time (most recent first)
        books_data.sort(key=lambda x: x.get('readUpdateTime', 0), reverse=True)

        # Calculate pagination
        total = len(books_data)
        total_pages = math.ceil(total / page_size)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        # Get page data
        page_books = books_data[start_idx:end_idx]

        # Fetch detailed info for books on current page
        cookies = get_user_cookies(current_user)
        weread_api = WeReadAPI(cookies)
        detailed_books = []

        for book in page_books:
            try:
                # Check cache first
                cached_book = db.query(BookCache).filter(BookCache.book_id == book['bookId']).first()

                if cached_book:
                    book_info = cached_book.book_info
                else:
                    # Fetch from API and cache
                    book_info = weread_api.get_book_info(book['bookId'])
                    cache_entry = BookCache(book_id=book['bookId'], book_info=book_info)
                    db.add(cache_entry)
                    db.commit()

                detailed_books.append({
                    'bookId': book['bookId'],
                    'title': book_info.get('title', ''),
                    'author': book_info.get('author', ''),
                    'cover': book_info.get('cover', '').replace('s_', 't7_'),
                    'finishReading': book_info.get('finishReading', 0),
                    'category': book_info.get('category', ''),
                    'newRatingDetail': book_info.get('newRatingDetail', {}).get('title', ''),
                    'readUpdateTime': book.get('readUpdateTime', 0)
                })

            except Exception as e:
                print(f"Error fetching book info for {book['bookId']}: {e}")
                # Use basic info from cached data
                detailed_books.append({
                    'bookId': book['bookId'],
                    'title': book.get('title', ''),
                    'author': book.get('author', ''),
                    'cover': book.get('cover', '').replace('s_', 't7_'),
                    'finishReading': book.get('finishReading', 0),
                    'category': book.get('category', ''),
                    'newRatingDetail': '',
                    'readUpdateTime': book.get('readUpdateTime', 0)
                })

        return APIResponse(
            success=True,
            message="Books retrieved successfully",
            data={
                "books": detailed_books,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get books: {str(e)}")

@router.get("/{book_id}", response_model=APIResponse)
async def get_book_detail(
    book_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed information for a specific book"""
    try:
        # Check cache first
        cached_book = db.query(BookCache).filter(BookCache.book_id == book_id).first()

        if cached_book:
            book_info = cached_book.book_info
        else:
            # Fetch from API
            cookies = get_user_cookies(current_user)
            weread_api = WeReadAPI(cookies)
            book_info = weread_api.get_book_info(book_id)

            # Cache the result
            cache_entry = BookCache(book_id=book_id, book_info=book_info)
            db.add(cache_entry)
            db.commit()

        return APIResponse(
            success=True,
            message="Book detail retrieved successfully",
            data={
                "bookId": book_id,
                "title": book_info.get('title', ''),
                "author": book_info.get('author', ''),
                "cover": book_info.get('cover', '').replace('s_', 't7_'),
                "intro": book_info.get('intro', ''),
                "publisher": book_info.get('publisher', ''),
                "category": book_info.get('category', ''),
                "newRatingDetail": book_info.get('newRatingDetail', {}).get('title', '')
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get book detail: {str(e)}")

@router.post("/refresh", response_model=APIResponse)
async def refresh_books(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Refresh user's books from WeRead API"""
    try:
        cookies = get_user_cookies(current_user)
        weread_api = WeReadAPI(cookies)
        user_data = weread_api.get_user_data(current_user.wr_vid)

        # Update cached data
        user_books = db.query(UserBooks).filter(UserBooks.user_id == current_user.id).first()
        if user_books:
            user_books.books_data = user_data
        else:
            user_books = UserBooks(user_id=current_user.id, books_data=user_data)
            db.add(user_books)

        db.commit()

        return APIResponse(
            success=True,
            message="Books refreshed successfully"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh books: {str(e)}")