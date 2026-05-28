from app.storage.jsonl_store import read_events
from app.observability.trace_redaction import public_projection


class ReplayService:
    def get_public_replay(self, match_id: str) -> list[dict]:
        return public_projection(read_events(match_id))

    def get_full_replay(self, match_id: str) -> list[dict]:
        return read_events(match_id)


replay_service = ReplayService()
