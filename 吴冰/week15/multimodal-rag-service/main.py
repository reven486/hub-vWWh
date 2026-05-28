import logging
from fastapi import FastAPI

from config import UPLOAD_DIR, STATIC_DIR
from orm.database import init_db
from services.vector_store import ensure_collection
from api.document import router as document_router
from api.retrieval import router as retrieval_router
from api.chat import router as chat_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Multimodal RAG Service", version="1.0.0")

# 注册路由
app.include_router(document_router)
app.include_router(retrieval_router)
app.include_router(chat_router)

# 挂载静态目录（用于访问解析后的图片）
import os
from fastapi.staticfiles import StaticFiles

if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
def startup():
    """初始化数据库和必要目录。"""
    init_db()
    ensure_collection()
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    logger.info("Multimodal RAG Service started")


@app.get("/health")
def health():
    return {"status": "ok"}
