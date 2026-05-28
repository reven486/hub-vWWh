from fastapi import APIRouter

from app.models import ReplayResponse
from app.services.replay_service import replay_service

router = APIRouter(prefix="/replay", tags=["replay"])


@router.get("/{match_id}", response_model=ReplayResponse)
async def get_public_replay(match_id: str) -> ReplayResponse:
    return ReplayResponse(match_id=match_id, events=replay_service.get_public_replay(match_id))


@router.get("/{match_id}/full", response_model=ReplayResponse)
async def get_full_replay(match_id: str) -> ReplayResponse:
    return ReplayResponse(match_id=match_id, events=replay_service.get_full_replay(match_id))
