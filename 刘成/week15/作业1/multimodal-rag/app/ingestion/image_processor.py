import base64
from pathlib import Path
from PIL import Image
from io import BytesIO
from typing import Optional


class ImageProcessor:
    """Load, resize, and encode images"""

    MAX_DIMENSION = 1024  # Max width or height for embedding

    def load_image(self, file_path: Path) -> Image.Image:
        """Load image from file path"""
        return Image.open(file_path)

    def resize_if_needed(self, img: Image.Image) -> Image.Image:
        """Resize image if either dimension exceeds MAX_DIMENSION"""
        if img.width <= self.MAX_DIMENSION and img.height <= self.MAX_DIMENSION:
            return img

        ratio = min(self.MAX_DIMENSION / img.width, self.MAX_DIMENSION / img.height)
        new_width = int(img.width * ratio)
        new_height = int(img.height * ratio)
        return img.resize((new_width, new_height), Image.LANCZOS)

    def to_base64(self, img: Image.Image, format: str = "PNG") -> str:
        """Convert PIL Image to base64 string"""
        buffer = BytesIO()
        img.save(buffer, format=format)
        img_bytes = buffer.getvalue()
        return base64.b64encode(img_bytes).decode("utf-8")

    def process_image(
        self,
        file_path: Path,
        resize: bool = True,
    ) -> dict:
        """Process image file and return base64 + metadata"""
        img = self.load_image(file_path)

        original_width, original_height = img.width, img.height

        if resize:
            img = self.resize_if_needed(img)

        # Determine MIME type
        mime_type = f"image/{file_path.suffix[1:].lower()}"
        if mime_type == "image/jpg":
            mime_type = "image/jpeg"

        base64_data = self.to_base64(img, format=mime_type.split("/")[1].upper())

        return {
            "base64": base64_data,
            "mime_type": mime_type,
            "original_width": original_width,
            "original_height": original_height,
            "processed_width": img.width,
            "processed_height": img.height,
        }

    def is_image_file(self, file_path: Path) -> bool:
        """Check if file is a supported image type"""
        image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
        return file_path.suffix.lower() in image_extensions


image_processor = ImageProcessor()
