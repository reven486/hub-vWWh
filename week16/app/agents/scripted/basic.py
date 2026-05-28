from app.agents.base import BaseAgent
from app.engine.enums import ActionType, Role
from app.engine.models import ActionIntent, ObservationEnvelope


class ScriptedRoleAgent(BaseAgent):
    def act(self, envelope: ObservationEnvelope) -> ActionIntent:
        alive_players = [player_id for player_id in envelope.public_state.alive_players if player_id != envelope.player_id]
        if ActionType.KILL in envelope.action_space:
            non_wolves = [pid for pid in alive_players if pid not in envelope.private_state.get("known_wolves", [])]
            target = non_wolves[0] if non_wolves else alive_players[0]
            return ActionIntent(player_id=envelope.player_id, action_type=ActionType.KILL, target_id=target)
        if ActionType.CHECK in envelope.action_space:
            checked = set(envelope.private_state.get("seer_checks", {}).keys())
            options = [pid for pid in alive_players if pid not in checked]
            target = options[0] if options else alive_players[0]
            return ActionIntent(player_id=envelope.player_id, action_type=ActionType.CHECK, target_id=target)
        if ActionType.SAVE in envelope.action_space and envelope.private_state.get("witch_save_available") and envelope.private_state.get("night_victim"):
            return ActionIntent(player_id=envelope.player_id, action_type=ActionType.SAVE)
        if ActionType.POISON in envelope.action_space and envelope.private_state.get("witch_poison_available"):
            known_checks = envelope.private_state.get("seer_checks", {})
            wolves = [pid for pid, role in known_checks.items() if role == Role.WEREWOLF]
            if wolves:
                return ActionIntent(player_id=envelope.player_id, action_type=ActionType.POISON, target_id=wolves[0])
        if ActionType.SPEAK in envelope.action_space:
            return ActionIntent(player_id=envelope.player_id, action_type=ActionType.SPEAK, content=f"我是 {envelope.player_id}，当前优先关注发言和投票一致性。")
        if ActionType.VOTE in envelope.action_space:
            target = alive_players[0] if alive_players else None
            return ActionIntent(player_id=envelope.player_id, action_type=ActionType.VOTE, target_id=target)
        return ActionIntent(player_id=envelope.player_id, action_type=ActionType.SKIP)
