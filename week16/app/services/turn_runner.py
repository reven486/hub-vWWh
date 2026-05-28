from __future__ import annotations

from app.agents.registry import build_agents
from app.core.config import get_settings
from app.engine.enums import ActionType, Phase
from app.engine.models import ActionIntent, GameEvent, GameState
from app.engine.resolver import apply_night_action, resolve_night, resolve_votes
from app.engine.validator import validate_action
from app.engine.visibility import VisibilityProjector
from app.engine.win_conditions import detect_winner
from app.observability.event_logger import log_event
from app.storage.repositories import persist_state


class TurnRunner:
    async def run_match(self, state: GameState) -> GameState:
        max_turns = get_settings().game.max_turns
        while state.phase != Phase.FINISHED and state.turn <= max_turns:
            await self.step_match(state)

        if state.phase != Phase.FINISHED:
            state.winner = detect_winner(state) or "draw"
            await self._finish_match(state)
        return state

    async def step_match(self, state: GameState) -> GameState:
        if state.phase == Phase.FINISHED:
            return state

        if state.turn > get_settings().game.max_turns:
            state.winner = detect_winner(state) or "draw"
            await self._finish_match(state)
            return state

        agents = build_agents(state)

        if state.phase == Phase.NIGHT_WEREWOLF:
            await self._run_night_phase(state, agents, Phase.NIGHT_WEREWOLF)
            state.phase = Phase.NIGHT_SEER
            await persist_state(state)
            return state

        if state.phase == Phase.NIGHT_SEER:
            await self._run_night_phase(state, agents, Phase.NIGHT_SEER)
            state.phase = Phase.NIGHT_WITCH
            await persist_state(state)
            return state

        if state.phase == Phase.NIGHT_WITCH:
            await self._run_night_phase(state, agents, Phase.NIGHT_WITCH)
            deaths = resolve_night(state)
            for dead_id in deaths:
                log_event(state, GameEvent(match_id=state.match_id, turn=state.turn, phase=Phase.DAY_ANNOUNCEMENT, event_type="player.eliminated", visibility="public", target_player_id=dead_id, payload={"reason": "night"}))
            winner = detect_winner(state)
            if winner:
                state.winner = winner
                await self._finish_match(state)
                return state
            state.phase = Phase.DAY_DISCUSSION
            await persist_state(state)
            return state

        if state.phase == Phase.DAY_DISCUSSION:
            await self._run_discussion_phase(state, agents)
            state.phase = Phase.DAY_VOTE
            await persist_state(state)
            return state

        if state.phase == Phase.DAY_VOTE:
            await self._run_vote_phase(state, agents)
            winner = detect_winner(state)
            if winner:
                state.winner = winner
                await self._finish_match(state)
                return state
            state.turn += 1
            if state.turn > get_settings().game.max_turns:
                state.winner = "draw"
                await self._finish_match(state)
                return state
            state.phase = Phase.NIGHT_WEREWOLF
            await persist_state(state)
            return state

        return state

    async def _run_night_phase(self, state: GameState, agents: dict[str, object], phase: Phase) -> None:
        self._start_phase(state, phase)
        for player in state.alive_players():
            envelope = VisibilityProjector.build_observation(state, player.player_id)
            if not envelope.action_space:
                continue
            action = agents[player.player_id].act(envelope)
            self._record_action_event(state, player.player_id, action)
            try:
                validate_action(state, action)
            except Exception as exc:
                log_event(state, GameEvent(match_id=state.match_id, turn=state.turn, phase=phase, event_type="action.rejected", visibility="internal", actor_player_id=player.player_id, role=player.role, payload={"reason": str(exc)}))
                continue
            apply_night_action(state, action)

    async def _run_discussion_phase(self, state: GameState, agents: dict[str, object]) -> None:
        self._start_phase(state, Phase.DAY_DISCUSSION)
        for player in state.alive_players():
            action = agents[player.player_id].act(VisibilityProjector.build_observation(state, player.player_id))
            if action.action_type == ActionType.SPEAK:
                log_event(state, GameEvent(match_id=state.match_id, turn=state.turn, phase=state.phase, event_type="player.spoke", visibility="public", actor_player_id=player.player_id, role=player.role, payload={"content": action.content or ""}))

    async def _run_vote_phase(self, state: GameState, agents: dict[str, object]) -> None:
        self._start_phase(state, Phase.DAY_VOTE)
        votes: list[ActionIntent] = []
        for player in state.alive_players():
            action = agents[player.player_id].act(VisibilityProjector.build_observation(state, player.player_id))
            self._record_action_event(state, player.player_id, action)
            try:
                validate_action(state, action)
            except Exception:
                continue
            if action.action_type == ActionType.VOTE:
                votes.append(action)
        eliminated = resolve_votes(votes)
        if eliminated:
            state.get_player(eliminated).alive = False
            log_event(state, GameEvent(match_id=state.match_id, turn=state.turn, phase=state.phase, event_type="player.eliminated", visibility="public", target_player_id=eliminated, payload={"reason": "vote"}))

    def _start_phase(self, state: GameState, phase: Phase) -> None:
        state.phase = phase
        log_event(state, GameEvent(match_id=state.match_id, turn=state.turn, phase=phase, event_type="phase.started", visibility="public", payload={}))

    async def _finish_match(self, state: GameState) -> None:
        if state.phase == Phase.FINISHED:
            return
        state.phase = Phase.FINISHED
        log_event(
            state,
            GameEvent(
                match_id=state.match_id,
                turn=state.turn,
                phase=state.phase,
                event_type="match.finished",
                visibility="public",
                payload={"winner": state.winner},
            ),
        )
        await persist_state(state)

    def _record_action_event(self, state: GameState, player_id: str, action: ActionIntent) -> None:
        player = state.get_player(player_id)
        log_event(state, GameEvent(match_id=state.match_id, turn=state.turn, phase=state.phase, event_type="agent.action_returned", visibility="internal", actor_player_id=player_id, role=player.role, payload=action.model_dump(mode="json")))
