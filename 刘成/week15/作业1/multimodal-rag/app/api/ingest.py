from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Optional

from app.models.schemas import IngestResponse, DocumentResponse, DocStatus
from app.services.pipeline import rag_pipeline
from app.knowledge_base.manager import kb_manager

router = APIRouter()


@router.post("", response_model=IngestResponse)
async def ingest_document(
    file: UploadFile = File(...),
):
    """
    Ingest a document (PDF, DOCX, TXT, or image).
    Extracts text/images, chunks, embeds, and stores in Qdrant.
    """
    try:
        content = await file.read()
        result = rag_pipeline.ingest_document(
            file_content=content,
            filename=file.filename,
        )
        return IngestResponse(
            document_id=result["document_id"],
            chunk_count=result["chunk_count"],
            status=result["status"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document from Qdrant, disk, and SQLite"""
    try:
        doc = kb_manager.get_document(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete from Qdrant
        from app.services.qdrant_service import qdrant_service
        qdrant_service.delete_by_document_id(doc_id)

        # Delete from disk
        from app.knowledge_base.document_store import document_store
        from pathlib import Path
        doc_dir = document_store.base_dir / doc_id
        if doc_dir.exists():
            import shutil
            shutil.rmtree(doc_dir)

        # Delete from SQLite
        kb_manager.delete_document(doc_id)

        return {"message": "Document deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents", response_model=list[DocumentResponse])
async def list_documents():
    """List all ingested documents"""
    return kb_manager.list_documents()


@router.get("/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str):
    """Get document metadata"""
    doc = kb_manager.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc
