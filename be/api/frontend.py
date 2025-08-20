from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from fe.html import HTML_TEMPLATE

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def get_frontend():
    """프론트엔드 HTML 페이지 반환"""
    return HTMLResponse(content=HTML_TEMPLATE)
