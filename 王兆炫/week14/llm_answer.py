"""
本地知识库 — LLM 回答（骨架）

仅负责：把「检索到的上下文 + 用户问题」交给大模型生成回答。模型与 Prompt 细节在此补全。
"""

from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI


def build_messages(question: str, context_chunks: list[str]) -> list:
    """拼装系统提示与用户消息（可按作业要求调整拒答策略等）。"""
    context_block = "\n\n---\n\n".join(context_chunks) if context_chunks else "（当前无检索到参考资料）"
    system = (
        "你是严谨的问答助手。请仅根据「参考资料」回答用户问题；"
        "若资料不足以回答，请明确说明无法从资料中得出答案。"
    )
    user = f"参考资料：\n{context_block}\n\n用户问题：\n{question}"
    return [SystemMessage(content=system), HumanMessage(content=user)]


def answer(question: str, context_chunks: list[str], llm: Optional[ChatOpenAI] = None) -> str:
    """
    基于检索片段生成回答。

    :param question: 用户问题
    :param context_chunks: `document_retrieval.retrieve_documents` 的返回结果
    :param llm: 可选，外部注入已配置好的 ChatOpenAI；为 None 时使用占位默认参数（需自行配置环境变量）
    :return: 模型回复正文
    """
    messages = build_messages(question, context_chunks)
    if llm is None:
        # TODO: 与 Week14 教程一致，从环境变量读取 base_url / api_key / model
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    response = llm.invoke(messages)
    return response.content


if __name__ == "__main__":
    from document_retrieval import retrieve_documents

    q = "示例问题"
    ctx = retrieve_documents(q, top_k=4)
    # 需要有效 API 与网络时再取消注释
    # print(answer(q, ctx))
