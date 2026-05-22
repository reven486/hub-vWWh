import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import sessionmaker, declarative_base
from enum import Enum as PyEnum

DB_URL = "sqlite:///./files.db"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class FileStatus(PyEnum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DocumentFile(Base):
    __tablename__ = "document_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    file_path = Column(String, unique=True, index=True)
    upload_time = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default=FileStatus.UPLOADED.value)
    error_message = Column(String, nullable=True)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_document(db, filename: str, file_path: str):
    db_doc = DocumentFile(filename=filename, file_path=file_path, status=FileStatus.UPLOADED.value)
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    return db_doc

def update_document_status(db, doc_id: int, status: str, error_message: str = None):
    db_doc = db.query(DocumentFile).filter(DocumentFile.id == doc_id).first()
    if db_doc:
        db_doc.status = status
        if error_message:
            db_doc.error_message = error_message
        db.commit()
        db.refresh(db_doc)
    return db_doc
