import os
import json
import subprocess
from pathlib import Path

from app.core.config import settings


class PdfParser:
    def parse(self, pdf_path: str, output_dir: str) -> dict:
        os.makedirs(output_dir, exist_ok=True)
        result = self._run_mineru(pdf_path, output_dir)
        return self._collect_results(output_dir, result)

    def _run_mineru(self, pdf_path: str, output_dir: str) -> dict:
        try:
            subprocess.run(
                ["magic-pdf", "-p", pdf_path, "-o", output_dir],
                check=True, capture_output=True, text=True, timeout=300,
            )
            return {"success": True}
        except FileNotFoundError:
            return self._run_mineru_python_api(pdf_path, output_dir)
        except subprocess.CalledProcessError as e:
            return {"success": False, "error": e.stderr}

    def _run_mineru_python_api(self, pdf_path: str, output_dir: str) -> dict:
        try:
            from mineru.pdf_extractor import PDFExtractor
            extractor = PDFExtractor(pdf_path, output_dir)
            extractor.extract()
            return {"success": True}
        except ImportError:
            return {"success": False, "error": "mineru not installed"}

    def _collect_results(self, output_dir: str, parse_result: dict) -> dict:
        md_files = list(Path(output_dir).rglob("*.md"))
        image_files = list(Path(output_dir).rglob("*.png")) + list(Path(output_dir).rglob("*.jpg"))

        markdown_content = ""
        if md_files:
            markdown_content = md_files[0].read_text(encoding="utf-8")

        return {
            "success": parse_result.get("success", False),
            "error": parse_result.get("error"),
            "markdown": markdown_content,
            "image_paths": [str(f) for f in image_files],
            "output_dir": output_dir,
        }
