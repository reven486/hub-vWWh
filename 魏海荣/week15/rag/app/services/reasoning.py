from typing import List, Dict, Any, Optional
from openai import OpenAI
from app.core.config import config
from app.models.schemas import SourceInfo


class ReasoningService:
    def __init__(self):
        self._client = None

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            models_config = config.models.get("llm", {})
            self._client = OpenAI(
                api_key=models_config.get("api_key", ""),
                base_url=models_config.get("api_base", "https://api.openai.com/v1")
            )
        return self._client

    def generate_answer(
        self,
        query: str,
        text_contents: List[Dict[str, Any]],
        image_contents: List[Dict[str, Any]]
    ) -> tuple[str, List[SourceInfo]]:
        prompt = self._build_prompt(query, text_contents, image_contents)
        model_name = config.models.get("llm", {}).get("model_name", "qwen-plus")

        response = self.client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "你是一个专业的多模态文档问答助手。请根据提供的上下文信息回答用户的问题。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )

        answer = response.choices[0].message.content
        sources = self._extract_sources(text_contents, image_contents)
        return answer, sources

    def _build_prompt(
        self,
        query: str,
        text_contents: List[Dict[str, Any]],
        image_contents: List[Dict[str, Any]]
    ) -> str:
        prompt_parts = [f"用户问题: {query}\n\n"]

        if text_contents:
            prompt_parts.append("【文本信息】\n")
            for i, item in enumerate(text_contents, 1):
                prompt_parts.append(f"{i}. {item.get('content', '')} (来源: {item.get('source', '未知')})\n")

        if image_contents:
            prompt_parts.append("\n【图像信息】\n")
            for i, item in enumerate(image_contents, 1):
                prompt_parts.append(f"{i}. 图表 {item.get('chart_id', '未知')} (来源: {item.get('source', '未知')})\n")

        prompt_parts.append("\n请基于以上信息生成准确、简洁的回答，并注明信息来源。")
        return "".join(prompt_parts)

    def _extract_sources(
        self,
        text_contents: List[Dict[str, Any]],
        image_contents: List[Dict[str, Any]]
    ) -> List[SourceInfo]:
        sources = []
        for item in text_contents:
            sources.append(SourceInfo(
                pdf_name=item.get("pdf_name", "未知"),
                page=item.get("page")
            ))
        for item in image_contents:
            sources.append(SourceInfo(
                pdf_name=item.get("pdf_name", "未知"),
                page=item.get("page"),
                chart_id=item.get("chart_id")
            ))
        return sources


reasoning_service = ReasoningService()
