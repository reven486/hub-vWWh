from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional

from app.models.schemas import QueryRequest, QueryResponse
from app.services.pipeline import rag_pipeline

router = APIRouter()


@router.post("", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    Query the RAG system with text and/or image input.
    Returns answer along with retrieved context chunks.
    """
    try:
        result = rag_pipeline.query(
            query_text=request.query_text,
            query_image=request.query_image,
            top_k=request.top_k or 5,
        )
        return QueryResponse(
            answer=result["answer"],
            retrieved_chunks=result["retrieved_chunks"],
            has_image_query=result["has_image_query"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def query_documents_stream(request: QueryRequest):
    """
    Query with streaming response (SSE).
    """
    async def event_generator():
        try:
            for chunk in rag_pipeline.query_stream(
                query_text=request.query_text,
                query_image=request.query_image,
                top_k=request.top_k or 5,
            ):
                yield f"data: {chunk}\n\n"
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
