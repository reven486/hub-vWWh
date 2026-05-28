import json
from urllib import error, request

from app.agents.base import BaseAgent
from app.agents.scripted.basic import ScriptedRoleAgent
from app.core.config import get_settings
from app.engine.enums import ActionType
from app.engine.models import ActionIntent, ObservationEnvelope
from app.services.prompt_builder import build_role_prompt


class LLMAgent(BaseAgent):
    def __init__(self, player_id: str):
        super().__init__(player_id)
        self._fallback = ScriptedRoleAgent(player_id)

    def act(self, envelope: ObservationEnvelope) -> ActionIntent:
        settings = get_settings().llm
        if not settings.api_key:
            return self._fallback.act(envelope)

        try:
            content = self._request_completion(build_role_prompt(envelope))
            payload = self._parse_json(content)
            action_type = ActionType(payload.get("action_type", ActionType.SKIP.value))
            target_id = payload.get("target_id") or None
            content_value = payload.get("content") or None
            return ActionIntent(
                player_id=envelope.player_id,
                action_type=action_type,
                target_id=target_id,
                content=content_value,
            )
        except Exception:
            return self._fallback.act(envelope)

    def _request_completion(self, prompt: str) -> str:
        settings = get_settings().llm
        body = json.dumps(
            {
                "model": settings.model,
                "messages": [
                    {"role": "system", "content": "你是狼人杀多智能体中的一个角色。你必须只输出合法 JSON。"},
                    {"role": "user", "content": prompt},
                ],
                "temperature": settings.temperature,
                "max_tokens": settings.max_tokens,
            },
            ensure_ascii=False,
        ).encode("utf-8")
        req = request.Request(
            url=f"{settings.base_url}/chat/completions",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.api_key}",
            },
            method="POST",
        )
        with request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        return payload["choices"][0]["message"]["content"]

    def _parse_json(self, content: str) -> dict:
        text = content.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
        if not text.startswith("{"):
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                text = text[start:end + 1]
        return json.loads(text)
