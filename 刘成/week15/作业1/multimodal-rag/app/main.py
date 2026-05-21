from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.router import api_router
from app.config import settings
from app.services.qdrant_service import qdrant_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure Qdrant collection exists
    if not qdrant_service.collection_exists():
        qdrant_service.create_collection()
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title="Multimodal RAG System",
    description="RAG system with Qwen3 + Qwen-VL + DashScope",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Multimodal RAG System API", "version": "0.1.0"}
