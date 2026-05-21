import uuid
import asyncio
import httpx
from pathlib import Path
from PIL import Image

from app.core.config import get_settings
from app.core.exceptions import DocumentParseError
from app.services.embedding import embed_text, embed_images
from app.db import milvus as milvus_db
from app.db.sqlite import insert_chunk, update_document_status, get_document

SUPPORTED_TYPES = {".pdf", ".docx", ".txt"}
DOC_DIR = Path("app/doc/uploads")


def get_doc_dir() -> Path:
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    return DOC_DIR


async def save_uploaded_file(filename: str, content: bytes) -> tuple[str, str]:
    doc_id = str(uuid.uuid4())
    suffix = Path(filename).suffix.lower()
    dest = get_doc_dir() / f"{doc_id}{suffix}"
    dest.write_bytes(content)
    return doc_id, str(dest)


async def _call_mineru(filepath: str) -> dict:
    settings = get_settings()
    url = settings.mineru.base_url + settings.mineru.parse_endpoint
    async with httpx.AsyncClient(timeout=settings.mineru.timeout) as client:
        with open(filepath, "rb") as f:
            files = {"file": (Path(filepath).name, f, "application/octet-stream")}
            resp = await client.post(url, files=files)
        resp.raise_for_status()
        return resp.json()


def _chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


async def process_document(doc_id: str, kb_id: str):
    """Called by the Kafka worker to parse and index a document."""
    await update_document_status(doc_id, "processing")
    doc = await get_document(doc_id)
    if not doc:
        raise DocumentParseError(doc_id, "Document record not found")

    filepath = doc["filepath"]
    filename = doc["filename"]

    try:
        parse_result = await _call_mineru(filepath)
    except Exception as e:
        await update_document_status(doc_id, "failed")
        raise DocumentParseError(doc_id, str(e))

    pages = parse_result.get("pages", [])
    text_chunk_ids, text_kb_ids, text_embeddings = [], [], []
    image_chunk_ids, image_kb_ids, image_embeddings = [], [], []

    for page in pages:
        page_num = page.get("page_num", 0)

        # Process text blocks
        text_blocks = page.get("texts", [])
        all_text = " ".join(b.get("text", "") for b in text_blocks)
        if all_text.strip():
            for idx, chunk_text in enumerate(_chunk_text(all_text)):
                chunk_id = str(uuid.uuid4())
                source_label = f"{filename} | 第{page_num}页 | 文本段落{idx + 1}"
                await insert_chunk(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    kb_id=kb_id,
                    chunk_type="text",
                    content=chunk_text,
                    image_path=None,
                    page_num=page_num,
                    chunk_index=idx,
                    source_label=source_label,
                )
                text_chunk_ids.append(chunk_id)
                text_kb_ids.append(kb_id)

        # Batch embed texts every 32 chunks
        if len(text_chunk_ids) >= 32:
            batch_texts = [
                (await _get_chunk_content(cid)) for cid in text_chunk_ids[-32:]
            ]
            embs = embed_text([t for t in batch_texts if t])
            text_embeddings.extend(embs)

        # Process image blocks
        image_blocks = page.get("images", [])
        for img_idx, img_block in enumerate(image_blocks):
            img_path = img_block.get("path") or img_block.get("image_path")
            if not img_path or not Path(img_path).exists():
                continue
            chunk_id = str(uuid.uuid4())
            fig_label = img_block.get("caption", f"图{img_idx + 1}")
            source_label = f"{filename} | 第{page_num}页 | {fig_label}"
            await insert_chunk(
                chunk_id=chunk_id,
                doc_id=doc_id,
                kb_id=kb_id,
                chunk_type="image",
                content=img_block.get("caption"),
                image_path=img_path,
                page_num=page_num,
                chunk_index=img_idx,
                source_label=source_label,
            )
            try:
                img = Image.open(img_path).convert("RGB")
                emb = embed_images([img])[0]
                image_chunk_ids.append(chunk_id)
                image_kb_ids.append(kb_id)
                image_embeddings.append(emb)
            except Exception:
                pass

    # Embed remaining text chunks
    if text_chunk_ids:
        from app.db.sqlite import get_chunks_by_ids
        remaining = len(text_chunk_ids) - len(text_embeddings)
        if remaining > 0:
            chunks = await get_chunks_by_ids(text_chunk_ids[-remaining:])
            texts = [c.get("content", "") for c in chunks]
            if texts:
                embs = embed_text(texts)
                text_embeddings.extend(embs)

    if text_chunk_ids and text_embeddings:
        milvus_db.insert_text_vectors(text_chunk_ids, text_kb_ids, text_embeddings)
    if image_chunk_ids and image_embeddings:
        milvus_db.insert_image_vectors(image_chunk_ids, image_kb_ids, image_embeddings)

    await update_document_status(doc_id, "completed")


async def _get_chunk_content(chunk_id: str) -> str:
    from app.db.sqlite import get_chunks_by_ids
    chunks = await get_chunks_by_ids([chunk_id])
    return chunks[0].get("content", "") if chunks else ""
