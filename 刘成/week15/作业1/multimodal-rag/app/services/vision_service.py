import dashscope
from dashscope import MultiModalConversation
from typing import Optional

from app.config import settings


class VisionService:
    """Qwen-VL API for image understanding"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.dashscope_api_key
        dashscope.api_key = self.api_key

    def describe_image(
        self,
        image_base64: str,
        prompt: str = "请描述这张图片的内容。",
        model: str = "qwen-vl-plus",
    ) -> str:
        """Generate a description of an image using Qwen-VL"""
        messages = [
            {
                "role": "user",
                "content": [
                    {"image": f"data:image/png;base64,{image_base64}"},
                    {"text": prompt},
                ],
            }
        ]

        response = MultiModalConversation.call(
            model=model,
            messages=messages,
        )

        if response.status_code != 200:
            raise ValueError(f"Vision API error: {response.code} - {response.message}")

        return response.output["choices"][0]["message"]["content"]

    def answer_about_image(
        self,
        image_base64: str,
        question: str,
        model: str = "qwen-vl-plus",
    ) -> str:
        """Answer a question about an image using Qwen-VL"""
        messages = [
            {
                "role": "user",
                "content": [
                    {"image": f"data:image/png;base64,{image_base64}"},
                    {"text": question},
                ],
            }
        ]

        response = MultiModalConversation.call(
            model=model,
            messages=messages,
        )

        if response.status_code != 200:
            raise ValueError(f"Vision API error: {response.code} - {response.message}")

        return response.output["choices"][0]["message"]["content"]


vision_service = VisionService()
