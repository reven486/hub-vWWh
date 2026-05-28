from collections import Counter

from app.engine.enums import ActionType
from app.engine.models import ActionIntent, GameState


def apply_night_action(state: GameState, action: ActionIntent) -> None:
    player = state.get_player(action.player_id)
    if action.action_type == ActionType.KILL:
        state.pending_night_kill = action.target_id
    elif action.action_type == ActionType.CHECK and action.target_id:
        target = state.get_player(action.target_id)
        player.seer_checks[target.player_id] = target.role
    elif action.action_type == ActionType.SAVE:
        state.pending_save_target = state.pending_night_kill
        player.witch_save_available = False
    elif action.action_type == ActionType.POISON and action.target_id:
        state.pending_poison_target = action.target_id
        player.witch_poison_available = False


def resolve_night(state: GameState) -> list[str]:
    deaths: list[str] = []
    if state.pending_night_kill and state.pending_night_kill != state.pending_save_target:
        deaths.append(state.pending_night_kill)
    if state.pending_poison_target and state.pending_poison_target not in deaths:
        deaths.append(state.pending_poison_target)

    for player_id in deaths:
        state.get_player(player_id).alive = False

    state.pending_night_kill = None
    state.pending_save_target = None
    state.pending_poison_target = None
    return deaths


def resolve_votes(actions: list[ActionIntent]) -> str | None:
    votes = [action.target_id for action in actions if action.target_id]
    if not votes:
        return None
    ranked = Counter(votes).most_common()
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        return None
    return ranked[0][0]
