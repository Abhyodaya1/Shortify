"""Tests for Path Traversal Protection & Subprocess Timeouts (Task 4).
Verifies resolved-path containment checks on file routes and strict timeout enforcement.
"""

from pathlib import Path
import subprocess
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.timeline_compositor import MasterTimelineCompositor


@pytest.fixture
def client():
    return TestClient(app)


class TestPathTraversalProtection:
    """Verifies that directory traversal attacks on static file endpoints are blocked."""

    def test_preview_blocks_relative_traversal(self, client):
        """Relative traversal sequences must return HTTP 400."""
        traversal_attempts = [
            "..%2F..%2Fmain.py",
            "..\\..\\main.py",
            "....//....//Windows//win.ini",
            "%2e%2e%2f%2e%2e%2fmain.py",
            "valid_test_clip.mp4%00.exe",
        ]
        for payload in traversal_attempts:
            resp = client.get(f"/api/v1/shorts/preview/{payload}")
            assert resp.status_code == 400, f"Expected 400 for payload: {payload}, got {resp.status_code}"
            assert "Path traversal attempt detected" in resp.json()["detail"]

    def test_download_blocks_relative_traversal(self, client):
        """Download endpoint must block traversal attempts with HTTP 400."""
        resp = client.get("/api/v1/shorts/download/..%2F..%2F..%2FWindows%2Fwin.ini")
        assert resp.status_code == 400
        assert "Path traversal attempt detected" in resp.json()["detail"]

    def test_preview_nonexistent_file_returns_404(self, client):
        """A clean, non-existent file name inside the renders dir must return HTTP 404."""
        resp = client.get("/api/v1/shorts/preview/non_existent_clip_12345.mp4")
        assert resp.status_code == 404
        assert "Requested video file does not exist" in resp.json()["detail"]

    def test_preview_legitimate_file_succeeds(self, client, tmp_path):
        """A legitimate file strictly inside STORAGE_RENDERS must return HTTP 200."""
        renders_dir = Path("backend/storage/renders").resolve()
        renders_dir.mkdir(parents=True, exist_ok=True)
        test_file = renders_dir / "valid_test_clip.mp4"
        test_file.write_bytes(b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom")

        try:
            resp = client.get("/api/v1/shorts/preview/valid_test_clip.mp4")
            assert resp.status_code == 200
            assert resp.headers["content-type"] == "video/mp4"
        finally:
            if test_file.exists():
                test_file.unlink()

    def test_background_thumbnail_blocks_traversal(self, client):
        """Background thumbnail endpoint must reject path traversal attempts."""
        resp = client.get("/api/v1/shorts/backgrounds/..%2F..%2Ftest/thumbnail")
        assert resp.status_code == 400
        assert "Invalid background ID" in resp.json()["detail"]


class TestSubprocessTimeoutGuards:
    """Verifies that subprocess calls fail safely on timeout instead of hanging."""

    def test_safe_run_ffmpeg_times_out(self):
        """_safe_run_ffmpeg must raise RuntimeError when a process hangs and exceeds timeout."""
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd=["ffmpeg"], timeout=1)):
            with pytest.raises(RuntimeError) as exc_info:
                MasterTimelineCompositor._safe_run_ffmpeg(["ffmpeg", "-i", "hanging_input.mp4"], timeout=1)
            assert "timed out after 1 seconds" in str(exc_info.value)
