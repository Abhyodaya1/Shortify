"""Asset ingestion and storage endpoints implementing the upload_asset contract."""

from __future__ import annotations
from typing import Optional
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from ..services.storage import StorageService, UploadUrlResponse

router = APIRouter(prefix="/api/v1/assets", tags=["Assets"])
storage_service = StorageService(base_upload_dir=Path("data/uploads"))


class UploadAssetRequest(BaseModel):
    filename: str = Field(..., description="Original filename with extension (e.g. video.mp4)")
    content_type: str = Field(..., description="MIME content type (e.g. video/mp4, audio/wav)")
    byte_size: Optional[int] = Field(default=None, description="Expected file size in bytes")


@router.post("/upload-url", response_model=UploadUrlResponse, summary="Create presigned asset upload ticket (upload_asset contract)")
async def create_upload_url(payload: UploadAssetRequest) -> UploadUrlResponse:
    """Implements the Motion MCP upload_asset tool specification."""
    if not payload.filename:
        raise HTTPException(status_code=400, detail="Filename cannot be empty")
    return storage_service.create_upload_ticket(
        filename=payload.filename,
        content_type=payload.content_type,
        byte_size=payload.byte_size,
    )


@router.put("/upload/{asset_id}/{filename}", summary="Receive binary file upload")
async def receive_asset_upload(asset_id: str, filename: str, request: Request):
    """Receives binary upload payload at the issued upload_url."""
    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="Uploaded file body cannot be empty")
    path, attachment_url = storage_service.save_uploaded_bytes(asset_id, filename, body)
    return {
        "status": "success",
        "asset_id": asset_id,
        "filename": filename,
        "bytes_received": len(body),
        "attachment_url": attachment_url,
    }


@router.get("/{asset_id}/{filename}", summary="Retrieve stored media asset")
async def get_asset(asset_id: str, filename: str):
    """Streams the stored asset for video players and export renderers."""
    path = storage_service.engine.get_asset_path(asset_id, filename)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Asset not found")
    return FileResponse(path)

