"""Integration and unit tests for the Asset Ingestion API using TestClient."""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_upload_asset_workflow():
    # 1. Request upload ticket (upload_asset contract)
    ticket_payload = {
        "filename": "camera_wide.mp4",
        "content_type": "video/mp4",
        "byte_size": 1024,
    }
    res = client.post("/api/v1/assets/upload-url", json=ticket_payload)
    assert res.status_code == 200
    data = res.json()
    assert "asset_id" in data
    assert "upload_url" in data
    assert "attachment_url" in data
    assert data["headers"]["Content-Type"] == "video/mp4"

    asset_id = data["asset_id"]

    # 2. Upload sample binary bytes to the issued upload endpoint
    fake_video_bytes = b"FAKE_MP4_HEADER_VIDEO_STREAM_BYTES"
    upload_endpoint = f"/api/v1/assets/upload/{asset_id}/camera_wide.mp4"
    upload_res = client.put(upload_endpoint, content=fake_video_bytes)
    assert upload_res.status_code == 200
    upload_data = upload_res.json()
    assert upload_data["status"] == "success"
    assert upload_data["bytes_received"] == len(fake_video_bytes)

    # 3. Retrieve the asset via public attachment route
    get_res = client.get(f"/api/v1/assets/{asset_id}/camera_wide.mp4")
    assert get_res.status_code == 200
    assert get_res.content == fake_video_bytes
