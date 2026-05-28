from fastapi import APIRouter
from app.api import document, chat

api_router = APIRouter()

# 文档管理路由
api_router.include_router(
    document.router,
    prefix="",
    tags=["documents"]
)

# 问答路由
api_router.include_router(
    chat.router,
    prefix="",
    tags=["chat"]
)