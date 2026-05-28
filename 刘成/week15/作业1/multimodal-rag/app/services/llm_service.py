import dashscope
from dashscope import Generation
from typing import Optional

from app.config import settings


class LLMService:
    """Qwen3 API for text generation"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.dashscope_api_key
        dashscope.api_key = self.api_key

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        model: str = "qwen3-4b",
    ) -> str:
        """Generate text using Qwen3 API"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = Generation.call(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            result_format={"type": "message"},
        )

        if response.status_code != 200:
            raise ValueError(f"LLM API error: {response.code} - {response.message}")

        return response.output["choices"][0]["message"]["content"]

    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        model: str = "qwen3-4b",
    ):
        """Generate text with streaming response"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = Generation.call(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
            result_format={"type": "message"},
        )

        for chunk in response:
            if chunk.status_code == 200:
                yield chunk.output["choices"][0]["message"]["content"]


llm_service = LLMService()
