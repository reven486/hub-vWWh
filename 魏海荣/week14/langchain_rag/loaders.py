"""
文档加载模块 (Loaders)

提供统一的文档加载接口，支持多种文件格式：
- PDF 文档 (.pdf)
- HTML 文档 (.html, .htm)
- 文本文件 (.txt)

使用 LangChain v1 的 document_loaders 组件。

参考：
- https://python.langchain.com/docs/concepts/document_loaders/
"""

import os
from pathlib import Path
from typing import Optional, Union, List

from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    BSHTMLLoader,
    UnstructuredMarkdownLoader,
    CSVLoader,
)
from langchain_core.documents import Document

from config import settings, get_logger

logger = get_logger(__name__)


# 支持的文件类型及对应加载器
LOADER_MAPPING = {
    ".pdf": PyPDFLoader,
    ".html": BSHTMLLoader,
    ".htm": BSHTMLLoader,
    ".txt": TextLoader,
    ".md": UnstructuredMarkdownLoader,
    ".csv": CSVLoader,
}


def create_loader(file_path: str) -> Optional[object]:
    """
    根据文件扩展名创建对应的加载器

    Args:
        file_path: 文件路径

    Returns:
        对应的 Loader 实例，None 表示不支持该文件类型

    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 不支持的文件类型
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    if ext not in LOADER_MAPPING:
        logger.warning(f"不支持的文件类型: {ext}, 文件: {file_path}")
        return None

    loader_class = LOADER_MAPPING[ext]

    # TextLoader 需要指定编码
    if ext == ".txt":
        return loader_class(file_path, encoding="utf-8")

    return loader_class(file_path)


def load_file(file_path: str) -> List[Document]:
    """
    加载单个文件

    Args:
        file_path: 文件路径

    Returns:
        Document 列表

    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 不支持的文件类型
    """
    logger.debug(f"加载文件: {file_path}")

    loader = create_loader(file_path)
    if loader is None:
        raise ValueError(f"不支持的文件类型: {os.path.splitext(file_path)[1]}")

    try:
        docs = loader.load()
        logger.info(f"✅ 成功加载文件: {file_path}, 获取 {len(docs)} 个文档块")
        return docs
    except Exception as e:
        logger.error(f"❌ 加载文件失败: {file_path}, 错误: {e}")
        raise


def load_directory(
    directory_path: str,
    recursive: bool = True,
    load_hidden: bool = False,
    show_progress: bool = True,
) -> List[Document]:
    """
    加载目录下的所有支持的文件

    Args:
        directory_path: 目录路径
        recursive: 是否递归搜索子目录
        load_hidden: 是否加载隐藏文件
        show_progress: 是否显示加载进度

    Returns:
        所有加载的 Document 列表
    """
    if not os.path.exists(directory_path):
        raise FileNotFoundError(f"目录不存在: {directory_path}")

    if not os.path.isdir(directory_path):
        raise ValueError(f"不是有效的目录: {directory_path}")

    all_docs = []
    supported_exts = set(LOADER_MAPPING.keys())

    logger.info(f"开始扫描目录: {directory_path}, 递归: {recursive}")

    if recursive:
        for root, dirs, files in os.walk(directory_path):
            # 过滤隐藏目录
            if not load_hidden:
                dirs[:] = [d for d in dirs if not d.startswith(".")]

            for file in files:
                # 过滤隐藏文件
                if not load_hidden and file.startswith("."):
                    continue

                file_path = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()

                if ext in supported_exts:
                    try:
                        docs = load_file(file_path)
                        all_docs.extend(docs)
                    except Exception as e:
                        logger.warning(f"跳过文件 {file_path}: {e}")
    else:
        # 非递归模式
        for file in os.listdir(directory_path):
            file_path = os.path.join(directory_path, file)
            if os.path.isfile(file_path):
                ext = os.path.splitext(file)[1].lower()
                if ext in supported_exts:
                    try:
                        docs = load_file(file_path)
                        all_docs.extend(docs)
                    except Exception as e:
                        logger.warning(f"跳过文件 {file_path}: {e}")

    logger.info(f"📂 目录加载完成: 共加载 {len(all_docs)} 个文档块")
    return all_docs


def load_documents(
    source: Union[str, List[str]],
    **kwargs,
) -> List[Document]:
    """
    统一的文档加载接口

    Args:
        source: 文件路径、目录路径或文件路径列表
        **kwargs: 传递给 load_directory 的额外参数

    Returns:
        Document 列表

    Example:
        >>> # 加载单个文件
        >>> docs = load_documents("docs/report.pdf")

        >>> # 加载目录
        >>> docs = load_documents("docs/")

        >>> # 加载多个文件
        >>> docs = load_documents(["docs/a.pdf", "docs/b.txt"])
    """
    if isinstance(source, list):
        all_docs = []
        for path in source:
            try:
                docs = load_file(path) if os.path.isfile(path) else load_directory(path, **kwargs)
                all_docs.extend(docs)
            except Exception as e:
                logger.warning(f"加载失败 {path}: {e}")
        return all_docs

    elif os.path.isfile(source):
        return load_file(source)

    elif os.path.isdir(source):
        return load_directory(source, **kwargs)

    else:
        raise ValueError(f"无效的文档源: {source}")


# ==================== LangChain DirectoryLoader 兼容接口 ====================

def get_directory_loader(
    directory_path: str,
    glob: str = "**/*",
    load_hidden: bool = False,
    silent_errors: bool = False,
    recursive: bool = True,
) -> List[Document]:
    """
    使用 LangChain DirectoryLoader 的兼容接口

    Args:
        directory_path: 目录路径
        glob: 文件匹配模式（如 "*.pdf"）
        load_hidden: 是否加载隐藏文件
        silent_errors: 是否静默处理错误
        recursive: 是否递归搜索

    Returns:
        Document 列表
    """
    from langchain_community.document_loaders import DirectoryLoader

    loader = DirectoryLoader(
        path=directory_path,
        glob=glob,
        load_hidden=load_hidden,
        silent_errors=silent_errors,
        recursive=recursive,
    )

    docs = loader.load()
    logger.info(f"📂 DirectoryLoader 完成: 共加载 {len(docs)} 个文档块")
    return docs
