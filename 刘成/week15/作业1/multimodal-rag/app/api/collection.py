from fastapi import APIRouter, HTTPException

from app.models.schemas import CollectionStats
from app.services.qdrant_service import qdrant_service
from app.knowledge_base.manager import kb_manager

router = APIRouter()


@router.get("/stats", response_model=CollectionStats)
async def get_collection_stats():
    """Get Qdrant collection statistics"""
    try:
        info = qdrant_service.get_collection_info()
        return CollectionStats(
            collection_name=info["collection_name"],
            points_count=info["points_count"],
            vectors_count=info["vectors_count"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_collection():
    """Reset the entire collection - delete all points and SQLite data"""
    try:
        # Reset Qdrant collection
        qdrant_service.reset_collection()

        # Clear SQLite data
        docs = kb_manager.list_documents()
        for doc in docs:
            kb_manager.delete_document(doc.id)

        return {"message": "Collection reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
