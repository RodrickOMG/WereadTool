#!/usr/bin/env python3
"""
创建 book_note_sync 表的迁移脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import engine, Base
from models import BookNoteSync

def create_note_sync_table():
    """创建笔记同步表"""
    try:
        # 创建表
        BookNoteSync.__table__.create(engine, checkfirst=True)
        print("✅ book_note_sync 表创建成功")
    except Exception as e:
        print(f"❌ 创建表失败: {e}")

if __name__ == "__main__":
    create_note_sync_table()