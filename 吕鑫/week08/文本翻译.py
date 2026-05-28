from pydantic import BaseModel, Field
from typing_extensions import Literal

import openai

client = openai.OpenAI(
    api_key="sk-35609c8a5c4e42c6bc8b38888615c54b",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)


class ExtractionAgent:
    def __init__(self, model_name: str):
        self.model_name = model_name

    def call(self, user_prompt, response_model):
        schema = response_model.model_json_schema()
        messages = [
            {
                "role": "system",
                "content": "你是信息抽取助手。你必须调用工具，并准确提取用户请求中的结构化字段。若用户没有明确说明原始语种，请填写“自动识别”。",
            },
            {
                "role": "user",
                "content": user_prompt,
            }
        ]

        tools = [
            {
                "type": "function",
                "function": {
                    "name": schema["title"],
                    "description": schema["description"],
                    "parameters": {
                        "type": "object",
                        "properties": schema["properties"],
                        "required": schema["required"],
                    },
                },
            }
        ]

        response = client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            tools=tools,
            tool_choice={"type": "function", "function": {"name": schema["title"]}},
        )

        try:
            tool_calls = response.choices[0].message.tool_calls
            if not tool_calls:
                print("ERROR", response.choices[0].message)
                return None
            arguments = tool_calls[0].function.arguments
            return response_model.model_validate_json(arguments)
        except Exception:
            print("ERROR", response.choices[0].message)
            return None


class TranslationTask(BaseModel):
    """识别用户翻译请求中的原始语种、目标语种和待翻译文本"""

    source_language: Literal["中文", "英文", "日文", "韩文", "越南语", "法文", "德文", "西班牙文", "自动识别"] = Field(
        description="原始语种，如果用户没有明确说明，则根据文本内容自动识别"
    )
    target_language: Literal["中文", "英文", "日文", "韩文", "越南语", "法文", "德文", "西班牙文"] = Field(
        description="目标语种"
    )
    text: str = Field(description="待翻译的原始文本")


class TranslationAgent:
    def __init__(self, model_name: str = "qwen-plus"):
        self.model_name = model_name
        self.extraction_agent = ExtractionAgent(model_name)

    def extract_task(self, user_prompt: str):
        return self.extraction_agent.call(user_prompt, TranslationTask)

    def translate(self, task: TranslationTask):
        response = client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个专业翻译助手。只输出翻译结果，不要输出解释。",
                },
                {
                    "role": "user",
                    "content": f"请把下面的文本从{task.source_language}翻译成{task.target_language}：{task.text}",
                },
            ],
        )
        return response.choices[0].message.content

    def run(self, user_prompt: str):
        task = self.extract_task(user_prompt)
        if task is None:
            return None, None
        translated_text = self.translate(task)
        return task, translated_text


agent = TranslationAgent(model_name="qwen-plus")
user_prompt = "帮我把안녕 세계翻译成法语"

result, translated_text = agent.run(user_prompt)

if result is None:
    print("信息抽取失败，请检查提示词或模型返回结果。")
else:
    print("原始语种:", result.source_language)
    print("目标语种:", result.target_language)
    print("待翻译的文本:", result.text)
    print("翻译结果:", translated_text)
