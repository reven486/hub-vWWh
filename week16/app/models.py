from pydantic import BaseModel


class MatchCreateResponse(BaseModel):
    match_id: str
    phase: str
    players: list[dict]


class MatchStateResponse(BaseModel):
    match_id: str
    winner: str | None
    turn: int
    phase: str


class ReplayResponse(BaseModel):
    match_id: str
    events: list[dict]
