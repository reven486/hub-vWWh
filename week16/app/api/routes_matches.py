from fastapi import APIRouter

from app.models import MatchCreateResponse, MatchStateResponse
from app.services.match_service import match_service
from app.services.turn_runner import TurnRunner

router = APIRouter(prefix="/matches", tags=["matches"])


def build_match_state_response(state) -> MatchStateResponse:
    return MatchStateResponse(match_id=state.match_id, winner=state.winner, turn=state.turn, phase=state.phase.value)


@router.post("", response_model=MatchCreateResponse)
async def create_match() -> MatchCreateResponse:
    state = await match_service.create_match()
    return MatchCreateResponse(
        match_id=state.match_id,
        phase=state.phase.value,
        players=[{"player_id": player.player_id, "seat": player.seat} for player in state.players],
    )


@router.get("/{match_id}", response_model=MatchStateResponse)
async def get_match(match_id: str) -> MatchStateResponse:
    return build_match_state_response(match_service.get_match(match_id))


@router.post("/{match_id}/step", response_model=MatchStateResponse)
async def step_match(match_id: str) -> MatchStateResponse:
    state = match_service.get_match(match_id)
    state = await TurnRunner().step_match(state)
    return build_match_state_response(state)


@router.post("/{match_id}/run", response_model=MatchStateResponse)
async def run_match(match_id: str) -> MatchStateResponse:
    state = match_service.get_match(match_id)
    state = await TurnRunner().run_match(state)
    return build_match_state_response(state)
