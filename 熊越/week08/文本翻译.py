from openai import OpenAI
import time
from pydantic import BaseModel, Field
from typing import List, Optional
from typing_extensions import Literal

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy"  # vLLM不需要真实API key
)


class ExtractionAgent:
    def __init__(self, model_name: str):
        self.model_name = model_name

    def call(self, user_prompt, response_model, system_prompt: Optional[str] = None):
        messages = []

        # 添加系统提示词（如果有）
        # if system_prompt:
        #     messages.append({
        #         "role": "system",
        #         "content": system_prompt
        #     })

        messages.append({
            "role": "user",
            "content": user_prompt
        })

        # 传入需要提取的内容，自己写了一个tool格式
        tools = [
            {
                "type": "function",
                "function": {
                    "name": response_model.model_json_schema()['title'],
                    "description": response_model.model_json_schema()['description'],
                    "parameters": {
                        "type": "object",
                        "properties": response_model.model_json_schema()['properties'],
                        "required": response_model.model_json_schema()['required'],
                    },
                }
            }
        ]

        response = client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            tools=tools,
            tool_choice={"type": "function", "function": {"name": response_model.model_json_schema()['title']}},
        )

        try:
            # 提取的参数（json格式）
            arguments = response.choices[0].message.tool_calls[0].function.arguments
            # 参数转换为datamodel
            return response_model.model_validate_json(arguments)
        except Exception as e:
            print(f'ERROR: {e}')
            print('Response:', response.choices[0].message)
            return None


# 使用示例#
class Text(BaseModel):
    """文本问答内容解析"""
    original_text: str = Field(description="原始文本")
    translated_text: str = Field(description="翻译后的文本")
    confidence: List[str] = Field(description="置性度，0-1之间")
result = ExtractionAgent(model_name = "qwen3.5-0.8b").call('请翻译为中文：good!', Text)
print(result)
