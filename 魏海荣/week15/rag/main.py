from fastapi import FastAPI
from app.api.upload import router as upload_router
from app.api.chat import router as chat_router

app = FastAPI(
    title="多模态文档智能问答系统",
    description="基于PDF知识库的多模态问答系统",
    version="1.0.0"
)

app.include_router(upload_router)
app.include_router(chat_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    from app.core.config import config

    uvicorn.run(
        "main:app",
        host=config.app.get("host", "0.0.0.0"),
        port=config.app.get("port", 8000),
        reload=config.app.get("debug", False)
    )
