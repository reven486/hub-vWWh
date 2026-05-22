from typing import List, Optional
from pydantic import BaseModel, Field


class DocumentUploadRequest(BaseModel):
    knowledge_base_id: str = Field(..., description="Knowledge base ID")
    file_name: str = Field(..., description="File name")
    file_path: str = Field(..., description="File path")


class DocumentUploadResponse(BaseModel):
    document_id: str
    file_name: str
    status: str


class ChatRequest(BaseModel):
    knowledge_base_id: str = Field(..., description="Knowledge base ID")
    query: str = Field(..., description="User query")
    top_k: int = Field(default=5, description="Number of results to retrieve")


class SourceInfo(BaseModel):
    pdf_name: str
    page: Optional[int] = None
    chart_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceInfo]


class Document(BaseModel):
    id: str
    file_name: str
    file_path: str
    status: str
    knowledge_base_id: str


class TextChunk(BaseModel):
    id: str
    document_id: str
    content: str
    page: int
    chunk_index: int


class ImageChunk(BaseModel):
    id: str
    document_id: str
    image_path: str
    page: int
    chart_id: Optional[str] = None
