"""End-to-End integration test covering the entire Motion GVA clean-room workflow."""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models.timeline import Timeline, TrackType

client = TestClient(app)


def test_full_motion_gva_lifecycle():
    # Step 1: Request presigned asset ticket
    asset_res = client.post(
        "/api/v1/assets/upload-url",
        json={
            "filename": "podcast_multicam_wide.mp4",
            "content_type": "video/mp4",
            "byte_size": 104857600,
        },
    )
    assert asset_res.status_code == 200
    asset_data = asset_res.json()
    assert "upload_url" in asset_data
    assert "asset_id" in asset_data
    asset_id = asset_data["asset_id"]

    # Step 2: Create autonomous video project (create_video contract)
    create_res = client.post(
        "/api/v1/videos/create",
        json={
            "prompt": "Edit my multicam footage into an engaging 15-second teaser. Cut to active speaker.",
            "engine": "gva",
            "effort": "standard",
            "aspect_ratio": "16:9",
            "attachments": [asset_id, "guest_cam.mp4"],
        },
    )
    assert create_res.status_code == 202
    create_data = create_res.json()
    job_id = create_data["job_id"]
    assert create_data["status"] == "completed"

    # Step 3: Fetch status
    status_res = client.get(f"/api/v1/videos/status/{job_id}")
    assert status_res.status_code == 200
    assert status_res.json()["progress_percent"] == 100

    # Step 4: Retrieve Timeline JSON & verify structure
    timeline_res = client.get(f"/api/v1/videos/{job_id}/timeline")
    assert timeline_res.status_code == 200
    timeline = timeline_res.json()
    assert timeline["width"] == 1920
    assert timeline["height"] == 1080
    assert len(timeline["tracks"]) >= 3  # Video, Captions, Audio

    initial_video_track = next(t for t in timeline["tracks"] if t["track_type"] == "video")
    initial_intro_duration = initial_video_track["clips"][0]["duration_ms"]

    # Step 5: Conversational Followup Revision #1 - Trimming
    followup_trim_res = client.post(
        "/api/v1/videos/followup",
        json={
            "job_id": job_id,
            "instruction": "Trim intro for snappier pacing",
        },
    )
    assert followup_trim_res.status_code == 200
    assert "Trimmed intro clip" in followup_trim_res.json()["diff_summary"]

    # Verify timeline updated
    timeline_v2_res = client.get(f"/api/v1/videos/{job_id}/timeline")
    timeline_v2 = timeline_v2_res.json()
    v2_video_track = next(t for t in timeline_v2["tracks"] if t["track_type"] == "video")
    assert v2_video_track["clips"][0]["duration_ms"] < initial_intro_duration

    # Step 6: Conversational Followup Revision #2 - Kinetic Subtitle Styling
    followup_caption_res = client.post(
        "/api/v1/videos/followup",
        json={
            "job_id": job_id,
            "instruction": "Change caption font color to yellow and make it larger",
        },
    )
    assert followup_caption_res.status_code == 200
    caption_diff = followup_caption_res.json()["diff_summary"]
    assert "yellow" in caption_diff

    # Step 7: Conversational Followup Revision #3 - Spatial Canvas Annotation
    followup_annot_res = client.post(
        "/api/v1/videos/followup",
        json={
            "job_id": job_id,
            "instruction": "Isolate guest speaker with a close-up",
            "timestamp_ms": 4500,
            "annotation_bounds": {"x": 120.0, "y": 80.0, "width": 400.0, "height": 300.0},
        },
    )
    assert followup_annot_res.status_code == 200
    annot_diff = followup_annot_res.json()["diff_summary"]
    assert "isolate speaker" in annot_diff

    # Step 8: Multi-format Roundtrip Exports
    remotion_res = client.get(f"/api/v1/videos/{job_id}/export/remotion")
    assert remotion_res.status_code == 200
    remotion_code = remotion_res.json()["content"]
    assert "from 'remotion';" in remotion_code
    assert "VideoComposition" in remotion_code

    fcpxml_res = client.get(f"/api/v1/videos/{job_id}/export/fcpxml")
    assert fcpxml_res.status_code == 200
    fcpxml_content = fcpxml_res.json()["content"]
    assert '<?xml version="1.0"' in fcpxml_content
    assert '<fcpxml version="1.9">' in fcpxml_content
