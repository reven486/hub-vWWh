import json

from app.engine.models import ObservationEnvelope


def build_role_prompt(envelope: ObservationEnvelope) -> str:
    payload = {
        "player_id": envelope.player_id,
        "role": envelope.role.value,
        "phase": envelope.public_state.phase.value,
        "turn": envelope.public_state.turn,
        "alive_players": envelope.public_state.alive_players,
        "eliminated_players": envelope.public_state.eliminated_players,
        "recent_public_events": envelope.public_state.recent_public_events,
        "private_state": envelope.private_state,
        "action_space": [action.value for action in envelope.action_space],
    }
    return (
        "你在参加一局 AI 狼人杀。你只能根据给定观察信息行动，不能假设未提供的私密信息。"
        "\n你的目标是尽力帮助自己阵营获胜，同时输出一个严格 JSON 对象，不要输出 markdown，不要输出解释。"
        "\nJSON 格式固定为："
        '{"action_type":"<kill|check|save|poison|speak|vote|skip>","target_id":"<可为空>","content":"<仅 speak 时需要，其余可为空>"}'
        "\n规则："
        "\n1. action_type 必须来自 action_space。"
        "\n2. 如果不是 speak，content 置空字符串。"
        "\n3. 如果动作需要 target_id，就从 alive_players 中选择合法对象，且不能选择自己。"
        "\n4. 如果是 speak，请说一句自然、简短、符合当前局势的话，不要重复模板。"
        "\n5. 只返回 JSON。"
        f"\n观察信息如下：\n{json.dumps(payload, ensure_ascii=False)}"
    )
