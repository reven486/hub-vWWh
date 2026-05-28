from typing import Optional
class Text(BaseModel):
    """翻译请求解析器"""
    source_text: str = Field(description="需要翻译的原文")
    source_language: Optional[str] = Field(description="源语言，如不指定则自动检测")
    target_language: Optional[str] = Field(description="目标语言，从用户的提问中推测")
    result:str = Field(description="翻译的结果，用推测出来的目标语言")
    
result = ExtractionAgent(model_name = "qwen-plus").call('请翻译:China is a beautiful place', Text)
print(result)

result = ExtractionAgent(model_name = "qwen-plus").call('Please Translate:中国是一个美丽的地方', Text)
print(result)
