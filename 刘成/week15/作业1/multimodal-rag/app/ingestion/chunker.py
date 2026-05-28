import uuid
from typing import list
from app.models.document import Chunk, ChunkType
from app.config import settings


class Chunker:
    """Split text into semantic chunks and handle images as independent chunks"""

    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

    def chunk_text(self, text: str, document_id: str, source_file: str, page: int = None) -> list[Chunk]:
        """Split text into overlapping chunks by character count"""
        chunks = []
        chunk_index = 0

        if not text or not text.strip():
            return chunks

        # Simple character-based chunking with overlap
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + self.chunk_size

            # Try to break at sentence/paragraph boundary
            if end < text_length:
                # Look for sentence-ending punctuation
                for sep in ['。', '！', '？', '.', '!', '?', '\n\n']:
                    last_sep = text.rfind(sep, start, end)
                    if last_sep > start:
                        end = last_sep + 1
                        break

            chunk_text = text[start:end].strip()
            if chunk_text:
                chunk = Chunk(
                    id=str(uuid.uuid4()),
                    document_id=document_id,
                    chunk_type=ChunkType.TEXT,
                    chunk_index=chunk_index,
                    content=chunk_text,
                    source_file=source_file,
                    page=page,
                )
                chunks.append(chunk)
                chunk_index += 1

            # Move start with overlap
            start = end - self.chunk_overlap
            if start >= text_length - self.chunk_overlap:
                break

        return chunks

    def chunk_image(
        self,
        document_id: str,
        source_file: str,
        base64_data: str,
        mime_type: str,
        original_width: int = None,
        original_height: int = None,
    ) -> Chunk:
        """Create a single chunk for an image"""
        return Chunk(
            id=str(uuid.uuid4()),
            document_id=document_id,
            chunk_type=ChunkType.IMAGE,
            chunk_index=0,
            content=base64_data,
            source_file=source_file,
            mime_type=mime_type,
            original_width=original_width,
            original_height=original_height,
        )


chunker = Chunker()
