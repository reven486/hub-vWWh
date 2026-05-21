import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.core.exceptions import UnsupportedFileTypeError
from app.models.schemas import UploadDocumentResponse
from app.services.document import SUPPORTED_TYPES, save_uploaded_file
from app.db.sqlite import insert_document
from app.db.kafka import send_parse_task

router = APIRouter()


@router.post("/upload/document", response_model=UploadDocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    kb_id: str = Form(..., description="Knowledge base ID"),
):
    filename = file.filename or "unknown"
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_TYPES:
        raise UnsupportedFileTypeError(filename)

    content = await file.read()
    doc_id, filepath = await save_uploaded_file(filename, content)

    await insert_document(doc_id=doc_id, filename=filename, filepath=filepath, kb_id=kb_id)
    await send_parse_task(doc_id=doc_id, kb_id=kb_id)

    return UploadDocumentResponse(
        doc_id=doc_id,
        filename=filename,
        kb_id=kb_id,
        status="pending",
    )
