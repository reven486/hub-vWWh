import sqlite3
from pathlib import Path
from typing import Optional
from datetime import datetime
import uuid

from app.config import settings
from app.models.schemas import DocumentResponse, ChunkResponse, IndexResponse, DocStatus


class KnowledgeBaseManager:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.metadata_db
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                source_file TEXT NOT NULL,
                doc_type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                chunk_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'processing'
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                chunk_type TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content_text TEXT,
                page INTEGER,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS indexes (
                document_id TEXT PRIMARY KEY,
                qdrant_points_count INTEGER,
                last_indexed_at TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            )
        """)

        conn.commit()
        conn.close()

    def add_document(
        self,
        source_file: str,
        doc_type: str,
        file_path: str,
        file_size: Optional[int] = None,
    ) -> str:
        doc_id = str(uuid.uuid4())
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO documents (id, source_file, doc_type, file_path, file_size)
            VALUES (?, ?, ?, ?, ?)
            """,
            (doc_id, source_file, doc_type, file_path, file_size),
        )
        conn.commit()
        conn.close()
        return doc_id

    def get_document(self, doc_id: str) -> Optional[DocumentResponse]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return DocumentResponse(
                id=row["id"],
                source_file=row["source_file"],
                doc_type=row["doc_type"],
                file_path=row["file_path"],
                file_size=row["file_size"],
                uploaded_at=datetime.fromisoformat(row["uploaded_at"]),
                chunk_count=row["chunk_count"],
                status=DocStatus(row["status"]),
            )
        return None

    def list_documents(self) -> list[DocumentResponse]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM documents ORDER BY uploaded_at DESC")
        rows = cursor.fetchall()
        conn.close()

        return [
            DocumentResponse(
                id=row["id"],
                source_file=row["source_file"],
                doc_type=row["doc_type"],
                file_path=row["file_path"],
                file_size=row["file_size"],
                uploaded_at=datetime.fromisoformat(row["uploaded_at"]),
                chunk_count=row["chunk_count"],
                status=DocStatus(row["status"]),
            )
            for row in rows
        ]

    def update_document_status(
        self, doc_id: str, status: DocStatus, chunk_count: Optional[int] = None
    ):
        conn = self._get_conn()
        cursor = conn.cursor()
        if chunk_count is not None:
            cursor.execute(
                "UPDATE documents SET status = ?, chunk_count = ? WHERE id = ?",
                (status.value, chunk_count, doc_id),
            )
        else:
            cursor.execute(
                "UPDATE documents SET status = ? WHERE id = ?",
                (status.value, doc_id),
            )
        conn.commit()
        conn.close()

    def delete_document(self, doc_id: str):
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM chunks WHERE document_id = ?", (doc_id,))
        cursor.execute("DELETE FROM indexes WHERE document_id = ?", (doc_id,))
        cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))

        conn.commit()
        conn.close()

    def add_chunk(
        self,
        doc_id: str,
        chunk_type: str,
        chunk_index: int,
        content_text: Optional[str] = None,
        page: Optional[int] = None,
    ) -> str:
        chunk_id = str(uuid.uuid4())
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO chunks (id, document_id, chunk_type, chunk_index, content_text, page)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (chunk_id, doc_id, chunk_type, chunk_index, content_text, page),
        )
        conn.commit()
        conn.close()
        return chunk_id

    def get_chunks_by_document(self, doc_id: str) -> list[ChunkResponse]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM chunks WHERE document_id = ? ORDER BY chunk_index",
            (doc_id,),
        )
        rows = cursor.fetchall()
        conn.close()

        return [
            ChunkResponse(
                id=row["id"],
                document_id=row["document_id"],
                chunk_type=row["chunk_type"],
                chunk_index=row["chunk_index"],
                content_text=row["content_text"],
                page=row["page"],
            )
            for row in rows
        ]

    def update_index(self, doc_id: str, points_count: int):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO indexes (document_id, qdrant_points_count, last_indexed_at)
            VALUES (?, ?, ?)
            """,
            (doc_id, points_count, datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()

    def get_index_info(self, doc_id: str) -> Optional[IndexResponse]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM indexes WHERE document_id = ?", (doc_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            last_indexed = row["last_indexed_at"]
            return IndexResponse(
                document_id=row["document_id"],
                qdrant_points_count=row["qdrant_points_count"],
                last_indexed_at=datetime.fromisoformat(last_indexed) if last_indexed else None,
            )
        return None


kb_manager = KnowledgeBaseManager()
