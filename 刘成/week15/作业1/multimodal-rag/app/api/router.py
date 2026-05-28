from fastapi import APIRouter

from app.api import ingest, query, collection, health

api_router = APIRouter()

api_router.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
api_router.include_router(query.router, prefix="/query", tags=["query"])
api_router.include_router(collection.router, prefix="/collection", tags=["collection"])
api_router.include_router(health.router, tags=["health"])
