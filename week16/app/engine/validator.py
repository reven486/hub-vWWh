from app.core.exceptions import InvalidActionError
from app.engine.enums import ActionType, Phase, Role
from app.engine.models import ActionIntent, GameState


def validate_action(state: GameState, action: ActionIntent) -> None:
    player = state.get_player(action.player_id)
    if not player.alive:
        raise InvalidActionError("dead players cannot act")

    if state.phase == Phase.NIGHT_WEREWOLF and player.role != Role.WEREWOLF:
        raise InvalidActionError("only werewolves can act now")
    if state.phase == Phase.NIGHT_SEER and player.role != Role.SEER:
        raise InvalidActionError("only seer can act now")
    if state.phase == Phase.NIGHT_WITCH and player.role != Role.WITCH:
        raise InvalidActionError("only witch can act now")

    if action.action_type in {ActionType.KILL, ActionType.CHECK, ActionType.POISON, ActionType.VOTE} and not action.target_id:
        raise InvalidActionError("target_id is required")
    if action.action_type == ActionType.SAVE and not state.pending_night_kill:
        raise InvalidActionError("no victim to save")
    if action.target_id == action.player_id and action.action_type in {ActionType.KILL, ActionType.POISON, ActionType.VOTE}:
        raise InvalidActionError("cannot target self")

    if action.target_id:
        target = state.get_player(action.target_id)
        if not target.alive and action.action_type in {ActionType.KILL, ActionType.POISON, ActionType.VOTE, ActionType.CHECK}:
            raise InvalidActionError("target must be alive")
