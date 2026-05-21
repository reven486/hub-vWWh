import os
from openai import OpenAI
from typing import List, Optional
from app.config import settings
from app.core.retriever import RetrievalResult


class AnswerGenerator:
    """基于Qwen-VL API的答案生成器"""

    def __init__(self, api_key: Optional[str] = None):
        api_key = api_key or settings.QWEN_API_KEY
        base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def _build_prompt(self, query: str, contexts: List[RetrievalResult]) -> str:
        """构建提示词"""
        context_parts = []
        for ctx in contexts:
            if ctx.chunk_type == "text":
                context_parts.append(f"[文本] 页面{ctx.page}: {ctx.content[:200]}...")
            else:
                context_parts.append(f"[图像] 页面{ctx.page}: {ctx.content}")

        context_str = "\n".join(context_parts)

        prompt = f"""你是一个专业的文档问答助手。基于以下检索到的内容回答用户问题。

检索到的内容:
{context_str}

用户问题: {query}

请根据以上内容给出准确的答案。如果检索内容中没有明确答案，请说明"根据检索内容无法确定答案"。
答案中请引用信息来源（如"根据页面X的文本"或"根据页面X的图像"）。

答案:"""
        return prompt

    async def generate(
        self,
        query: str,
        contexts: List[RetrievalResult],
        model: str = "qwen3.6-flash"
    ) -> str:
        """
        调用Qwen-VL API生成答案

        Args:
            query: 用户问题
            contexts: 检索到的上下文
            model: 使用的模型

        Returns:
            str: 生成的答案
        """
        if not self.client.api_key:
            raise ValueError("QWEN_API_KEY is not set")

        prompt = self._build_prompt(query, contexts)

        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
        )

        return response.choices[0].message.content


def get_generator() -> AnswerGenerator:
    return AnswerGenerator()