from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.schemas import ChatRequest, ChatResponse, RetrieveRequest, RetrieveResponse
from app.services.rag_service import get_rag_service

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    多模态问答接口

    支持图文混合检索和基于Qwen-VL的答案生成。
    返回答案及信息来源。
    """
    service = get_rag_service(db)
    return await service.chat(request)


@router.post("/retrieve", response_model=RetrieveResponse)
async def retrieve(
    request: RetrieveRequest,
    db: Session = Depends(get_db)
):
    """
    纯检索接口

    返回检索到的上下文，不生成答案。
    """
    service = get_rag_service(db)
    return await service.retrieve(request)