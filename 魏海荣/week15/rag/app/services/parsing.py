import uuid
from typing import Dict, Any, List
import httpx
from pathlib import Path
from app.core.config import config
from app.core.exceptions import ParseError
from app.db.sqlite import sqlite_client
from app.db.milvus import milvus_client
from app.services.retrieval import retrieval_service


class ParsingService:
    def __init__(self):
        self._mineru_base_url = None

    @property
    def mineru_base_url(self) -> str:
        if self._mineru_base_url is None:
            self._mineru_base_url = config.mineru.get("base_url", "http://localhost:8001")
        return self._mineru_base_url

    async def parse_pdf(self, file_path: str) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=config.mineru.get("timeout", 300)) as client:
                with open(file_path, "rb") as f:
                    files = {"file": (Path(file_path).name, f, "application/pdf")}
                    response = await client.post(
                        f"{self.mineru_base_url}/parse",
                        files=files
                    )
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException:
            raise ParseError("Mineru parse timeout")
        except Exception as e:
            raise ParseError(f"Mineru parse failed: {str(e)}")

    def chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start = end
        return chunks

    def process_document(self, document_id: str, parse_result: Dict[str, Any]):
        doc_info = sqlite_client.get_document(document_id)
        if not doc_info:
            raise ParseError(f"Document not found: {document_id}")

        pdf_name = doc_info["file_name"]

        for page_idx, page_content in enumerate(parse_result.get("pages", []), start=1):
            text_blocks = page_content.get("texts", [])
            for block_idx, block in enumerate(text_blocks):
                chunk_id = str(uuid.uuid4())
                content = block.get("content", "")
                if not content:
                    continue

                chunk = {
                    "id": chunk_id,
                    "document_id": document_id,
                    "content": content,
                    "page": page_idx,
                    "chunk_index": block_idx
                }
                sqlite_client.save_text_chunk(chunk)

                embedding = retrieval_service.encode_text(content)
                milvus_client.insert_text(document_id, chunk_id, embedding, page_idx)

            image_blocks = page_content.get("images", [])
            for img_idx, img_block in enumerate(image_blocks):
                chunk_id = str(uuid.uuid4())
                image_path = img_block.get("path", "")
                chart_id = img_block.get("chart_id")

                if not image_path:
                    continue

                chunk = {
                    "id": chunk_id,
                    "document_id": document_id,
                    "image_path": image_path,
                    "page": page_idx,
                    "chart_id": chart_id
                }
                sqlite_client.save_image_chunk(chunk)

                try:
                    embedding = retrieval_service.encode_image(image_path)
                    milvus_client.insert_image(document_id, chunk_id, embedding, page_idx)
                except Exception:
                    pass

        sqlite_client.update_document_status(document_id, "completed")


parsing_service = ParsingService()
