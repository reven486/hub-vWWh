# 本地知识库问答

两阶段：**文档检索** → **LLM 回答**。

## 目录

| 文件 / 目录 | 作用 |
|-------------|------|
| `knowledge_base/` | 本地语料占位目录（后续可放 txt/md 等） |
| `document_retrieval.py` | 子问题一：按问题检索文档片段 |
| `llm_answer.py` | 子问题二：根据片段与问题调用大模型生成答案 |

## 串联方式

1. `retrieve_documents(question)` 得到 `list[str]`。  
2. `answer(question, context_chunks)` 得到最终回复。

示例见各文件末尾 `if __name__ == "__main__":`。

## 依赖（自行安装）

与 Week14 LangChain 教程一致即可，例如：`langchain-core`、`langchain-openai` 等；检索侧后续若用向量库再增加对应包。

## 说明

中间实现（加载、切分、向量索引、具体模型名与密钥）在代码中以 `TODO` 标出，按课程要求补全即可。
