from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class KnowledgeBaseCreate(BaseModel):
    name: str
    description: str = ""


class KnowledgeBaseResponse(BaseModel):
    id: int
    name: str
    description: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentResponse(BaseModel):
    id: int
    knowledge_base_id: int
    filename: str
    file_size: int
    page_count: int
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    knowledge_base_id: int
    question: str
    top_k: int = 5


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict] = []


class SourceInfo(BaseModel):
    document_id: int
    filename: str
    page_number: int
    chunk_index: int
    content: str
    score: float
