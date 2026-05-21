import pytest
from app.core.chunker import TextChunker, ImageChunker, DocumentChunker, Chunk as ChunkData


def test_text_chunker():
    """测试文本切分"""
    chunker = TextChunker(max_chars=100, overlap=10)

    text = "A" * 250
    chunks = chunker.chunk(text, page=1)

    assert len(chunks) == 3
    assert all(c.chunk_type == "text" for c in chunks)
    assert chunks[0].page == 1


def test_text_chunker_short_text():
    """测试短文本切分"""
    chunker = TextChunker(max_chars=100, overlap=10)

    text = "Short text"
    chunks = chunker.chunk(text, page=1)

    assert len(chunks) == 1
    assert chunks[0].content == "Short text"


def test_image_chunker():
    """测试图像切分"""
    chunker = ImageChunker()

    chunks = chunker.chunk("/path/to/image.png", "Image caption", page=1)

    assert len(chunks) == 1
    assert chunks[0].chunk_type == "image_caption"
    assert "image.png" in chunks[0].content


def test_document_chunker():
    """测试文档切分"""
    chunker = DocumentChunker()

    markdown = "Page 1 content\n---PAGE BREAK---\nPage 2 content"
    images = []

    chunks = chunker.chunk_document(markdown, images, page_start=1)

    assert len(chunks) == 2
    assert all(c.page in [1, 2] for c in chunks)