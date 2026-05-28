from app.agents.base import BaseAgent
from app.engine.enums import ActionType
from app.engine.models import ActionIntent, ObservationEnvelope


class HumanProxyAgent(BaseAgent):
    def act(self, envelope: ObservationEnvelope) -> ActionIntent:
        return ActionIntent(player_id=envelope.player_id, action_type=ActionType.SKIP)
