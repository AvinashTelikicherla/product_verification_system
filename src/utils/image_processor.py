"""Image processing and analysis utilities."""

import base64
from pathlib import Path
from typing import Optional, Tuple


class ImageProcessor:
    """Handle image processing and analysis."""

    SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20MB

    @staticmethod
    def validate_image_file(file_path: str) -> Tuple[bool, str]:
        """Validate image file."""
        path = Path(file_path)

        if not path.exists():
            return False, "File does not exist"

        if path.suffix.lower() not in ImageProcessor.SUPPORTED_FORMATS:
            supported = ", ".join(ImageProcessor.SUPPORTED_FORMATS)
            return False, f"Unsupported image format. Supported: {supported}"

        file_size = path.stat().st_size
        if file_size > ImageProcessor.MAX_IMAGE_SIZE:
            return (
                False,
                f"File size exceeds {ImageProcessor.MAX_IMAGE_SIZE / (1024*1024):.0f}MB limit",
            )

        return True, "Valid image"

    @staticmethod
    def encode_image_to_base64(file_path: str) -> Optional[str]:
        """Encode image file to base64."""
        try:
            with open(file_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception as e:
            print(f"Error encoding image: {e}")
            return None

    @staticmethod
    def get_image_mime_type(file_path: str) -> str:
        """Get MIME type for image."""
        ext = Path(file_path).suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        return mime_types.get(ext, "image/jpeg")
