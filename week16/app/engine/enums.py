from enum import Enum


class Role(str, Enum):
    WEREWOLF = "werewolf"
    SEER = "seer"
    WITCH = "witch"
    VILLAGER = "villager"


class Phase(str, Enum):
    NIGHT_WEREWOLF = "night_werewolf"
    NIGHT_SEER = "night_seer"
    NIGHT_WITCH = "night_witch"
    DAY_ANNOUNCEMENT = "day_announcement"
    DAY_DISCUSSION = "day_discussion"
    DAY_VOTE = "day_vote"
    FINISHED = "finished"


class ActionType(str, Enum):
    KILL = "kill"
    CHECK = "check"
    SAVE = "save"
    POISON = "poison"
    SPEAK = "speak"
    VOTE = "vote"
    SKIP = "skip"
