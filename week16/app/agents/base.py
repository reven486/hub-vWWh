from __future__ import annotations

from abc import ABC, abstractmethod

from app.engine.models import ActionIntent, ObservationEnvelope


class BaseAgent(ABC):
    def __init__(self, player_id: str):
        self.player_id = player_id

    @abstractmethod
    def act(self, envelope: ObservationEnvelope) -> ActionIntent:
        raise NotImplementedError
