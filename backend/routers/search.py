from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
import math

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db
from models import User, UserBooks
from schemas import SearchResponse, APIResponse
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
async def search_books(
    q: str = Query(..., description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search books in user's library"""
    try:
        # Get user books data
        user_books = db.query(UserBooks).filter(UserBooks.user_id == current_user.id).first()

        if not user_books or not user_books.books_data:
            # If no cached data, fetch from WeRead API
            cookies = get_user_cookies(current_user)
            weread_api = WeReadAPI(cookies)
            user_data = weread_api.get_user_data(current_user.wr_vid)

            # Save to cache
            if user_books:
                user_books.books_data = user_data
            else:
                user_books = UserBooks(user_id=current_user.id, books_data=user_data)
                db.add(user_books)
            db.commit()
        else:
            user_data = user_books.books_data

        # Perform search
        cookies = get_user_cookies(current_user)
        weread_api = WeReadAPI(cookies)
        search_results = weread_api.search_books(user_data, q)

        # Calculate pagination
        total = len(search_results)
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        # Get page data
        page_results = search_results[start_idx:end_idx]

        return APIResponse(
            success=True,
            message=f"Found {total} books matching '{q}'",
            data={
                "results": page_results,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "query": q
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("suggestions", response_model=APIResponse)
async def get_search_suggestions(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(5, ge=1, le=10),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get search suggestions based on user's library"""
    try:
        # Get user books data
        user_books = db.query(UserBooks).filter(UserBooks.user_id == current_user.id).first()

        if not user_books or not user_books.books_data:
            return APIResponse(
                success=True,
                message="No suggestions available",
                data={"suggestions": []}
            )

        user_data = user_books.books_data
        books = user_data.get('books', [])

        # Simple suggestion logic - find books with titles containing the query
        suggestions = []
        query_lower = q.lower()

        for book in books:
            title = book.get('title', '').lower()
            author = book.get('author', '').lower()

            if query_lower in title or query_lower in author:
                suggestions.append({
                    "bookId": book.get('bookId'),
                    "title": book.get('title'),
                    "author": book.get('author')
                })

                if len(suggestions) >= limit:
                    break

        return APIResponse(
            success=True,
            message="Suggestions retrieved",
            data={"suggestions": suggestions}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")