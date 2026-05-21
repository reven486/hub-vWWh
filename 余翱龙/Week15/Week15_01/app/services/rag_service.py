from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.database import Document
from app.models.schemas import ChatRequest, ChatResponse, SourceInfo, RetrieveRequest, RetrieveResponse
from app.core.retriever import get_retriever, RetrievalResult
from app.core.generator import get_generator


class RAGService:
    """RAG流程服务"""

    def __init__(self, db: Session):
        self.db = db
        self.retriever = get_retriever()
        self.generator = get_generator()

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """
        执行RAG问答

        Args:
            request: 问答请求

        Returns:
            ChatResponse: 问答响应
        """
        # 1. 检索相关上下文
        retrieval_results = await self.retriever.retrieve(
            query=request.query,
            doc_ids=request.doc_ids,
            top_k=request.top_k
        )

        # 2. 生成答案
        answer = await self.generator.generate(
            query=request.query,
            contexts=retrieval_results
        )

        # 3. 构建响应
        sources = []
        for result in retrieval_results:
            # 获取文档名
            doc = self.db.query(Document).filter(Document.doc_id == result.doc_id).first()
            doc_name = doc.doc_name if doc else "unknown"

            sources.append(SourceInfo(
                chunk_id=result.chunk_id,
                type=result.chunk_type,
                doc_name=doc_name,
                page=result.page,
                content=result.content[:200] if result.chunk_type == "text" else None,
                image_path=result.image_path if result.chunk_type == "image" else None
            ))

        return ChatResponse(
            answer=answer,
            sources=sources,
            model_used="qwen3-vl-32b"
        )

    async def retrieve(self, request: RetrieveRequest) -> RetrieveResponse:
        """
        执行纯检索

        Args:
            request: 检索请求

        Returns:
            RetrieveResponse: 检索响应
        """
        results = await self.retriever.retrieve(
            query=request.query,
            doc_ids=request.doc_ids,
            top_k=request.top_k
        )

        sources = []
        for result in results:
            doc = self.db.query(Document).filter(Document.doc_id == result.doc_id).first()
            doc_name = doc.doc_name if doc else "unknown"

            sources.append(SourceInfo(
                chunk_id=result.chunk_id,
                type=result.chunk_type,
                doc_name=doc_name,
                page=result.page,
                content=result.content[:200] if result.chunk_type == "text" else None,
                image_path=result.image_path if result.chunk_type == "image" else None
            ))

        return RetrieveResponse(results=sources)


def get_rag_service(db: Session) -> RAGService:
    return RAGService(db)