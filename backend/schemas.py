from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Auth schemas
class WeReadLogin(BaseModel):
    wr_gid: str
    wr_vid: str
    wr_skey: str
    wr_rt: str
    wr_name: Optional[str] = ""
    wr_avatar: Optional[str] = ""
    wr_localvid: Optional[str] = ""
    wr_gender: Optional[str] = ""
    wr_pf: Optional[str] = "0"

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None

class User(BaseModel):
    id: int
    wr_vid: str
    wr_name: str
    wr_avatar: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class QrLoginResponse(BaseModel):
    session_id: str
    qr_code_url: str
    expires_at: datetime

class QrLoginStatusResponse(BaseModel):
    status: str  # waiting, scanned, confirmed, expired
    message: str
    access_token: Optional[str] = None
    user: Optional[Dict[str, Any]] = None

# Book schemas
class BookInfo(BaseModel):
    bookId: str
    title: str
    author: str
    cover: str
    finishReading: int
    category: str
    newRatingDetail: str
    readUpdateTime: int

class BookDetail(BaseModel):
    bookId: str
    title: str
    author: str
    cover: str
    intro: str
    publisher: Optional[str] = None
    category: Optional[str] = None
    newRatingDetail: Optional[str] = None

class BooksResponse(BaseModel):
    books: List[BookInfo]
    total: int
    page: int
    page_size: int
    total_pages: int

# Search schemas
class SearchRequest(BaseModel):
    query: str
    page: int = 1
    page_size: int = 10

class SearchResult(BaseModel):
    bookId: str
    title: str
    author: str
    cover: str
    ratio: int

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int
    page: int
    page_size: int

# Notes schemas
class NoteRequest(BaseModel):
    book_id: str
    option: int = 1  # 1: all chapters, 2: only chapters with notes

class NoteResponse(BaseModel):
    book_id: str
    book_title: str
    markdown_content: str
    html_content: str

class ChapterInfo(BaseModel):
    chapterUid: int
    level: int
    title: str

# API Response wrapper
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None