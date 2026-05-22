from dataclasses import dataclass, field
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


@dataclass
class Document:
    id: str
    source_file: str
    doc_type: str
    file_path: str
    file_size: Optional[int] = None
    uploaded_at: datetime = field(default_factory=datetime.now)
    chunk_count: int = 0
    status: DocStatus = DocStatus.PROCESSING


@dataclass
class TextChunk:
    id: str
    document_id: str
    chunk_index: int
    content: str
    page: Optional[int] = None


@dataclass
class ImageChunk:
    id: str
    document_id: str
    chunk_index: int
    base64_data: str
    mime_type: str
    width: Optional[int] = None
    height: Optional[int] = None
    original_width: Optional[int] = None
    original_height: Optional[int] = None


@dataclass
class Chunk:
    """Unified chunk representation for both text and image"""
    id: str
    document_id: str
    chunk_type: ChunkType
    chunk_index: int
    content: str  # text content or base64 data
    source_file: str
    page: Optional[int] = None
    mime_type: Optional[str] = None
    original_width: Optional[int] = None
    original_height: Optional[int] = None

    def to_payload(self) -> dict:
        payload = {
            "chunk_id": self.id,
            "document_id": self.document_id,
            "chunk_type": self.chunk_type.value,
            "content": self.content,
            "source_file": self.source_file,
            "chunk_index": self.chunk_index,
        }
        if self.page is not None:
            payload["page"] = self.page
        if self.mime_type is not None:
            payload["mime_type"] = self.mime_type
        if self.original_width is not None:
            payload["original_width"] = self.original_width
        if self.original_height is not None:
            payload["original_height"] = self.original_height
        return payload
