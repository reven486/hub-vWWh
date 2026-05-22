from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
from app.config import settings

Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"

    doc_id = Column(String(36), primary_key=True)
    doc_name = Column(String(255), nullable=False)
    doc_path = Column(String(512), nullable=False)
    status = Column(String(20), default="pending")  # pending, parsing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    chunks = relationship("Chunk", back_populates="document")
    images = relationship("Image", back_populates="document")


class Chunk(Base):
    __tablename__ = "chunks"

    chunk_id = Column(String(36), primary_key=True)
    doc_id = Column(String(36), ForeignKey("documents.doc_id"), nullable=False)
    chunk_type = Column(String(20), nullable=False)  # text, image_caption
    content = Column(Text, nullable=False)
    vector_id = Column(Integer, nullable=True)
    page = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="chunks")


class Image(Base):
    __tablename__ = "images"

    image_id = Column(String(36), primary_key=True)
    doc_id = Column(String(36), ForeignKey("documents.doc_id"), nullable=False)
    image_path = Column(String(512), nullable=False)
    caption = Column(Text, nullable=True)
    vector_id = Column(Integer, nullable=True)
    page = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="images")


engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)