"""Resume file handling."""

from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime
import PyPDF2

from services.settings import settings


class FileService:
    """Handle resume file uploads and extraction."""
    
    def __init__(self):
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_upload(self, file_bytes: bytes, filename: str) -> str:
        """Save uploaded file and return ID."""
        if len(file_bytes) > settings.max_file_size:
            raise ValueError(f"File too large: {len(file_bytes)} bytes")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_id = f"{timestamp}_{filename}"
        file_path = self.upload_dir / file_id
        
        file_path.write_bytes(file_bytes)
        return file_id
    
    async def get_file_path(self, file_id: str) -> Path:
        """Get path to uploaded file."""
        file_path = self.upload_dir / file_id
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_id}")
        return file_path
    
    @staticmethod
    def extract_pdf_text(file_path: Path) -> str:
        """Extract text from PDF."""
        text = []
        try:
            with open(file_path, "rb") as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    text.append(page.extract_text())
        except Exception as e:
            raise ValueError(f"Failed to extract PDF: {e}")
        
        return "\n".join(text)