from app.agents.base import BaseAgent
from app.agents.llm_agent import LLMAgent
from app.engine.models import GameState


def build_agents(state: GameState) -> dict[str, BaseAgent]:
    return {player.player_id: LLMAgent(player.player_id) for player in state.players}
