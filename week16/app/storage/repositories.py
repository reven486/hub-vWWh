from app.engine.models import GameState
from app.storage.sqlite import replace_players, upsert_match


async def persist_state(state: GameState) -> None:
    status = "finished" if state.winner else "running"
    await upsert_match(state.match_id, status, state.turn, state.phase.value, state.winner)
    await replace_players(
        state.match_id,
        [
            {
                "id": player.player_id,
                "name": player.name,
                "role": player.role.value,
                "alive": player.alive,
                "seat": player.seat,
            }
            for player in state.players
        ],
    )
