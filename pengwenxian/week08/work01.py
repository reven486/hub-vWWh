import openai
from pydantic import BaseModel, Field


client = openai.OpenAI(
    api_key="sk-89beb5cc538544fc9ab0ad56bcf6f044", # https://bailian.console.aliyun.com/?tab=model#/api-key
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)


class CustomAgent:
    def __init__(self, model_name: str):
        self.model_name = model_name

    def call(self, user_prompt, response_model):
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "translate",
                    "description": "将用户输入的待翻译的文本从原始语种转换成目标语种",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "src_text": {
                                "description": "待翻译的文本",
                                "title": "Src Text",
                                "type": "string"
                            },
                            "dst_text": {
                                "description": "翻译后的文本",
                                "title": "Dst Text",
                                "type": "string"
                            },
                            "src_lang": {
                                "description": "原始语种",
                                "title": "Src Lang",
                                "type": "string"
                            },
                            "dst_lang": {
                                "description": "目标语种",
                                "title": "Dst Lang",
                                "type": "string"
                            }
                        },
                        "required": ["src_text", "dst_text", "src_lang", "dst_lang"]
                    }
                }
            }
        ]

        messages = [
            {
                "role": "user",
                "content": user_prompt
            }
        ]

        response = client.chat.completions.create(
            model="qwen-plus",
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        args = response.choices[0].message.tool_calls[0].function.arguments
        return response_model.model_validate_json(args)


class TranslateLanguage(BaseModel):
    """
    翻译语种的Pydantic模型
    """
    src_text: str = Field(description="待翻译的文本")
    dst_text: str = Field(description="翻译后的文本")
    src_lang: str = Field(description="原始语种")
    dst_lang: str = Field(description="目标语种")

result = CustomAgent = CustomAgent("qwen-plus").call("帮我将good！翻译为中文", TranslateLanguage)
print(result)
