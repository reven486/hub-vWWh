import pytest
from pathlib import Path
import tempfile
import os

from app.knowledge_base.manager import KnowledgeBaseManager
from app.knowledge_base.document_store import DocumentStore
from app.ingestion.text_processor import TextProcessor
from app.ingestion.image_processor import ImageProcessor
from app.ingestion.chunker import Chunker


@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    yield db_path
    os.unlink(db_path)


@pytest.fixture
def kb_manager(temp_db):
    return KnowledgeBaseManager(db_path=temp_db)


def test_kb_add_document(kb_manager):
    doc_id = kb_manager.add_document(
        source_file="test.pdf",
        doc_type="pdf",
        file_path="/path/to/test.pdf",
        file_size=1024,
    )
    assert doc_id is not None

    doc = kb_manager.get_document(doc_id)
    assert doc is not None
    assert doc.source_file == "test.pdf"
    assert doc.doc_type == "pdf"


def test_kb_list_documents(kb_manager):
    kb_manager.add_document("doc1.pdf", "pdf", "/path/doc1.pdf")
    kb_manager.add_document("doc2.txt", "txt", "/path/doc2.txt")

    docs = kb_manager.list_documents()
    assert len(docs) == 2


def test_kb_delete_document(kb_manager):
    doc_id = kb_manager.add_document("test.pdf", "pdf", "/path/test.pdf")
    kb_manager.delete_document(doc_id)

    doc = kb_manager.get_document(doc_id)
    assert doc is None


def test_kb_add_chunk(kb_manager):
    doc_id = kb_manager.add_document("test.pdf", "pdf", "/path/test.pdf")
    chunk_id = kb_manager.add_chunk(
        doc_id=doc_id,
        chunk_type="text",
        chunk_index=0,
        content_text="This is test content",
        page=1,
    )
    assert chunk_id is not None

    chunks = kb_manager.get_chunks_by_document(doc_id)
    assert len(chunks) == 1
    assert chunks[0].content_text == "This is test content"


def test_text_processor():
    processor = TextProcessor()

    # Create temp txt file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("This is a test document.\nWith multiple lines.")
        temp_path = Path(f.name)

    try:
        result = processor.extract_from_txt(temp_path)
        assert len(result) == 1
        assert "test document" in result[0]["text"]
    finally:
        os.unlink(temp_path)


def test_chunker():
    chunker = Chunker(chunk_size=50, chunk_overlap=10)
    text = "This is a test document. " * 10

    chunks = chunker.chunk_text(
        text=text,
        document_id="test-doc",
        source_file="test.txt",
    )

    assert len(chunks) > 1
    assert all(c.chunk_type.value == "text" for c in chunks)
