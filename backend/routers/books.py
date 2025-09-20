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
    mode: str = Query("all", description="加载模式: rawbooks, all"),
    filter: str = Query("all", description="筛选条件: all, read, unread"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's books with pagination"""
    try:
        # Get user books data from cache
        user_books = db.query(UserBooks).filter(UserBooks.user_id == current_user.id).first()

        print(f"📋 检查用户书籍缓存: user_id={current_user.id}")
        if user_books:
            books_data = user_books.books_data
            if books_data and isinstance(books_data, dict):
                cached_books = books_data.get('books', [])
                print(f"   ✅ 找到缓存数据: {len(cached_books)} 本书")
                print(f"   📋 数据源: {books_data.get('source', 'unknown')}")
            else:
                print(f"   ⚠️ 缓存数据无效: {type(books_data)}")
        else:
            print(f"   ❌ 未找到用户书籍缓存记录")

        # 检查缓存数据是否有效且包含书籍
        need_refresh = False
        if not user_books or not user_books.books_data:
            need_refresh = True
            print("   🔄 需要刷新：无缓存数据")
        else:
            books_data = user_books.books_data
            if not isinstance(books_data, dict):
                need_refresh = True
                print("   🔄 需要刷新：缓存数据格式无效")
            else:
                cached_books = books_data.get('books', [])
                if not cached_books or len(cached_books) == 0:
                    need_refresh = True
                    print("   🔄 需要刷新：缓存的书籍列表为空")
                else:
                    print(f"   ✅ 使用缓存数据: {len(cached_books)} 本书")

        if need_refresh:
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

                # 使用增强版方法获取完整书架数据
                print("📚 使用增强版方法获取书架数据（包括rawBooks和rawIndexes）")
                user_data = weread_api.get_user_data_enhanced(current_user.wr_vid)

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

                # 检查是否是cookie过期
                if user_data.get('error') == 'cookie_expired':
                    print("🔐 检测到Cookie过期，需要重新登录")
                    return APIResponse(
                        success=False,
                        message="登录已过期，请重新登录",
                        data={
                            "error": "cookie_expired",
                            "need_login": True,
                            "redirect_to": "/login"
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
            # 使用缓存的数据
            user_data = user_books.books_data
            print(f"📚 使用缓存书架数据: {len(user_data.get('books', []))} 本书")

        # Get books list
        all_books_data = user_data.get('books', [])

        # 根据加载模式处理书籍
        if mode == "rawbooks":
            # rawbooks模式：优先显示有完整信息的书籍，但仍包含所有书籍以保证分页正确
            books_data = all_books_data
            print(f"📖 rawbooks模式: 总共 {len(books_data)} 本书籍（优先显示完整信息）")
        else:
            # 返回所有书籍
            books_data = all_books_data
            print(f"📚 完整模式: 返回 {len(books_data)} 本书籍")

        # 根据筛选条件过滤书籍
        if filter == "read":
            books_data = [book for book in books_data if book.get('finishReading') == 1]
            print(f"📖 筛选已读书籍: {len(books_data)} 本")
        elif filter == "unread":
            books_data = [book for book in books_data if book.get('finishReading') == 0]
            print(f"📚 筛选未读书籍: {len(books_data)} 本")
        else:
            print(f"📋 显示全部书籍: {len(books_data)} 本")

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
            # 验证bookId有效性
            book_id = book.get('bookId', '')
            if (not book_id or
                not isinstance(book_id, str) or
                book_id.strip() == '' or
                book_id in ['undefined', 'null', 'None']):
                print(f"⚠️ 跳过无效的bookId: {book_id}")
                continue

            try:
                # 优先检查原始数据是否包含足够的信息
                has_sufficient_data = (
                    book.get('title') and 
                    book.get('title') != '未知书籍' and
                    book.get('author') and
                    book.get('author') != '未知作者'
                )
                
                if has_sufficient_data:
                    # 直接使用原始数据，避免额外的API调用
                    print(f"📖 使用缓存数据: {book['bookId']} - {book.get('title', '')}")
                    book_info = book
                else:
                    # 检查数据库缓存
                    cached_book = db.query(BookCache).filter(BookCache.book_id == book['bookId']).first()

                    if cached_book:
                        print(f"💾 使用数据库缓存: {book['bookId']}")
                        book_info = cached_book.book_info
                    else:
                        # 仅在必要时才调用API获取详细信息
                        print(f"🌐 通过API获取详细信息: {book['bookId']}")
                        book_info = weread_api.get_book_info(book['bookId'])
                        
                        # 只缓存成功获取的数据
                        if not book_info.get('error'):
                            cache_entry = BookCache(book_id=book['bookId'], book_info=book_info)
                            db.add(cache_entry)
                            db.commit()

                # 处理评分信息的不同格式
                rating_detail = book_info.get('newRatingDetail', '')

                # 定义评分映射，确保与前端getRatingImage函数一致
                valid_ratings = ['神作', '好评如潮', '脍炙人口', '值得一读', '褒贬不一', '不值一读']

                if isinstance(rating_detail, dict):
                    rating_title = rating_detail.get('title', '')
                    # 保留有效的评分标题，无效的设为空
                    if rating_title and rating_title not in valid_ratings:
                        print(f"⚠️ 无效评分标题: '{rating_title}' (书籍: {book.get('title', '')})")
                        rating_title = ''
                    else:
                        print(f"✅ 有效评分标题: '{rating_title}' (书籍: {book.get('title', '')})")
                elif isinstance(rating_detail, str):
                    # 确保评分标题有效
                    if rating_detail in valid_ratings:
                        rating_title = rating_detail
                        print(f"✅ 字符串评分标题: '{rating_title}' (书籍: {book.get('title', '')})")
                    else:
                        print(f"⚠️ 无效字符串评分: '{rating_detail}' (书籍: {book.get('title', '')})")
                        rating_title = ''
                else:
                    rating_title = ''

                detailed_books.append({
                    'bookId': book['bookId'],
                    'title': book_info.get('title', book.get('title', '')),
                    'author': book_info.get('author', book.get('author', '')),
                    'cover': book_info.get('cover', book.get('cover', '')).replace('s_', 't7_'),
                    'finishReading': book_info.get('finishReading', book.get('finishReading', 0)),
                    'category': book_info.get('category', book.get('category', '')),
                    'newRatingDetail': rating_title,
                    'readUpdateTime': book.get('readUpdateTime', 0),
                    'source': book_info.get('source', 'unknown')  # 添加数据来源标识
                })

            except Exception as e:
                print(f"⚠️ 处理书籍信息出错 {book['bookId']}: {e}")
                # 使用原始数据作为备选
                detailed_books.append({
                    'bookId': book['bookId'],
                    'title': book.get('title', '书籍信息不可用'),
                    'author': book.get('author', '未知'),
                    'cover': book.get('cover', '').replace('s_', 't7_') if book.get('cover') else '',
                    'finishReading': book.get('finishReading', 0),
                    'category': book.get('category', ''),
                    'newRatingDetail': '',
                    'readUpdateTime': book.get('readUpdateTime', 0),
                    'source': 'fallback'
                })

        # 计算加载状态信息
        total_all_books = len(all_books_data)
        rawbooks_count = len([book for book in all_books_data if not book.get('needsDetailFetch', False)])
        synced_books_count = total_all_books - rawbooks_count

        return APIResponse(
            success=True,
            message="Books retrieved successfully",
            data={
                "books": detailed_books,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "loading_info": {
                    "mode": mode,
                    "total_all_books": total_all_books,
                    "rawbooks_count": rawbooks_count,
                    "synced_books_count": synced_books_count,
                    "has_more_to_sync": False  # 现在已经包含所有书籍，无需再同步
                }
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
        print(f"📚 API调用 /books/{book_id} - 用户: {current_user.wr_name}")
        print(f"   📋 bookId类型: {type(book_id)}, 长度: {len(book_id)}, 内容: '{book_id}'")

        # 验证bookId
        if (not book_id or
            not isinstance(book_id, str) or
            book_id.strip() == '' or
            book_id in ['undefined', 'null', 'None']):
            print(f"❌ 无效的bookId参数: {book_id}")
            return APIResponse(
                success=False,
                message="无效的书籍ID",
                data={
                    "error": "INVALID_BOOK_ID",
                    "bookId": book_id
                }
            )

        book_id = book_id.strip()
        print(f"✅ bookId验证通过，开始获取详情: {book_id}")

        # 不使用缓存，每次都获取最新数据
        print(f"🔄 获取最新书籍详情: {book_id}")

        # 清除可能存在的旧缓存
        cached_book = db.query(BookCache).filter(BookCache.book_id == book_id).first()
        if cached_book:
            print(f"🗑️ 清除旧缓存: {book_id}")
            db.delete(cached_book)
            db.commit()

        # 直接从API获取最新数据
        cookies = get_user_cookies(current_user)
        weread_api = WeReadAPI(cookies)
        book_info = weread_api.get_book_info(book_id)

        # 检查是否是认证错误
        if book_info.get('error') == '认证失败' or book_info.get('title') == '需要重新登录获取':
            print(f"🔐 书籍详情获取失败，认证错误: {book_id}")
            return APIResponse(
                success=False,
                message="获取书籍详情失败，登录已过期",
                data={
                    "error": "LOGIN_EXPIRED",
                    "requires_login": True,
                    "bookId": book_id
                }
            )

        # 检查是否是未知书籍错误
        if book_info.get('title') in ['未知书籍', '书籍信息不可用'] or book_info.get('error') == 'html_response':
            print(f"📖 检测到未知书籍: {book_id}")
            return APIResponse(
                success=False,
                message="未知书籍信息，请检查cookie是否有效或重新登录",
                data={
                    "error": "UNKNOWN_BOOK",
                    "requires_login": True,
                    "bookId": book_id,
                    "title": "未知书籍"
                }
            )

        # 检查是否是其他严重错误（只对明确的错误状态进行拦截）
        if book_info.get('error') in ['获取失败', 'API调用失败'] and book_info.get('title') in ['书籍信息暂时不可用']:
            print(f"⚠️ 书籍详情严重错误: {book_id}")
            return APIResponse(
                success=False,
                message="书籍详情暂时不可用，请稍后重试",
                data={
                    "error": "BOOK_INFO_UNAVAILABLE",
                    "bookId": book_id,
                    "retry": True
                }
            )

        # 处理评分信息
        new_rating_detail = book_info.get('newRatingDetail', {})
        if isinstance(new_rating_detail, dict):
            rating_title = new_rating_detail.get('title', '')
        else:
            rating_title = str(new_rating_detail) if new_rating_detail else ''

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
                "newRatingDetail": rating_title
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

        # 使用增强版方法获取完整书架数据
        print("🔄 刷新书架：使用增强版方法获取数据（包括rawBooks和rawIndexes）")
        user_data = weread_api.get_user_data_enhanced(current_user.wr_vid)

        # 检查是否是cookie过期
        if user_data.get('error') == 'cookie_expired':
            print("🔐 刷新时检测到Cookie过期，需要重新登录")
            return APIResponse(
                success=False,
                message="登录已过期，请重新登录",
                data={
                    "error": "cookie_expired",
                    "need_login": True,
                    "redirect_to": "/login"
                }
            )

        # Update cached data
        user_books = db.query(UserBooks).filter(UserBooks.user_id == current_user.id).first()
        if user_books:
            user_books.books_data = user_data
        else:
            user_books = UserBooks(user_id=current_user.id, books_data=user_data)
            db.add(user_books)

        db.commit()

        # 显示详细的刷新信息
        source = user_data.get('source', 'unknown')
        html_count = user_data.get('html_book_count', 0)
        synced_count = user_data.get('synced_book_count', 0)
        total_count = len(user_data.get('books', []))

        print(f"✅ 书架刷新完成:")
        print(f"   📋 数据源: {source}")
        print(f"   📖 HTML解析: {html_count} 本")
        print(f"   🔄 syncBook同步: {synced_count} 本")
        print(f"   📚 总计: {total_count} 本书")

        return APIResponse(
            success=True,
            message=f"书架刷新成功，共获取 {total_count} 本书籍",
            data={
                "total_books": total_count,
                "source": source,
                "html_book_count": html_count,
                "synced_book_count": synced_count
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh books: {str(e)}")

@router.post("/test-html-parsing", response_model=APIResponse)
async def test_html_parsing(
    html_file_path: str = Query("response.html"),
    current_user: User = Depends(get_current_user)
):
    """
    测试HTML解析功能 - 从指定的HTML文件中解析书籍信息
    """
    try:
        import os
        from weread_api import WeReadAPI
        
        # 构建完整的文件路径
        if not os.path.isabs(html_file_path):
            # 如果是相对路径，从项目根目录开始
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            html_file_path = os.path.join(project_root, html_file_path)
        
        # 检查文件是否存在
        if not os.path.exists(html_file_path):
            raise HTTPException(
                status_code=404,
                detail=f"HTML文件不存在: {html_file_path}"
            )
        
        # 读取HTML文件内容
        try:
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"读取HTML文件失败: {str(e)}"
            )
        
        # 创建WeReadAPI实例进行测试（使用空cookie）
        weread_api = WeReadAPI("")
        
        # 使用新的HTML解析方法
        books = weread_api._extract_books_from_html(html_content, current_user.wr_vid)
        
        # 统计信息
        total_books = len(books)
        books_with_details = sum(1 for book in books if book.get('title') != '未知书籍')
        
        # 按数据来源分组统计
        source_stats = {}
        for book in books:
            source = book.get('source', 'unknown')
            source_stats[source] = source_stats.get(source, 0) + 1
        
        return APIResponse(
            success=True,
            message=f"HTML解析测试完成，共提取到 {total_books} 本书籍",
            data={
                "total_books": total_books,
                "books_with_details": books_with_details,
                "source_statistics": source_stats,
                "books": books[:20],  # 只返回前20本书作为示例
                "html_file_path": html_file_path,
                "html_file_size": len(html_content),
                "test_info": {
                    "user_vid": current_user.wr_vid,
                    "parsing_method": "从window.__INITIAL_STATE__解析完整书籍数据",
                    "data_sources": list(source_stats.keys())
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"HTML解析测试失败: {str(e)}"
        )