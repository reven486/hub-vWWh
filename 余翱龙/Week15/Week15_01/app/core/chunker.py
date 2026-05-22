import uuid
from typing import List, Tuple
from dataclasses import dataclass
from app.config import settings


@dataclass
class Chunk:
    chunk_id: str
    chunk_type: str  # text, image_caption
    content: str
    page: int
    vector_id: int = -1


class TextChunker:
    """文本内容切分器"""

    def __init__(self, max_chars: int = None, overlap: int = None):
        self.max_chars = max_chars or settings.CHUNK_MAX_CHARS
        self.overlap = overlap or settings.CHUNK_OVERLAP

    def chunk(self, text: str, page: int = 0) -> List[Chunk]:
        """
        将长文本切分成小块

        Args:
            text: 输入文本
            page: 页码

        Returns:
            List[Chunk]: 切分后的文本块
        """
        if not text.strip():
            return []

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.max_chars
            chunk_text = text[start:end]

            chunks.append(Chunk(
                chunk_id=str(uuid.uuid4()),
                chunk_type="text",
                content=chunk_text.strip(),
                page=page,
                vector_id=-1
            ))

            start += self.max_chars - self.overlap

        return chunks


class ImageChunker:
    """图像组织器 - 为图像生成描述块"""

    def __init__(self):
        pass

    def chunk(self, image_path: str, caption: str, page: int) -> List[Chunk]:
        """
        创建图像的chunk

        Args:
            image_path: 图像路径
            caption: 图像描述
            page: 页码

        Returns:
            List[Chunk]: 包含图像路径和描述的chunk
        """
        if not caption:
            caption = f"Image at page {page}"

        return [Chunk(
            chunk_id=str(uuid.uuid4()),
            chunk_type="image_caption",
            content=f"[IMAGE]{image_path}[/IMAGE]\n{caption}",
            page=page,
            vector_id=-1
        )]


class DocumentChunker:
    """文档切分协调器"""

    def __init__(self):
        self.text_chunker = TextChunker()
        self.image_chunker = ImageChunker()

    def chunk_document(self, markdown: str, images: List, page_start: int = 0) -> List[Chunk]:
        """
        将文档内容切分成chunks

        Args:
            markdown: 文档markdown内容
            images: 图像信息列表
            page_start: 起始页码

        Returns:
            List[Chunk]: 所有chunks
        """
        chunks = []

        # 按页面分割markdown
        pages = markdown.split("---PAGE BREAK---")

        for page_idx, page_text in enumerate(pages):
            page_num = page_start + page_idx
            page_chunks = self.text_chunker.chunk(page_text, page_num)
            chunks.extend(page_chunks)

        # 处理图像chunks
        for img in images:
            img_chunks = self.image_chunker.chunk(img.image_path, img.caption, img.page)
            chunks.extend(img_chunks)

        return chunks


def create_chunker() -> DocumentChunker:
    return DocumentChunker()