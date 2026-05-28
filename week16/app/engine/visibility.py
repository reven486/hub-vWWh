from app.engine.enums import ActionType, Phase, Role
from app.engine.models import GameState, ObservationEnvelope, PublicGameState
from app.engine.rules import PHASE_ACTIONS


class VisibilityProjector:
    @staticmethod
    def build_observation(state: GameState, player_id: str) -> ObservationEnvelope:
        player = state.get_player(player_id)
        public_state = PublicGameState(
            turn=state.turn,
            phase=state.phase,
            alive_players=[alive.player_id for alive in state.alive_players()],
            eliminated_players=state.eliminated_player_ids(),
            recent_public_events=[event.model_dump(mode="json") for event in state.events if event.visibility == "public"][-8:],
        )

        private_state: dict[str, object] = {}
        if player.role == Role.WEREWOLF:
            private_state["known_wolves"] = list(player.known_wolves)
        if player.role == Role.SEER:
            private_state["seer_checks"] = dict(player.seer_checks)
        if player.role == Role.WITCH:
            private_state["witch_save_available"] = player.witch_save_available
            private_state["witch_poison_available"] = player.witch_poison_available
            if state.pending_night_kill:
                private_state["night_victim"] = state.pending_night_kill

        action_space = []
        if player.alive:
            if state.phase == Phase.NIGHT_WEREWOLF and player.role == Role.WEREWOLF:
                action_space = PHASE_ACTIONS[state.phase]
            elif state.phase == Phase.NIGHT_SEER and player.role == Role.SEER:
                action_space = PHASE_ACTIONS[state.phase]
            elif state.phase == Phase.NIGHT_WITCH and player.role == Role.WITCH:
                action_space = PHASE_ACTIONS[state.phase]
            elif state.phase == Phase.DAY_DISCUSSION:
                action_space = [ActionType.SPEAK]
            elif state.phase == Phase.DAY_VOTE:
                action_space = [ActionType.VOTE]

        return ObservationEnvelope(
            player_id=player.player_id,
            role=player.role,
            public_state=public_state,
            private_state=private_state,
            action_space=action_space,
        )
