from fastapi import APIRouter, HTTPException

from app.models.schemas import ChatRequest, ChatResponse, SourceInfo
from app.services.retrieval import retrieve_context
from app.services.llm import generate_answer

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    text_chunks, image_chunks = await retrieve_context(
        kb_id=request.kb_id,
        question=request.question,
        top_k_text=request.top_k_text,
        top_k_image=request.top_k_image,
    )

    answer = await generate_answer(
        question=request.question,
        text_chunks=text_chunks,
        image_chunks=image_chunks,
    )

    sources: list[SourceInfo] = []
    seen = set()
    for chunk in text_chunks + image_chunks:
        chunk_id = chunk.get("id")
        if chunk_id in seen:
            continue
        seen.add(chunk_id)
        sources.append(
            SourceInfo(
                doc_id=chunk.get("doc_id", ""),
                page_num=chunk.get("page_num"),
                chunk_type=chunk.get("chunk_type", "text"),
                source_label=chunk.get("source_label"),
            )
        )

    return ChatResponse(answer=answer, sources=sources)
