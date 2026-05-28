"""文档摄入：加载 docs/ 中的本地文档，切分后写入 FAISS 向量库。

支持格式：.txt / .md / .pdf / .docx
"""
import shutil
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import (
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
)
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

BASE_DIR = Path(__file__).parent
DOCS_DIR = BASE_DIR / "docs"
VECTOR_STORE_DIR = BASE_DIR / "vector_store"

LOADERS = {
    ".txt": lambda p: TextLoader(p, encoding="utf-8"),
    ".md": lambda p: TextLoader(p, encoding="utf-8"),
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
}


def load_documents(docs_dir: Path):
    documents = []
    for path in sorted(docs_dir.rglob("*")):
        if not path.is_file():
            continue
        loader_factory = LOADERS.get(path.suffix.lower())
        if loader_factory is None:
            continue
        print(f"[load] {path.relative_to(docs_dir)}")
        documents.extend(loader_factory(str(path)).load())
    return documents


def main():
    if not DOCS_DIR.exists():
        DOCS_DIR.mkdir(parents=True)
        print(f"已创建 {DOCS_DIR}，请放入文档后重新运行。")
        return

    docs = load_documents(DOCS_DIR)
    if not docs:
        print("docs/ 下没有可识别的文档（支持 .txt/.md/.pdf/.docx）")
        return

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    print(f"共切分为 {len(chunks)} 个文本块")

    embeddings = DashScopeEmbeddings(model="text-embedding-v3")
    vector_store = FAISS.from_documents(chunks, embeddings)

    # FAISS 的 C++ I/O 在 Windows 上不支持非 ASCII 路径，先写入临时 ASCII 目录再迁移。
    VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="faiss_") as tmp:
        vector_store.save_local(tmp)
        for f in Path(tmp).iterdir():
            target = VECTOR_STORE_DIR / f.name
            if target.exists():
                target.unlink()
            shutil.move(str(f), str(target))
    print(f"向量库已保存到 {VECTOR_STORE_DIR}")


if __name__ == "__main__":
    main()
