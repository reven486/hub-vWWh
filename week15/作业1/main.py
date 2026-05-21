import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.exceptions import DocumentParseError, UnsupportedFileTypeError
from app.db.sqlite import init_db
from app.db.milvus import connect_milvus
from app.api import upload, chat

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing SQLite schema...")
    await init_db()
    logger.info("Connecting to Milvus...")
    try:
        connect_milvus()
        logger.info("Milvus connected")
    except Exception as e:
        logger.warning("Milvus connection failed (will retry on use): %s", e)
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="多模态文档智能问答系统",
    description="基于图文混排 PDF 知识库的多模态问答系统",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(upload.router)
app.include_router(chat.router)


@app.exception_handler(UnsupportedFileTypeError)
async def unsupported_file_handler(request: Request, exc: UnsupportedFileTypeError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(DocumentParseError)
async def parse_error_handler(request: Request, exc: DocumentParseError):
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run("main:app", host=settings.app.host, port=settings.app.port, reload=settings.app.debug)
