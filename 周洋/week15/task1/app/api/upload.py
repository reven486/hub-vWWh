import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.database import Document, KnowledgeBase, DocumentStatus, get_session
from app.schemas.schemas import DocumentResponse

router = APIRouter(prefix="/upload", tags=["Upload"])


def get_db():
    session = get_session()
    try:
        yield session
    finally:
        session.close()


@router.post("/document", response_model=DocumentResponse, status_code=201)
async def upload_document(
    knowledge_base_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    os.makedirs(settings.upload_dir, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(settings.upload_dir, unique_name)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    doc = Document(
        knowledge_base_id=knowledge_base_id,
        filename=file.filename,
        file_path=file_path,
        file_size=len(content),
        status=DocumentStatus.uploaded,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Send Kafka event for async processing
    try:
        from app.worker.processor import send_parse_event
        send_parse_event(doc.id)
    except Exception:
        pass  # Kafka not available; document stays in 'uploaded' status

    return doc


@router.get("/documents", response_model=list[DocumentResponse])
def list_documents(knowledge_base_id: int = None, db: Session = Depends(get_db)):
    query = db.query(Document)
    if knowledge_base_id:
        query = query.filter(Document.knowledge_base_id == knowledge_base_id)
    return query.order_by(Document.created_at.desc()).all()


@router.get("/documents/{doc_id}", response_model=DocumentResponse)
def get_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc
