"""Utility functions and helpers."""

import os
import uuid
from datetime import datetime
from pathlib import Path

from src.config import settings


class FileUploadHandler:
    """Handle file uploads and storage."""

    @staticmethod
    def ensure_upload_dir():
        """Ensure upload directory exists."""
        Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def save_uploaded_file(file_content: bytes, original_filename: str) -> str:
        """Save uploaded file and return path."""
        FileUploadHandler.ensure_upload_dir()

        file_ext = Path(original_filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

        with open(file_path, "wb") as f:
            f.write(file_content)

        return file_path

    @staticmethod
    def delete_file(file_path: str) -> bool:
        """Delete a file."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
        return False


class DateTimeHelper:
    """DateTime utility functions."""

    @staticmethod
    def parse_iso_date(date_str: str) -> datetime:
        """Parse ISO format date string."""
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))

    @staticmethod
    def is_date_expired(expiry_date: datetime) -> bool:
        """Check if date is expired."""
        return expiry_date < datetime.utcnow()
