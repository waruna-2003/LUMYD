import os
import uuid
from pathlib import Path

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"

class StorageService:
    @staticmethod
    def save_file(file_content: bytes, original_filename: str) -> str:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            
        extension = os.path.splitext(original_filename)[1].lower()
        unique_filename = f"{uuid.uuid4()}{extension}"
        file_path = UPLOAD_DIR / unique_filename
        
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
            
        return str(file_path)

    @classmethod
    def resolve_file_path(cls, storage_path: str) -> str:
        """Resolves file path robustly even if repository root moved across directories."""
        if os.path.exists(storage_path):
            return storage_path
        filename = os.path.basename(storage_path)
        candidate = UPLOAD_DIR / filename
        if candidate.exists():
            return str(candidate)
        return storage_path
