from app.services.embedding import embed_single_text, embed_text_clip
from app.db import milvus as milvus_db
from app.db.sqlite import get_chunks_by_ids


async def retrieve_text_chunks(kb_id: str, question: str, top_k: int = 5) -> list[dict]:
    query_emb = embed_single_text(question)
    chunk_ids = milvus_db.search_text_vectors(kb_id, query_emb, top_k)
    return await get_chunks_by_ids(chunk_ids)


async def retrieve_image_chunks(kb_id: str, question: str, top_k: int = 3) -> list[dict]:
    query_emb = embed_text_clip([question])[0]
    chunk_ids = milvus_db.search_image_vectors(kb_id, query_emb, top_k)
    return await get_chunks_by_ids(chunk_ids)


async def retrieve_context(
    kb_id: str, question: str, top_k_text: int = 5, top_k_image: int = 3
) -> tuple[list[dict], list[dict]]:
    text_chunks = await retrieve_text_chunks(kb_id, question, top_k_text)
    image_chunks = await retrieve_image_chunks(kb_id, question, top_k_image)
    return text_chunks, image_chunks
