import uuid
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.models.schemas import DocumentUploadResponse
from app.db.sqlite import sqlite_client
from app.db.kafka import kafka_client
from app.core.exceptions import DocumentNotFoundError

router = APIRouter(prefix="/upload", tags=["upload"])

DOCS_DIR = Path(__file__).parent.parent / "doc"


@router.post("/document", response_model=DocumentUploadResponse)
async def upload_document(
    knowledge_base_id: str = Form(...),
    file: UploadFile = File(...)
):
    file_id = str(uuid.uuid4())
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in [".pdf", ".docx", ".txt"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    file_path = DOCS_DIR / f"{file_id}{file_ext}"
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    doc_info = {
        "id": file_id,
        "file_name": file.filename,
        "file_path": str(file_path),
        "status": "pending",
        "knowledge_base_id": knowledge_base_id
    }
    sqlite_client.save_document(doc_info)

    kafka_client.send_parse_task(file_id)

    return DocumentUploadResponse(
        document_id=file_id,
        file_name=file.filename,
        status="pending"
    )
