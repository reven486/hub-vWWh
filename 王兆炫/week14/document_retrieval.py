"""
本地知识库 — 文档检索（骨架）

不解析 PDF：知识库路径仅占位。在此处接入 Loader / 切分 / 向量库 / Retriever 等实现。
"""

from pathlib import Path

# 知识库根目录占位（可将 txt/md 等放入此目录后再实现加载逻辑）
KB_ROOT = Path(__file__).resolve().parent / "knowledge_base"


def retrieve_documents(query: str, *, top_k: int = 4) -> list[str]:
    """
    根据用户问题检索相关文档片段。

    :param query: 用户问题
    :param top_k: 返回片段条数上限
    :return: 与问题相关的文本片段列表（此处为空实现）
    """
    _ = (query, top_k, KB_ROOT)
    # TODO: 建索引 + 检索（如 LangChain Retriever），将 Document.page_content 收集为 str 列表
    return []


if __name__ == "__main__":
    chunks = retrieve_documents("示例问题", top_k=4)
    print("KB_ROOT =", KB_ROOT)
    print("chunks =", chunks)
