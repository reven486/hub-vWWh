import json
from pathlib import Path

from app.core.config import get_settings
from app.engine.models import GameEvent


def _event_path(match_id: str) -> Path:
    data_dir = Path(get_settings().game.data_dir) / match_id
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "events.jsonl"


def append_event(event: GameEvent) -> None:
    path = _event_path(event.match_id)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event.model_dump(mode="json"), ensure_ascii=False) + "\n")


def read_events(match_id: str) -> list[dict]:
    path = _event_path(match_id)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
