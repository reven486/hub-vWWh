import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from app.core.config import config


class SQLiteClient:
    _instance: Optional["SQLiteClient"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_db()
        return cls._instance

    def _init_db(self):
        db_path = config.database.get("sqlite", {}).get("path", "data/metadata.db")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_tables()

    def _create_tables(self):
        cursor = self._conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                knowledge_base_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS text_chunks (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                content TEXT NOT NULL,
                page INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                embedding_id TEXT,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS image_chunks (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                image_path TEXT NOT NULL,
                page INTEGER NOT NULL,
                chart_id TEXT,
                embedding_id TEXT,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            )
        """)
        self._conn.commit()

    def save_document(self, doc: Dict[str, Any]) -> str:
        cursor = self._conn.cursor()
        cursor.execute(
            "INSERT INTO documents (id, file_name, file_path, status, knowledge_base_id) VALUES (?, ?, ?, ?, ?)",
            (doc["id"], doc["file_name"], doc["file_path"], doc.get("status", "pending"), doc["knowledge_base_id"])
        )
        self._conn.commit()
        return doc["id"]

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "file_name": row[1],
                "file_path": row[2],
                "status": row[3],
                "knowledge_base_id": row[4]
            }
        return None

    def update_document_status(self, doc_id: str, status: str):
        cursor = self._conn.cursor()
        cursor.execute(
            "UPDATE documents SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, doc_id)
        )
        self._conn.commit()

    def save_text_chunk(self, chunk: Dict[str, Any]):
        cursor = self._conn.cursor()
        cursor.execute(
            "INSERT INTO text_chunks (id, document_id, content, page, chunk_index, embedding_id) VALUES (?, ?, ?, ?, ?, ?)",
            (chunk["id"], chunk["document_id"], chunk["content"], chunk["page"], chunk["chunk_index"], chunk.get("embedding_id"))
        )
        self._conn.commit()

    def save_image_chunk(self, chunk: Dict[str, Any]):
        cursor = self._conn.cursor()
        cursor.execute(
            "INSERT INTO image_chunks (id, document_id, image_path, page, chart_id, embedding_id) VALUES (?, ?, ?, ?, ?, ?)",
            (chunk["id"], chunk["document_id"], chunk["image_path"], chunk["page"], chunk.get("chart_id"), chunk.get("embedding_id"))
        )
        self._conn.commit()

    def get_text_chunks_by_document(self, doc_id: str) -> List[Dict[str, Any]]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM text_chunks WHERE document_id = ?", (doc_id,))
        return [{"id": r[0], "document_id": r[1], "content": r[2], "page": r[3], "chunk_index": r[4]} for r in cursor.fetchall()]

    def get_image_chunks_by_document(self, doc_id: str) -> List[Dict[str, Any]]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM image_chunks WHERE document_id = ?", (doc_id,))
        return [{"id": r[0], "document_id": r[1], "image_path": r[2], "page": r[3], "chart_id": r[4]} for r in cursor.fetchall()]


sqlite_client = SQLiteClient()
