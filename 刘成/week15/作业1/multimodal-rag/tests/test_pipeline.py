import pytest
from unittest.mock import patch, MagicMock

from app.services.pipeline import RAGPipeline
from app.models.document import ChunkType


@pytest.fixture
def rag_pipeline():
    return RAGPipeline()


def test_ingest_document_mock(rag_pipeline):
    """Test document ingestion with mocked services"""
    with patch.object(rag_pipeline, 'embed_chunks') as mock_embed:
        mock_embed.return_value = [[0.1] * 1024]

        with patch('app.services.qdrant_service.qdrant_service.upsert_points'):
            result = rag_pipeline.ingest_document(
                file_content=b"Test content",
                filename="test.txt",
            )

            assert "document_id" in result
            assert result["chunk_count"] >= 0


def test_query_requires_input(rag_pipeline):
    """Test that query requires either text or image input"""
    with pytest.raises(ValueError):
        rag_pipeline.query(query_text=None, query_image=None)
