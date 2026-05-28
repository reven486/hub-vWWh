import os
from typing import Any, Optional, cast

import openai
from pydantic import BaseModel, Field


def create_client() -> openai.OpenAI:
    """Create OpenAI-compatible client from environment variables."""
    api_key = (
        os.getenv("DEEPSEEK_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or "sk-bc3f2e9c549f422d93f28d6eb7005da3"
    )
    if not api_key:
        raise ValueError("请先设置环境变量 DEEPSEEK_API_KEY 或 OPENAI_API_KEY")

    base_url = os.getenv(
        "OPENAI_BASE_URL",
        "https://api.deepseek.com/v1",
    )
    return openai.OpenAI(api_key=api_key, base_url=base_url)


class TranslationRequest(BaseModel):
    """从用户输入中抽取翻译任务信息"""

    source_language: str = Field(description="原始语种，例如 中文、English、日本語")
    target_language: str = Field(description="目标语种，例如 英文、中文、法语")
    text: str = Field(description="待翻译的原始文本")


class ExtractionAgent:
    """使用 tools 自动抽取结构化参数"""

    def __init__(self, client: openai.OpenAI, model_name: str = "deepseek-chat"):
        self.client = client
        self.model_name = model_name

    def extract(
        self, user_prompt: str, response_model: type[TranslationRequest]
    ) -> Optional[TranslationRequest]:
        schema = response_model.model_json_schema()
        tools = [
            {
                "type": "function",
                "function": {
                    "name": schema["title"],
                    "description": schema.get("description", "extract structured fields"),
                    "parameters": {
                        "type": "object",
                        "properties": schema["properties"],
                        "required": schema.get("required", []),
                    },
                },
            }
        ]

        messages = [
            {
                "role": "system",
                "content": (
                    "你是翻译任务解析器。"
                    "从用户输入中提取 source_language、target_language、text。"
                    "如果语种未明确，结合语义推断最合理结果。"
                ),
            },
            {"role": "user", "content": user_prompt},
        ]

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=cast(Any, messages),
            tools=cast(Any, tools),
            tool_choice="auto",
        )

        try:
            tool_calls = response.choices[0].message.tool_calls
            if not tool_calls:
                return None
            arguments = cast(Any, tool_calls[0]).function.arguments
            return response_model.model_validate_json(arguments)
        except Exception:
            return None


class TranslationAgent:
    """先抽取参数，再执行翻译的智能体"""

    def __init__(self, client: openai.OpenAI, model_name: str = "deepseek-chat"):
        self.client = client
        self.model_name = model_name
        self.extractor = ExtractionAgent(client=client, model_name=model_name)

    def run(self, user_prompt: str) -> str:
        parsed = self.extractor.extract(user_prompt, TranslationRequest)
        if not parsed:
            return "无法识别翻译任务，请提供更明确的翻译要求。"

        translate_messages = [
            {
                "role": "system",
                "content": (
                    "你是专业翻译助手。"
                    "只输出翻译结果，不要解释。"
                    "保持原意，语气自然。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"请把下面文本从{parsed.source_language}翻译成{parsed.target_language}：\n"
                    f"{parsed.text}"
                ),
            },
        ]

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=cast(Any, translate_messages),
        )
        translation = (response.choices[0].message.content or "").strip()

        return (
            "=== 解析结果 ===\n"
            f"原始语种: {parsed.source_language}\n"
            f"目标语种: {parsed.target_language}\n"
            f"待翻译文本: {parsed.text}\n\n"
            "=== 翻译结果 ===\n"
            f"{translation}"
        )


if __name__ == "__main__":
    client = create_client()
    agent = TranslationAgent(client=client, model_name="deepseek-chat")

    examples = [
        "把这句话翻译成英文：今天天气真不错，我们去公园散步吧。",
        "Translate this into Chinese: I will send you the project report tomorrow.",
        "请把 '今日はとても忙しいですが、頑張ります。' 翻译成中文。",
    ]

    for idx, user_input in enumerate(examples, start=1):
        print(f"\n\n##### 示例 {idx} #####")
        print("用户输入:", user_input)
        print(agent.run(user_input))
