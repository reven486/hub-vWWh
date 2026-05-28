from __future__ import annotations

from datetime import datetime, UTC
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.engine.enums import ActionType, Phase, Role


class PlayerState(BaseModel):
    player_id: str
    name: str
    role: Role
    alive: bool = True
    seat: int
    known_wolves: list[str] = Field(default_factory=list)
    seer_checks: dict[str, Role] = Field(default_factory=dict)
    witch_save_available: bool = True
    witch_poison_available: bool = True


class PublicGameState(BaseModel):
    turn: int
    phase: Phase
    alive_players: list[str]
    eliminated_players: list[str]
    recent_public_events: list[dict[str, Any]]


class ObservationEnvelope(BaseModel):
    player_id: str
    role: Role
    public_state: PublicGameState
    private_state: dict[str, Any]
    action_space: list[ActionType]


class ActionIntent(BaseModel):
    player_id: str
    action_type: ActionType
    target_id: str | None = None
    content: str | None = None


class GameEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    match_id: str
    turn: int
    phase: Phase
    event_type: str
    visibility: str
    actor_player_id: str | None = None
    target_player_id: str | None = None
    role: Role | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    llm_metadata: dict[str, Any] | None = None


class GameState(BaseModel):
    match_id: str
    turn: int = 1
    phase: Phase = Phase.NIGHT_WEREWOLF
    players: list[PlayerState]
    events: list[GameEvent] = Field(default_factory=list)
    pending_night_kill: str | None = None
    pending_save_target: str | None = None
    pending_poison_target: str | None = None
    winner: str | None = None

    def alive_players(self) -> list[PlayerState]:
        return [player for player in self.players if player.alive]

    def get_player(self, player_id: str) -> PlayerState:
        for player in self.players:
            if player.player_id == player_id:
                return player
        raise KeyError(player_id)

    def eliminated_player_ids(self) -> list[str]:
        return [player.player_id for player in self.players if not player.alive]
