from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class DocumentUploadResponse(BaseModel):
    doc_id: str
    doc_name: str
    status: str
    message: str


class DocumentInfo(BaseModel):
    doc_id: str
    doc_name: str
    status: str
    created_at: datetime
    chunk_count: int
    image_count: int


class ChunkInfo(BaseModel):
    chunk_id: str
    chunk_type: str
    content: str
    page: Optional[int] = None


class SourceInfo(BaseModel):
    chunk_id: str
    type: str  # text, image
    doc_name: str
    page: Optional[int] = None
    content: Optional[str] = None
    image_path: Optional[str] = None


class ChatRequest(BaseModel):
    query: str
    doc_ids: Optional[List[str]] = None
    top_k: int = 4


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceInfo]
    model_used: str = "qwen-vl-max"


class RetrieveRequest(BaseModel):
    query: str
    doc_ids: Optional[List[str]] = None
    top_k: int = 4


class RetrieveResponse(BaseModel):
    results: List[SourceInfo]