import logging

from app.engine.models import GameEvent, GameState
from app.storage.jsonl_store import append_event

logger = logging.getLogger(__name__)


def log_event(state: GameState, event: GameEvent) -> None:
    state.events.append(event)
    append_event(event)
    logger.info(event.event_type, extra={"event": event.model_dump(mode="json")})
