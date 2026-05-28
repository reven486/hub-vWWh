class GameError(Exception):
    pass


class MatchNotFoundError(GameError):
    pass


class InvalidActionError(GameError):
    pass
