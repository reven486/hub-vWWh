from app.engine.enums import Role
from app.engine.models import GameState


def detect_winner(state: GameState) -> str | None:
    alive = state.alive_players()
    wolves = [player for player in alive if player.role == Role.WEREWOLF]
    villagers = [player for player in alive if player.role != Role.WEREWOLF]
    if not wolves:
        return "villagers"
    if len(wolves) >= len(villagers):
        return "werewolves"
    return None
