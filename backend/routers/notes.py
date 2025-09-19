from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
import markdown2

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db
from models import User
from schemas import NoteResponse, APIResponse
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

@router.get("/{book_id}", response_model=APIResponse)
async def get_book_notes(
    book_id: str,
    option: int = Query(1, description="1: all chapters, 2: only chapters with notes"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get book notes/highlights in markdown format"""
    try:
        cookies = get_user_cookies(current_user)
        weread_api = WeReadAPI(cookies)

        # Get book title
        book_info = weread_api.get_book_info(book_id)
        book_title = book_info.get('title', 'Unknown Book')

        # Get markdown content
        markdown_content = weread_api.get_markdown_content(book_id, option)

        if not markdown_content or markdown_content.strip() == '\n':
            return APIResponse(
                success=False,
                message="No notes found for this book",
                data=None
            )

        # Convert to HTML
        html_content = markdown2.markdown(markdown_content)

        return APIResponse(
            success=True,
            message="Notes retrieved successfully",
            data={
                "book_id": book_id,
                "book_title": book_title,
                "markdown_content": markdown_content,
                "html_content": html_content
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get notes: {str(e)}")

@router.get("/{book_id}/chapters", response_model=APIResponse)
async def get_book_chapters(
    book_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get book chapters information"""
    try:
        cookies = get_user_cookies(current_user)
        weread_api = WeReadAPI(cookies)

        chapters = weread_api.get_sorted_chapters(book_id)

        chapter_list = []
        for chapter in chapters:
            chapter_list.append({
                "chapterUid": chapter[0],
                "level": chapter[1],
                "title": chapter[2]
            })

        return APIResponse(
            success=True,
            message="Chapters retrieved successfully",
            data={"chapters": chapter_list}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chapters: {str(e)}")

@router.get("/{book_id}/export", response_model=APIResponse)
async def export_notes(
    book_id: str,
    format: str = Query("markdown", description="Export format: markdown or html"),
    option: int = Query(1, description="1: all chapters, 2: only chapters with notes"),
    current_user: User = Depends(get_current_user)
):
    """Export book notes in specified format"""
    try:
        cookies = get_user_cookies(current_user)
        weread_api = WeReadAPI(cookies)

        # Get book info
        book_info = weread_api.get_book_info(book_id)
        book_title = book_info.get('title', 'Unknown Book')

        # Get markdown content
        markdown_content = weread_api.get_markdown_content(book_id, option)

        if not markdown_content or markdown_content.strip() == '\n':
            return APIResponse(
                success=False,
                message="No notes found for this book",
                data=None
            )

        if format.lower() == "html":
            # Convert to HTML with title
            full_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>《{book_title}》笔记</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.1.0/github-markdown.min.css"/>
    <style>
        .markdown-body {{
            box-sizing: border-box;
            min-width: 200px;
            max-width: 980px;
            margin: 0 auto;
            padding: 45px;
        }}
        @media(max-width:767px) {{
            .markdown-body {{
                padding: 15px;
            }}
        }}
    </style>
</head>
<body class="markdown-body">
    <h1>《{book_title}》笔记</h1>
    {markdown2.markdown(markdown_content)}
</body>
</html>"""
            return APIResponse(
                success=True,
                message="Notes exported as HTML",
                data={
                    "content": full_html,
                    "filename": f"{book_title}_notes.html",
                    "format": "html"
                }
            )
        else:
            # Return markdown with title
            full_markdown = f"# 《{book_title}》笔记\n\n{markdown_content}"
            return APIResponse(
                success=True,
                message="Notes exported as Markdown",
                data={
                    "content": full_markdown,
                    "filename": f"{book_title}_notes.md",
                    "format": "markdown"
                }
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export notes: {str(e)}")