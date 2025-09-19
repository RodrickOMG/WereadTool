from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    wr_vid = Column(String, unique=True, index=True)
    wr_gid = Column(String)
    wr_skey = Column(String)
    wr_rt = Column(String)
    wr_localvid = Column(String, default="")
    wr_name = Column(String, default="")
    wr_avatar = Column(String, default="")
    wr_gender = Column(String, default="")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class UserBooks(Base):
    __tablename__ = "user_books"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    books_data = Column(JSON)  # Store the full books JSON data
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class BookCache(Base):
    __tablename__ = "book_cache"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(String, unique=True, index=True)
    book_info = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
