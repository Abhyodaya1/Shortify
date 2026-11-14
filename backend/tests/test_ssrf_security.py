"""Tests for Deep URL Ingestion Security & SSRF Defense (Task 3).
Verifies scheme whitelisting, host whitelisting, video ID syntax, DNS pre-resolution,
private IP/metadata endpoint rejection, and API integration.
"""

import socket
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.url_security_validator import URLSecurityValidator, SSRFSecurityError


@pytest.fixture
def client():
    return TestClient(app)


class TestURLSecurityValidator:
    """Unit tests for URLSecurityValidator logic."""

    def test_valid_youtube_urls(self):
        """Standard valid YouTube URL formats must be accepted and parsed correctly."""
        # Standard watch URL
        url, vid = URLSecurityValidator.validate_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert vid == "dQw4w9WgXcQ"

        # youtu.be short URL
        url, vid = URLSecurityValidator.validate_url("https://youtu.be/dQw4w9WgXcQ")
        assert vid == "dQw4w9WgXcQ"

        # Mobile URL
        url, vid = URLSecurityValidator.validate_url("https://m.youtube.com/watch?v=dQw4w9WgXcQ")
        assert vid == "dQw4w9WgXcQ"

        # Shorts URL
        url, vid = URLSecurityValidator.validate_url("https://www.youtube.com/shorts/dQw4w9WgXcQ")
        assert vid == "dQw4w9WgXcQ"

        # Embed URL
        url, vid = URLSecurityValidator.validate_url("https://www.youtube.com/embed/dQw4w9WgXcQ")
        assert vid == "dQw4w9WgXcQ"

    def test_disallowed_schemes_rejected(self):
        """file://, ftp://, gopher:// and other non-http(s) schemes must be rejected."""
        disallowed = [
            "file:///C:/Windows/win.ini",
            "file:///etc/passwd",
            "ftp://files.example.com/video.mp4",
            "gopher://127.0.0.1:6379/",
            "data:text/html,<html>test</html>",
            "tftp://10.0.0.1/file",
        ]
        for url in disallowed:
            with pytest.raises(SSRFSecurityError) as exc_info:
                URLSecurityValidator.validate_url(url)
            assert "Unsupported URL scheme" in str(exc_info.value)

    def test_unauthorized_hosts_rejected(self):
        """Non-YouTube hosts must be blocked immediately."""
        unauthorized = [
            "http://127.0.0.1/watch?v=dQw4w9WgXcQ",
            "http://localhost/watch?v=dQw4w9WgXcQ",
            "http://169.254.169.254/latest/meta-data/",
            "http://10.0.0.1/watch?v=dQw4w9WgXcQ",
            "https://attacker-controlled.com/watch?v=dQw4w9WgXcQ",
            "https://vimeo.com/123456789",
        ]
        for url in unauthorized:
            with pytest.raises(SSRFSecurityError) as exc_info:
                URLSecurityValidator.validate_url(url)
            assert "Unauthorized video host" in str(exc_info.value)

    def test_invalid_video_id_format(self):
        """Video IDs not matching ^[a-zA-Z0-9_-]{11}$ must be rejected."""
        invalid_urls = [
            "https://www.youtube.com/watch?v=short",
            "https://www.youtube.com/watch?v=toolongvideoidentifier12345",
            "https://www.youtube.com/watch?v=../../etc/passwd",
            "https://www.youtube.com/watch?v=",
            "https://youtu.be/bad_id",
        ]
        for url in invalid_urls:
            with pytest.raises(ValueError) as exc_info:
                URLSecurityValidator.validate_url(url)
            assert "Invalid" in str(exc_info.value) or "missing" in str(exc_info.value)

    def test_dns_rebinding_loopback_rejected(self):
        """If youtube.com resolves to 127.0.0.1, it must be blocked as SSRF."""
        fake_addrinfo = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))]
        with patch("socket.getaddrinfo", return_value=fake_addrinfo):
            with pytest.raises(SSRFSecurityError) as exc_info:
                URLSecurityValidator.validate_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
            assert "blocked private or reserved IP address: 127.0.0.1" in str(exc_info.value)

    def test_dns_rebinding_cloud_metadata_rejected(self):
        """If youtube.com resolves to 169.254.169.254, it must be blocked as SSRF."""
        fake_addrinfo = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("169.254.169.254", 443))]
        with patch("socket.getaddrinfo", return_value=fake_addrinfo):
            with pytest.raises(SSRFSecurityError) as exc_info:
                URLSecurityValidator.validate_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
            assert "169.254.169.254" in str(exc_info.value)

    def test_dns_rebinding_private_class_a_rejected(self):
        """If youtube.com resolves to 10.0.0.5, it must be blocked as SSRF."""
        fake_addrinfo = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.5", 443))]
        with patch("socket.getaddrinfo", return_value=fake_addrinfo):
            with pytest.raises(SSRFSecurityError) as exc_info:
                URLSecurityValidator.validate_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
            assert "10.0.0.5" in str(exc_info.value)

    def test_dns_rebinding_ipv6_mapped_loopback_rejected(self):
        """If youtube.com resolves to ::ffff:127.0.0.1, it must be blocked as SSRF."""
        fake_addrinfo = [(socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("::ffff:127.0.0.1", 443, 0, 0))]
        with patch("socket.getaddrinfo", return_value=fake_addrinfo):
            with pytest.raises(SSRFSecurityError) as exc_info:
                URLSecurityValidator.validate_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
            assert "blocked private or reserved IP address" in str(exc_info.value)


class TestSSRFAPIIntegration:
    """API-level integration tests for /api/v1/shorts/ingest-url endpoint."""

    def test_api_blocks_file_scheme(self, client):
        resp = client.post("/api/v1/shorts/ingest-url", json={"url": "file:///C:/Windows/win.ini"})
        assert resp.status_code == 403
        assert "Security violation" in resp.json()["detail"]

    def test_api_blocks_metadata_ip(self, client):
        resp = client.post("/api/v1/shorts/ingest-url", json={"url": "http://169.254.169.254/latest/meta-data/"})
        assert resp.status_code == 403
        assert "Security violation" in resp.json()["detail"]

    def test_api_blocks_localhost(self, client):
        resp = client.post("/api/v1/shorts/ingest-url", json={"url": "http://127.0.0.1:8000/api/v1/shorts/ingest-url"})
        assert resp.status_code == 403
        assert "Security violation" in resp.json()["detail"]

    def test_api_rejects_invalid_video_id(self, client):
        resp = client.post("/api/v1/shorts/ingest-url", json={"url": "https://www.youtube.com/watch?v=bad"})
        assert resp.status_code == 400
        assert "Invalid URL" in resp.json()["detail"]

