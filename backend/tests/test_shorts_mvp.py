"""Comprehensive tests for the Personal Shorts Generator MVP."""

import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.video_ingestion import IngestionService
from backend.app.services.face_tracker import FaceTrackingReframer
from backend.app.services.clip_selector import SmartClipSelector
from backend.app.services.shorts_renderer import ShortsRenderer
from backend.app.services.quality_assurance import QualityAssuranceEngine
from backend.app.storage.profile_store import ProfileStore
from backend.app.storage.dataset_store import DatasetStore, ClipFeedbackSubmission

client = TestClient(app)
TEST_SAMPLE = "backend/storage/uploads/test_sample.mp4"


def test_ingestion_service_local():
    assert os.path.exists(TEST_SAMPLE)
    data = IngestionService.ingest_local_file(TEST_SAMPLE, "test_sample.mp4")
    assert data["video_id"] is not None
    assert data["width"] == 1280
    assert data["height"] == 720
    assert data["duration_sec"] > 0
    assert len(data["transcript_cues"]) > 0


def test_face_tracking_reframer():
    reframer = FaceTrackingReframer()
    crop_data = reframer.track_clip_faces(TEST_SAMPLE, start_sec=0.0, end_sec=3.0)
    assert crop_data["source_width"] == 1280
    assert crop_data["source_height"] == 720
    assert crop_data["crop_width"] == int(720 * 9 / 16)
    assert crop_data["crop_height"] == 720
    assert 0 <= crop_data["optimal_crop_x"] <= (1280 - crop_data["crop_width"])


@pytest.mark.anyio
async def test_smart_clip_selector_modes():
    sample_cues = [
        {"start_sec": 0.0, "end_sec": 5.0, "text": "Stop editing clips by hand in 2026 before you burn out."},
        {"start_sec": 5.0, "end_sec": 12.0, "text": "This automated personal MVP identifies the best viral moments."},
        {"start_sec": 12.0, "end_sec": 22.0, "text": "It tracks the speaker's face with computer vision and centers the composition."},
        {"start_sec": 22.0, "end_sec": 31.0, "text": "Then it burns kinetic subtitles directly onto the 9:16 vertical MP4."},
    ]

    # Test 31s mode
    clips_31s = await SmartClipSelector.discover_clips(sample_cues, "AI Workflow", "31s")
    assert len(clips_31s) >= 1
    c31 = clips_31s[0]
    assert c31["duration_mode"] == "31s"
    assert c31["engagement_score"] > 30
    assert c31["opening_hook"] is not None
    assert "hook" in c31["score_breakdown"]
    assert "payoff" in c31["score_breakdown"]
    assert "standalone_context" in c31["score_breakdown"]


def test_shorts_renderer_mp4_and_qa():
    reframer = FaceTrackingReframer()
    crop_data = reframer.track_clip_faces(TEST_SAMPLE, 0.0, 2.0)
    output_filename = "test_rendered_short.mp4"

    rendered_path = ShortsRenderer.render_short_mp4(
        source_video_path=TEST_SAMPLE,
        start_sec=0.0,
        end_sec=2.0,
        crop_data=crop_data,
        hook_text="Stop editing clips by hand",
        subtitles=[
            {"start_rel_sec": 0.0, "end_rel_sec": 1.0, "text": "Stop editing clips by hand"},
            {"start_rel_sec": 1.0, "end_rel_sec": 2.0, "text": "before you burn out"},
        ],
        output_filename=output_filename,
    )
    assert os.path.exists(rendered_path)
    assert os.path.getsize(rendered_path) > 1000

    # Test Technical QA
    qa = QualityAssuranceEngine.validate_short_mp4(rendered_path, target_duration_sec=2.0)
    assert qa["checks"]["file_size_bytes"] > 1000
    assert qa["checks"]["width"] == 1080
    assert qa["checks"]["height"] == 1920
    assert qa["checks"]["aspect_ratio"] == 0.5625
    assert qa["checks"]["audio_stream_present"] is True


def test_api_shorts_flow_and_feedback():
    # 1. Upload local file
    with open(TEST_SAMPLE, "rb") as f:
        res = client.post("/api/v1/shorts/upload-file", files={"file": ("test_sample.mp4", f, "video/mp4")})
    assert res.status_code == 200
    video_id = res.json()["video_id"]

    # 2. Discover clips (Mode 31s)
    res_disc = client.post(
        "/api/v1/shorts/discover-clips",
        json={"video_id": video_id, "duration_mode": "31s"},
    )
    assert res_disc.status_code == 200
    data_disc = res_disc.json()
    assert len(data_disc["clips"]) >= 1
    clip_id = data_disc["clips"][0]["clip_id"]

    # 3. Render clip to 9:16 vertical MP4
    res_render = client.post("/api/v1/shorts/render-clip", json={"clip_id": clip_id})
    assert res_render.status_code == 200
    render_data = res_render.json()
    assert render_data["status"] == "success"
    assert "download_url" in render_data
    assert "qa_result" in render_data

    # 4. Download file
    res_dl = client.get(render_data["download_url"])
    assert res_dl.status_code == 200
    assert res_dl.headers["content-type"] == "video/mp4"

    # 5. Submit structured human feedback
    feedback_payload = {
        "clip_id": clip_id,
        "overall_rating": "good",
        "hook_rating": "strong",
        "subtitle_rating": "good",
        "framing_rating": "correct",
        "pacing_rating": "balanced",
        "approved_for_reference": True,
        "rejection_reasons": [],
        "notes": "Verified good payoff and accurate kinetic subtitles.",
    }
    fb_res = client.post(f"/api/v1/shorts/clips/{clip_id}/feedback", json=feedback_payload)
    assert fb_res.status_code == 200
    assert fb_res.json()["status"] == "recorded"

    # 6. Export dataset
    exp_res = client.get("/api/v1/shorts/dataset/export?dataset_type=preferences")
    assert exp_res.status_code == 200
    exp_data = exp_res.json()
    assert exp_data["record_count"] >= 1
