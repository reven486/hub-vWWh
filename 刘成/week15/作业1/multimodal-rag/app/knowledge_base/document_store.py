import shutil
import aiofiles
from pathlib import Path
from typing import Optional
import uuid

from app.config import settings


class DocumentStore:
    """Handles raw file persistence to data/documents/"""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or settings.documents_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save_file(self, file_content: bytes, original_filename: str, doc_id: str) -> str:
        """Save file to data/documents/{doc_id}/{original_filename}"""
        doc_dir = self.base_dir / doc_id
        doc_dir.mkdir(parents=True, exist_ok=True)

        dest_path = doc_dir / original_filename

        async with aiofiles.open(dest_path, "wb") as f:
            await f.write(file_content)

        return str(dest_path)

    def get_file_path(self, doc_id: str, filename: str) -> Optional[Path]:
        """Get the stored file path"""
        path = self.base_dir / doc_id / filename
        if path.exists():
            return path
        return None

    async def delete_file(self, doc_id: str, filename: str) -> bool:
        """Delete a specific file"""
        path = self.base_dir / doc_id / filename
        if path.exists():
            path.unlink()
            return True
        return False

    async def delete_document_files(self, doc_id: str) -> bool:
        """Delete all files for a document"""
        doc_dir = self.base_dir / doc_id
        if doc_dir.exists():
            shutil.rmtree(doc_dir)
            return True
        return False

    def get_file_size(self, doc_id: str, filename: str) -> Optional[int]:
        """Get file size"""
        path = self.base_dir / doc_id / filename
        if path.exists():
            return path.stat().st_size
        return None


document_store = DocumentStore()
