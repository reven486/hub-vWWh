from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatRequest, ChatResponse
from app.db.sqlite import sqlite_client
from app.services.retrieval import retrieval_service
from app.services.reasoning import reasoning_service
from app.core.exceptions import KnowledgeBaseNotFoundError

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    text_results = retrieval_service.search_text(request.query, request.top_k)
    image_results = retrieval_service.search_image(request.query, request.top_k)

    text_contents = []
    for item in text_results:
        doc = sqlite_client.get_document(item["document_id"])
        if doc:
            text_contents.append({
                "content": f"PDF: {doc['file_name']}, 第{item['page']}页",
                "pdf_name": doc["file_name"],
                "page": item["page"],
                "source": f"{doc['file_name']} 第{item['page']}页"
            })

    image_contents = []
    for item in image_results:
        doc = sqlite_client.get_document(item["document_id"])
        if doc:
            image_contents.append({
                "chart_id": item.get("chart_id", "未知"),
                "pdf_name": doc["file_name"],
                "page": item["page"],
                "source": f"{doc['file_name']} 第{item['page']}页 图表"
            })

    answer, sources = reasoning_service.generate_answer(
        request.query,
        text_contents,
        image_contents
    )

    return ChatResponse(answer=answer, sources=sources)
