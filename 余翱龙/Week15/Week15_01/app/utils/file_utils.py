import os
import hashlib
from typing import Optional


def get_file_hash(file_path: str) -> str:
    """计算文件的MD5哈希值"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def ensure_dir(path: str) -> None:
    """确保目录存在"""
    os.makedirs(path, exist_ok=True)


def get_file_extension(filename: str) -> Optional[str]:
    """获取文件扩展名"""
    if "." in filename:
        return filename.rsplit(".", 1)[1].lower()
    return None


def is_pdf(filename: str) -> bool:
    """检查是否为PDF文件"""
    return get_file_extension(filename) == "pdf"