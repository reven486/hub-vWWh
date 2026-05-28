from fastapi import APIRouter

from app.engine.visibility import VisibilityProjector
from app.services.match_service import match_service

router = APIRouter(prefix="/players", tags=["players"])


@router.get("/{match_id}/{player_id}")
async def get_player_view(match_id: str, player_id: str) -> dict:
    state = match_service.get_match(match_id)
    return VisibilityProjector.build_observation(state, player_id).model_dump(mode="json")
