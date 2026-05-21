# import dashscope
#
# text = "通用多模态表征模型示例"
# input = [{'text': text}]
# resp = dashscope.MultiModalEmbedding.call(
#     model="qwen3-vl-embedding",
#     input=input
# )
#
# print(resp)
from app.core.embedder import TextEmbedder
import asyncio


async def test():
    embedder = TextEmbedder()
    result = await embedder.embed_texts(['测试文本'])
    print('Embedding shape:', result.shape)


asyncio.run(test())