from pydantic import BaseModel, Field
from typing import Literal


class UploadDocumentResponse(BaseModel):
    doc_id: str
    filename: str
    kb_id: str
    status: str = "pending"
    message: str = "Document uploaded and queued for parsing"


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="User question")
    kb_id: str = Field(..., description="Knowledge base ID")
    top_k_text: int = Field(5, ge=1, le=20, description="Number of text chunks to retrieve")
    top_k_image: int = Field(3, ge=1, le=10, description="Number of image chunks to retrieve")


class SourceInfo(BaseModel):
    doc_id: str
    filename: str | None = None
    page_num: int | None = None
    chunk_type: Literal["text", "image"]
    source_label: str | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceInfo] = []


class DocumentStatus(BaseModel):
    doc_id: str
    filename: str
    kb_id: str
    status: str
