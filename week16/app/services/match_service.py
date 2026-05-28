from __future__ import annotations

from uuid import uuid4

from app.engine.enums import Phase
from app.engine.models import GameEvent, GameState, PlayerState
from app.engine.rules import SETUPS
from app.observability.event_logger import log_event
from app.storage.repositories import persist_state


class MatchService:
    def __init__(self) -> None:
        self._matches: dict[str, GameState] = {}

    async def create_match(self, setup_name: str = "standard_7") -> GameState:
        roles = SETUPS[setup_name]
        match_id = str(uuid4())
        players: list[PlayerState] = []
        werewolf_ids: list[str] = []
        for index, role in enumerate(roles, start=1):
            player_id = f"P{index}"
            if role.value == "werewolf":
                werewolf_ids.append(player_id)
            players.append(PlayerState(player_id=player_id, name=f"Player {index}", role=role, seat=index))

        for player in players:
            if player.role.value == "werewolf":
                player.known_wolves = [wolf_id for wolf_id in werewolf_ids if wolf_id != player.player_id]

        state = GameState(match_id=match_id, phase=Phase.NIGHT_WEREWOLF, players=players)
        log_event(
            state,
            GameEvent(
                match_id=match_id,
                turn=state.turn,
                phase=state.phase,
                event_type="match.created",
                visibility="public",
                payload={"players": [player.player_id for player in players]},
            ),
        )
        self._matches[match_id] = state
        await persist_state(state)
        return state

    def get_match(self, match_id: str) -> GameState:
        return self._matches[match_id]


match_service = MatchService()
