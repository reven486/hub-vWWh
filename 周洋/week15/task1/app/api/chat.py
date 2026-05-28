"""
Chat endpoint for Q&A over knowledge bases.

Uses BGE + CLIP embedders and Milvus retriever for context retrieval,
and Qwen-VL for answer generation. All model loading is lazy and
failures are handled gracefully so that validation errors on the
request body are reported as 422 rather than 500.
"""

from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.database import KnowledgeBase, get_session
from app.schemas.schemas import ChatRequest, ChatResponse, SourceInfo

router = APIRouter(prefix="/chat", tags=["Chat"])


def get_db():
    session = get_session()
    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Lazy initialisers  (no FastAPI Depends so body validation works first)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _get_bge_embedder():
    from app.services.embedder import BgeEmbedder
    return BgeEmbedder()


@lru_cache(maxsize=1)
def _get_clip_embedder():
    from app.services.embedder import ClipEmbedder
    return ClipEmbedder()


@lru_cache(maxsize=1)
def _get_retriever():
    from app.services.retriever import MilvusRetriever
    return MilvusRetriever()


# ---------------------------------------------------------------------------
# Answer generation helpers
# ---------------------------------------------------------------------------

def _generate_answer(prompt: str, retrieved: list[dict]) -> str:
    """Generate answer using Qwen-VL, falling back to a summary on error."""
    try:
        from app.core.dependencies import get_qwen_vl
        qwen = get_qwen_vl()
        model = qwen["model"]
        tokenizer = qwen["tokenizer"]

        messages = [{"role": "user", "content": prompt}]
        text = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True,
        )
        import torch
        inputs = tokenizer([text], return_tensors="pt").to(model.device)

        outputs = model.generate(
            **inputs, max_new_tokens=512, temperature=0.7,
        )
        response = tokenizer.decode(
            outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True,
        )
        return response.strip()
    except Exception:
        if retrieved:
            texts = [
                r.get("text_content", "")
                for r in retrieved
                if r.get("text_content")
            ]
            return "Based on retrieved documents:\n\n" + "\n".join(texts[:3])
        return "Unable to generate answer. No relevant context found."


def _build_context(results: list[dict]) -> tuple[list[SourceInfo], str]:
    """Build sources list and context string from retrieval results."""
    sources = []
    context_texts = []
    for r in results:
        sources.append(SourceInfo(
            document_id=r.get("document_id", 0),
            filename="",
            page_number=r.get("page_number", 0),
            chunk_index=r.get("chunk_id", 0),
            content=r.get("text_content", ""),
            score=r.get("score", 0.0),
        ))
        if r.get("text_content"):
            context_texts.append(f"[Page {r['page_number']}]: {r['text_content']}")

    context = (
        "\n\n".join(context_texts)
        if context_texts
        else "No relevant documents found."
    )
    return sources, context


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.post("", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    # 1. Validate KB exists  (fast path -- no models loaded yet)
    kb = (
        db.query(KnowledgeBase)
        .filter(KnowledgeBase.id == request.knowledge_base_id)
        .first()
    )
    if not kb:
        raise HTTPException(
            status_code=404, detail="Knowledge base not found",
        )

    # 2. Load embedders and retriever lazily (will raise on first call
    #    if models / Milvus are unavailable, but the 422 validation
    #    branch is already out of the way).
    try:
        bge = _get_bge_embedder()
        clip = _get_clip_embedder()
        retriever = _get_retriever()
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Backend service unavailable: {exc}",
        )

    # 3. Retrieve context
    try:
        bge_vec = bge.embed_query(request.question)
        clip_vec = clip.embed_query(request.question)
        results = retriever.search(bge_vec, clip_vec, top_k=request.top_k)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Retrieval failed: {exc}",
        )

    # 4. Build context and answer
    sources, context = _build_context(results)

    prompt = (
        "You are a multimodal document QA assistant. Answer the question "
        "based on the provided context.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {request.question}\n\n"
        "Answer the question concisely and cite the source page numbers "
        "where applicable."
    )

    answer = _generate_answer(prompt, results)

    return ChatResponse(
        answer=answer,
        sources=[s.model_dump() for s in sources],
    )
