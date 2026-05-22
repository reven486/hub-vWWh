import requests
import time
import zipfile
import os
import shutil
import httpx
import ssl
from typing import List, Optional
from dataclasses import dataclass
from PIL import Image
import uuid
import asyncio
from app.config import settings

# Disable SSL warnings
import urllib3
urllib3.disable_warnings()


@dataclass
class ImageInfo:
    image_id: str
    image_path: str
    caption: str
    page: int


@dataclass
class ParseResult:
    doc_id: str
    doc_name: str
    markdown: str
    images: List[ImageInfo]
    pages: List[str]


class MinerUParser:
    """基于MinerU API的PDF解析器"""

    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None):
        self.api_url = api_url or "https://mineru.net/api/v4"
        self.api_key = api_key or settings.MINERU_API_KEY

    async def parse(self, file_path: str, doc_id: str) -> ParseResult:
        """
        调用MinerU API解析PDF

        步骤:
        1. 检查是否已有解析结果
        2. 如无，则调用API解析
        3. 下载并解压结果
        4. 解析markdown和图像
        """
        file_name = os.path.basename(file_path)
        output_dir = os.path.join("data", "mineru_output", doc_id)

        # 先查找是否有已存在的解析结果
        existing_result = self._find_existing_result()
        if existing_result:
            existing_dir = os.path.dirname(existing_result)
            # 使用已有结果的目录结构
            return self._parse_output(doc_id, file_name, existing_dir)

        # 1. 申请上传URL
        batch_id, upload_urls = self._get_batch_upload_url([file_name])

        # 2. 上传文件
        self._upload_files([file_path], upload_urls)

        # 3. 轮询结果
        zip_url = self._poll_batch_result(batch_id, timeout=600)

        # 4. 下载并解压
        self._download_and_unzip(zip_url, output_dir)

        # 5. 解析结果
        return self._parse_output(doc_id, file_name, output_dir)

    def _find_existing_result(self) -> Optional[str]:
        """查找已存在的解析结果，返回full.md的路径"""
        mineru_base = os.path.join("data", "mineru_output")
        if not os.path.exists(mineru_base):
            return None

        for doc_folder in os.listdir(mineru_base):
            full_md = os.path.join(mineru_base, doc_folder, "full.md")
            if os.path.exists(full_md):
                return full_md
        return None

    def _get_batch_upload_url(self, file_names: List[str]):
        """申请批量上传URL"""
        url = f"{self.api_url}/file-urls/batch"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        files = [{"name": name, "data_id": f"file_{i}"} for i, name in enumerate(file_names)]
        data = {"files": files, "model_version": "vlm"}

        response = requests.post(url, headers=headers, json=data, verify=False)
        if response.status_code != 200:
            raise Exception(f"申请上传URL失败，状态码：{response.status_code}")

        result = response.json()
        if result["code"] != 0:
            raise Exception(f"申请失败：{result['msg']}")

        return result["data"]["batch_id"], result["data"]["file_urls"]

    def _upload_files(self, file_paths: List[str], upload_urls: List[str]):
        """上传文件到预签名URL"""
        import urllib3
        urllib3.disable_warnings()
        for local_path, upload_url in zip(file_paths, upload_urls):
            with open(local_path, 'rb') as f:
                res = requests.put(upload_url, data=f, verify=False)
            if res.status_code != 200:
                raise Exception(f"上传失败：{local_path}，状态码：{res.status_code}")

    def _poll_batch_result(self, batch_id: str, timeout: int = 600, interval: int = 3):
        """轮询解析结果"""
        poll_url = f"{self.api_url}/extract-results/batch/{batch_id}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        start_time = time.time()

        while time.time() - start_time < timeout:
            resp = requests.get(poll_url, headers=headers, verify=False)
            result = resp.json()

            if result["code"] != 0:
                raise Exception(f"查询失败：{result}")

            for item in result["data"]["extract_result"]:
                state = item["state"]
                name = item["file_name"]

                if state == "done":
                    return item["full_zip_url"]
                elif state == "failed":
                    raise Exception(f"解析失败：{name} - {item.get('err_msg', '未知错误')}")

            time.sleep(interval)

        raise Exception("解析超时")

    def _download_and_unzip(self, zip_url: str, save_dir: str):
        """下载并解压结果"""
        os.makedirs(save_dir, exist_ok=True)

        resp = requests.get(zip_url, verify=False)
        zip_path = os.path.join(save_dir, "result.zip")

        with open(zip_path, "wb") as f:
            f.write(resp.content)

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(save_dir)

    def _parse_output(self, doc_id: str, file_name: str, output_dir: str) -> ParseResult:
        """解析MinerU输出结果"""
        markdown = ""
        images = []

        # MinerU输出的是full.md，不是{file_name}.md
        md_path = os.path.join(output_dir, "full.md")
        if os.path.exists(md_path):
            with open(md_path, "r", encoding="utf-8") as f:
                markdown = f.read()

        # 查找图像文件夹
        images_dir = os.path.join(output_dir, "images")
        if os.path.exists(images_dir):
            for idx, img_file in enumerate(os.listdir(images_dir)):
                if img_file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                    img_path = os.path.join(images_dir, img_file)
                    dest_path = os.path.join(settings.IMAGE_PATH, f"{doc_id}_{idx}_{img_file}")

                    # 复制到images目录
                    shutil.copy(img_path, dest_path)

                    images.append(ImageInfo(
                        image_id=str(uuid.uuid4()),
                        image_path=dest_path,
                        caption="",
                        page=idx + 1
                    ))

        # 提取页面
        pages = self._extract_pages(markdown)

        return ParseResult(
            doc_id=doc_id,
            doc_name=file_name,
            markdown=markdown,
            images=images,
            pages=pages
        )

    def _extract_pages(self, markdown: str) -> List[str]:
        """从markdown中提取页面分割"""
        sections = markdown.split("---PAGE BREAK---")
        return [s.strip() for s in sections if s.strip()]


class MockMinerUParser:
    """用于测试的Mock解析器"""

    async def parse(self, file_path: str, doc_id: str) -> ParseResult:
        """模拟解析PDF，返回预设数据"""
        doc_name = os.path.basename(file_path)

        markdown = """
# 示例文档

这是第一页的内容。

![image1](image_placeholder_1)

## 第二页

第二页的文本内容，包含一些重要信息。

![image2](image_placeholder_2)

## 第三页

第三页内容。
"""

        images = []
        for i in range(2):
            image_id = str(uuid.uuid4())
            image_path = os.path.join(settings.IMAGE_PATH, f"{doc_id}_{image_id}.png")
            images.append(ImageInfo(
                image_id=image_id,
                image_path=image_path,
                caption=f"Image caption {i + 1}",
                page=i + 1
            ))

        pages = ["Page 1 content", "Page 2 content", "Page 3 content"]

        return ParseResult(
            doc_id=doc_id,
            doc_name=doc_name,
            markdown=markdown,
            images=images,
            pages=pages
        )


def get_parser() -> MinerUParser:
    """获取解析器实例"""
    if settings.MINERU_API_KEY:
        return MinerUParser()
    return MockMinerUParser()