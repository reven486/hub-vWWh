from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class ChunkType(str, Enum):
    TEXT = "text"
    IMAGE = "image"


class DocStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentBase(BaseModel):
    source_file: str
    doc_type: str
    file_size: Optional[int] = None


class DocumentCreate(DocumentBase):
    pass


class DocumentResponse(DocumentBase):
    id: str
    file_path: str
    uploaded_at: datetime
    chunk_count: int = 0
    status: DocStatus = DocStatus.PROCESSING

    class Config:
        from_attributes = True


class ChunkBase(BaseModel):
    chunk_type: ChunkType
    chunk_index: int
    content_text: Optional[str] = None


class ChunkResponse(ChunkBase):
    id: str
    document_id: str
    page: Optional[int] = None

    class Config:
        from_attributes = True


class IndexResponse(BaseModel):
    document_id: str
    qdrant_points_count: int
    last_indexed_at: Optional[datetime] = None


class IngestRequest(BaseModel):
    collection_name: Optional[str] = None


class IngestResponse(BaseModel):
    document_id: str
    chunk_count: int
    status: DocStatus


class QueryRequest(BaseModel):
    query_text: Optional[str] = None
    query_image: Optional[str] = None  # base64 encoded image
    top_k: Optional[int] = 5


class RetrievedChunk(BaseModel):
    chunk_id: str
    document_id: str
    chunk_type: ChunkType
    content: str
    score: float
    source_file: str
    page: Optional[int] = None


class QueryResponse(BaseModel):
    answer: str
    retrieved_chunks: list[RetrievedChunk]
    has_image_query: bool = False


class CollectionStats(BaseModel):
    collection_name: str
    points_count: int
    vectors_count: int


class HealthStatus(BaseModel):
    status: str
    qdrant: bool
    dashscope: bool
