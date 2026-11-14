"""Unit and integration tests for Video Generation and Revision API."""

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_create_video_and_export_workflow():
    # 1. Submit video brief matching Motion's multicam prompt
    create_payload = {
        "prompt": "Edit my multicam footage into a cohesive video. Sync the camera angles, cut to the active speaker, and use wide shots and close-ups.",
        "engine": "gva",
        "effort": "standard",
        "aspect_ratio": "16:9",
        "attachments": ["camera_wide.mp4", "camera_speaker.mp4", "audio_master.wav"],
    }

    res = client.post("/api/v1/videos/create", json=create_payload)
    assert res.status_code == 202
    data = res.json()
    assert "job_id" in data
    assert "thread_id" in data
    assert data["status"] == "completed"

    job_id = data["job_id"]

    # 2. Query Job Status
    status_res = client.get(f"/api/v1/videos/status/{job_id}")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["status"] == "completed"
    assert status_data["progress_percent"] == 100

    # 3. Inspect generated Timeline JSON
    timeline_res = client.get(f"/api/v1/videos/{job_id}/timeline")
    assert timeline_res.status_code == 200
    timeline = timeline_res.json()
    assert timeline["width"] == 1920
    assert timeline["height"] == 1080
    assert len(timeline["tracks"]) >= 2

    # 4. Apply Follow-up conversational instruction (create_followup contract)
    followup_payload = {
        "job_id": job_id,
        "instruction": "Make the intro snappier by trimming 1 second, and make the captions bright yellow.",
        "timestamp_ms": 2000,
    }
    followup_res = client.post("/api/v1/videos/followup", json=followup_payload)
    assert followup_res.status_code == 200
    followup_data = followup_res.json()
    assert "Trimmed intro clip" in followup_data["diff_summary"]

    # 5. Export as Remotion JSX/TSX
    remotion_res = client.get(f"/api/v1/videos/{job_id}/export/remotion")
    assert remotion_res.status_code == 200
    assert "RemotionRoot" in remotion_res.json()["content"]

    # 6. Export as FCPXML
    fcpxml_res = client.get(f"/api/v1/videos/{job_id}/export/fcpxml")
    assert fcpxml_res.status_code == 200
    assert "<fcpxml" in fcpxml_res.json()["content"]

