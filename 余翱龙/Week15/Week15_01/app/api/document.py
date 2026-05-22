from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.models.database import get_db, Document
from app.models.schemas import DocumentUploadResponse, DocumentInfo, ChunkInfo
from app.services.document_service import DocumentService

router = APIRouter()


@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传PDF文档"""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    service = DocumentService(db)
    doc = await service.upload_document(file)

    return DocumentUploadResponse(
        doc_id=doc.doc_id,
        doc_name=doc.doc_name,
        status=doc.status,
        message="Document uploaded successfully"
    )


@router.post("/documents/{doc_id}/process")
async def process_document(
    doc_id: str,
    db: Session = Depends(get_db)
):
    """处理（解析+向量化）文档"""
    service = DocumentService(db)

    # 检查文档是否存在
    doc = service.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # 处理文档
    try:
        success = await service.process_document(doc_id)
        if success:
            return {"message": "Document processed successfully", "doc_id": doc_id}
        else:
            raise HTTPException(status_code=500, detail="Processing failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{doc_id}", response_model=DocumentInfo)
async def get_document(
    doc_id: str,
    db: Session = Depends(get_db)
):
    """获取文档信息和解析状态"""
    service = DocumentService(db)
    doc = service.get_document(doc_id)

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    chunks = service.get_chunks(doc_id)
    images = service.get_images(doc_id)

    return DocumentInfo(
        doc_id=doc.doc_id,
        doc_name=doc.doc_name,
        status=doc.status,
        created_at=doc.created_at,
        chunk_count=len(chunks),
        image_count=len(images)
    )


@router.get("/documents/{doc_id}/chunks", response_model=List[ChunkInfo])
async def get_document_chunks(
    doc_id: str,
    db: Session = Depends(get_db)
):
    """获取文档chunk列表"""
    service = DocumentService(db)
    chunks = service.get_chunks(doc_id)

    return [
        ChunkInfo(
            chunk_id=c.chunk_id,
            chunk_type=c.chunk_type,
            content=c.content[:500],  # 限制内容长度
            page=c.page
        )
        for c in chunks
    ]


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    db: Session = Depends(get_db)
):
    """删除文档"""
    service = DocumentService(db)
    success = service.delete_document(doc_id)

    if not success:
        raise HTTPException(status_code=404, detail="Document not found")

    return {"message": "Document deleted successfully", "doc_id": doc_id}