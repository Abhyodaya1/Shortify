"""Asset storage service supporting local development storage and S3-compatible backends."""

from __future__ import annotations
import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from uuid import uuid4
from pydantic import BaseModel, Field


class UploadUrlResponse(BaseModel):
    asset_id: str
    upload_url: str
    attachment_url: str
    headers: Dict[str, str] = Field(default_factory=dict)
    expires_in_seconds: int = 3600


class LocalStorageEngine:
    """Manages file storage on local filesystem for zero-cost offline development."""

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_asset_path(self, asset_id: str, filename: str) -> Path:
        safe_name = Path(filename).name
        # Group by asset_id to prevent collision
        asset_dir = self.base_dir / asset_id
        asset_dir.mkdir(parents=True, exist_ok=True)
        return asset_dir / safe_name

    def write_file(self, asset_id: str, filename: str, content: bytes) -> Path:
        path = self.get_asset_path(asset_id, filename)
        with open(path, "wb") as f:
            f.write(content)
        return path

    def file_exists(self, asset_id: str, filename: str) -> bool:
        return self.get_asset_path(asset_id, filename).exists()

    def get_file_size(self, asset_id: str, filename: str) -> int:
        path = self.get_asset_path(asset_id, filename)
        return path.stat().st_size if path.exists() else 0


class StorageService:
    """High-level asset storage service fulfilling the Motion upload_asset contract."""

    def __init__(self, base_upload_dir: Optional[Path] = None, host_url: str = "http://localhost:8000"):
        if base_upload_dir is None:
            base_upload_dir = Path("data/uploads")
        self.engine = LocalStorageEngine(base_upload_dir)
        self.host_url = host_url.rstrip("/")

    def create_upload_ticket(
        self,
        filename: str,
        content_type: str,
        byte_size: Optional[int] = None,
    ) -> UploadUrlResponse:
        asset_id = str(uuid4())
        safe_name = Path(filename).name
        
        # In local development mode, upload_url points to our local upload endpoint
        upload_url = f"{self.host_url}/api/v1/assets/upload/{asset_id}/{safe_name}"
        # Public attachment_url that can be used inside create_video
        attachment_url = f"{self.host_url}/api/v1/assets/{asset_id}/{safe_name}"

        return UploadUrlResponse(
            asset_id=asset_id,
            upload_url=upload_url,
            attachment_url=attachment_url,
            headers={"Content-Type": content_type},
            expires_in_seconds=3600,
        )

    def save_uploaded_bytes(self, asset_id: str, filename: str, content: bytes) -> Tuple[Path, str]:
        path = self.engine.write_file(asset_id, filename, content)
        attachment_url = f"{self.host_url}/api/v1/assets/{asset_id}/{filename}"
        return path, attachment_url

