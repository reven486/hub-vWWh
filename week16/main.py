from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes_matches import router as matches_router
from app.api.routes_players import router as players_router
from app.api.routes_replay import router as replay_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.storage.sqlite import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await init_db()
    yield


app = FastAPI(
    title="AI Werewolf",
    description="Multi-agent werewolf game with structured replay and spectator view",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(matches_router)
app.include_router(players_router)
app.include_router(replay_router)

frontend_dir = Path(__file__).parent / "frontend"
if frontend_dir.exists():
    app.mount("/frontend", StaticFiles(directory=frontend_dir), name="frontend")


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return (frontend_dir / "index.html").read_text(encoding="utf-8")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run("main:app", host=settings.app.host, port=settings.app.port, reload=settings.app.debug)
