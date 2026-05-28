import pdfplumber
from docx import Document as DocxDocument
from pathlib import Path
from typing import Optional


class TextProcessor:
    """Extract text from PDF, DOCX, TXT files"""

    def extract_from_pdf(self, file_path: Path) -> list[dict]:
        """Extract text from PDF with page numbers"""
        results = []
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if text and text.strip():
                    results.append({
                        "page": page_num,
                        "text": text.strip(),
                    })
        return results

    def extract_from_docx(self, file_path: Path) -> list[dict]:
        """Extract text from DOCX"""
        results = []
        doc = DocxDocument(file_path)
        text_parts = []
        current_page = 1

        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                text_parts.append(text)

        if text_parts:
            results.append({
                "page": current_page,
                "text": "\n".join(text_parts),
            })

        return results

    def extract_from_txt(self, file_path: Path) -> list[dict]:
        """Extract text from TXT file"""
        results = []
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read().strip()

        if text:
            results.append({
                "page": 1,
                "text": text,
            })

        return results

    def process(self, file_path: Path, doc_type: str) -> list[dict]:
        """Process file based on type"""
        if doc_type == "pdf":
            return self.extract_from_pdf(file_path)
        elif doc_type in ["docx", "doc"]:
            return self.extract_from_docx(file_path)
        elif doc_type == "txt":
            return self.extract_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported document type: {doc_type}")


text_processor = TextProcessor()
