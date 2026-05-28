from app.engine.enums import ActionType, Phase, Role


SETUPS = {
    "standard_7": [
        Role.WEREWOLF,
        Role.WEREWOLF,
        Role.SEER,
        Role.WITCH,
        Role.VILLAGER,
        Role.VILLAGER,
        Role.VILLAGER,
    ]
}


PHASE_ACTIONS: dict[Phase, list[ActionType]] = {
    Phase.NIGHT_WEREWOLF: [ActionType.KILL, ActionType.SKIP],
    Phase.NIGHT_SEER: [ActionType.CHECK, ActionType.SKIP],
    Phase.NIGHT_WITCH: [ActionType.SAVE, ActionType.POISON, ActionType.SKIP],
    Phase.DAY_ANNOUNCEMENT: [],
    Phase.DAY_DISCUSSION: [ActionType.SPEAK],
    Phase.DAY_VOTE: [ActionType.VOTE],
    Phase.FINISHED: [],
}


PHASE_ROLES: dict[Phase, set[Role]] = {
    Phase.NIGHT_WEREWOLF: {Role.WEREWOLF},
    Phase.NIGHT_SEER: {Role.SEER},
    Phase.NIGHT_WITCH: {Role.WITCH},
    Phase.DAY_DISCUSSION: {Role.WEREWOLF, Role.SEER, Role.WITCH, Role.VILLAGER},
    Phase.DAY_VOTE: {Role.WEREWOLF, Role.SEER, Role.WITCH, Role.VILLAGER},
}
