"""Unit tests for EditorialProfile and profile API routes."""

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models.editorial_profile import EditorialProfile
from backend.app.storage.profile_store import ProfileStore

client = TestClient(app)


def test_profile_default_and_persistence():
    profile = ProfileStore.get_active_profile()
    assert profile.profile_id == "personal_default"
    assert profile.hook_style == "strong"
    assert profile.subtitle_style == "kinetic_editorial"
    assert profile.framing_style == "speaker"
    assert profile.target_duration_seconds in (31, 45)

    # Test snapshotting
    snapshot = ProfileStore.snapshot_profile()
    assert snapshot["profile_id"] == profile.profile_id
    assert snapshot["version"] == profile.version


def test_profile_api_endpoints():
    # GET profile
    res = client.get("/api/v1/profile")
    assert res.status_code == 200
    data = res.json()
    assert data["profile_id"] == "personal_default"
    version_before = data["version"]

    # PUT profile
    data["target_duration_seconds"] = 45
    data["max_hook_words"] = 8
    res_put = client.put("/api/v1/profile", json=data)
    assert res_put.status_code == 200
    put_data = res_put.json()
    assert put_data["target_duration_seconds"] == 45
    assert put_data["version"] == version_before + 1

    # Reset
    res_reset = client.post("/api/v1/profile/reset")
    assert res_reset.status_code == 200
    reset_data = res_reset.json()
    assert reset_data["target_duration_seconds"] == 31

