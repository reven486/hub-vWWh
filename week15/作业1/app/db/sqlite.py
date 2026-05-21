import aiosqlite
from pathlib import Path
from app.core.config import get_settings


async def get_db() -> aiosqlite.Connection:
    settings = get_settings()
    db_path = Path(settings.sqlite.db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return await aiosqlite.connect(str(db_path))


async def init_db():
    async with await get_db() as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                filepath TEXT NOT NULL,
                kb_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id TEXT PRIMARY KEY,
                doc_id TEXT NOT NULL,
                kb_id TEXT NOT NULL,
                chunk_type TEXT NOT NULL,
                content TEXT,
                image_path TEXT,
                page_num INTEGER,
                chunk_index INTEGER,
                source_label TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (doc_id) REFERENCES documents(id)
            )
        """)
        await db.commit()


async def insert_document(doc_id: str, filename: str, filepath: str, kb_id: str):
    async with await get_db() as db:
        await db.execute(
            "INSERT INTO documents (id, filename, filepath, kb_id, status) VALUES (?, ?, ?, ?, 'pending')",
            (doc_id, filename, filepath, kb_id),
        )
        await db.commit()


async def update_document_status(doc_id: str, status: str):
    async with await get_db() as db:
        await db.execute(
            "UPDATE documents SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, doc_id),
        )
        await db.commit()


async def get_document(doc_id: str) -> dict | None:
    async with await get_db() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def insert_chunk(
    chunk_id: str,
    doc_id: str,
    kb_id: str,
    chunk_type: str,
    content: str | None,
    image_path: str | None,
    page_num: int,
    chunk_index: int,
    source_label: str,
):
    async with await get_db() as db:
        await db.execute(
            """INSERT INTO chunks
               (id, doc_id, kb_id, chunk_type, content, image_path, page_num, chunk_index, source_label)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (chunk_id, doc_id, kb_id, chunk_type, content, image_path, page_num, chunk_index, source_label),
        )
        await db.commit()


async def get_chunks_by_ids(chunk_ids: list[str]) -> list[dict]:
    if not chunk_ids:
        return []
    placeholders = ",".join("?" * len(chunk_ids))
    async with await get_db() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            f"SELECT * FROM chunks WHERE id IN ({placeholders})", chunk_ids
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]
