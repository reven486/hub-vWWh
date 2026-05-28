from app.services.match_service import match_service
from app.services.turn_runner import TurnRunner


class SimulationService:
    async def run_single(self) -> dict:
        state = await match_service.create_match()
        state = await TurnRunner().run_match(state)
        return {"match_id": state.match_id, "winner": state.winner, "turn": state.turn}


simulation_service = SimulationService()
