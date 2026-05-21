import base64
from pathlib import Path
from openai import AsyncOpenAI
from app.core.config import get_settings


def _get_client() -> AsyncOpenAI:
    settings = get_settings()
    return AsyncOpenAI(api_key=settings.llm.api_key, base_url=settings.llm.base_url)


def _image_to_data_url(image_path: str) -> str | None:
    path = Path(image_path)
    if not path.exists():
        return None
    suffix = path.suffix.lower()
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".gif": "image/gif"}.get(
        suffix, "image/png"
    )
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return f"data:{mime};base64,{data}"


def _build_messages(question: str, text_chunks: list[dict], image_chunks: list[dict]) -> list[dict]:
    system_msg = {
        "role": "system",
        "content": (
            "你是一个多模态文档问答助手。根据提供的文本段落和图像，回答用户问题。"
            "回答要准确、简洁，并在答案末尾注明信息来源（文档名称、页码、图表编号）。"
        ),
    }

    context_parts: list = []
    if text_chunks:
        context_parts.append({"type": "text", "text": "【相关文本段落】\n"})
        for chunk in text_chunks:
            label = chunk.get("source_label", "")
            content = chunk.get("content", "")
            context_parts.append({"type": "text", "text": f"[{label}]\n{content}\n\n"})

    if image_chunks:
        context_parts.append({"type": "text", "text": "【相关图像】\n"})
        for chunk in image_chunks:
            label = chunk.get("source_label", "")
            image_path = chunk.get("image_path", "")
            data_url = _image_to_data_url(image_path) if image_path else None
            context_parts.append({"type": "text", "text": f"[{label}]\n"})
            if data_url:
                context_parts.append({"type": "image_url", "image_url": {"url": data_url}})

    context_parts.append({"type": "text", "text": f"\n【用户问题】\n{question}"})

    user_msg = {"role": "user", "content": context_parts}
    return [system_msg, user_msg]


async def generate_answer(
    question: str, text_chunks: list[dict], image_chunks: list[dict]
) -> str:
    settings = get_settings()
    client = _get_client()
    messages = _build_messages(question, text_chunks, image_chunks)
    response = await client.chat.completions.create(
        model=settings.llm.model,
        messages=messages,
        max_tokens=settings.llm.max_tokens,
        temperature=settings.llm.temperature,
    )
    return response.choices[0].message.content or ""
