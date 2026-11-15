"""Tests for AI YouTube SEO Metadata Orchestration & Scheduling Integration (Phase 9 & SEO Audit).
Verifies:
- Elimination of hardcoded metadata in scheduling payload.
- Generation of transcript-grounded titles, descriptions, hashtags, and tags.
- Distinct metadata for different clip transcripts.
- Multi-dimensional caching of packaging artifacts.
- Synchronization to discovered_clips session store and persistent scheduler.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.api.shorts_mvp_api import discovered_clips
from backend.app.services.persistent_scheduler import PersistentScheduler
from backend.app.services.cache_service import ContentCacheService

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_test_state():
    """Clear test clips from session store before and after tests."""
    discovered_clips.clear()
    yield
    discovered_clips.clear()


def test_generate_clip_metadata_endpoint():
    """Verifies that /api/v1/shorts/clips/{clip_id}/metadata generates rich transcript-grounded metadata."""
    clip_id = "test_clip_seo_01"
    discovered_clips[clip_id] = {
        "clip_id": clip_id,
        "index": 1,
        "transcript_segment": "When you color grade your video, never crush your shadows completely or you lose all dynamic range in the final export.",
        "opening_hook": "Never crush your shadows completely",
        "headline": "Color Grading Secret",
        "title": "Old Generic Title",
        "cues": [
            {"start": 0.0, "end": 2.5, "text": "When you color grade your video,"},
            {"start": 2.5, "end": 5.0, "text": "never crush your shadows completely"},
            {"start": 5.0, "end": 8.0, "text": "or you lose all dynamic range in the final export."},
        ],
    }

    response = client.post(f"/api/v1/shorts/clips/{clip_id}/metadata")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert data["clip_id"] == clip_id

    # Title verification
    title = data["title"]
    assert title != "Viral Short"
    assert len(title) <= 100
    assert "shadows" in title.lower() or "color" in title.lower() or "grading" in title.lower()

    # Alternatives verification
    alts = data["title_alternatives"]
    assert len(alts) >= 3
    assert all("text" in alt and "angle" in alt for alt in alts)

    # Description verification
    desc = data["description"]
    assert "Produced with Motion Video Agent" not in desc
    assert "shadows" in desc.lower() or "color" in desc.lower()
    assert "#" in desc  # Contains hashtags

    # Tags verification (plain keywords, no #)
    tags = data["tags"]
    print("DEBUG_TAGS:", tags)
    assert isinstance(tags, list)
    assert len(tags) > 0
    assert len(tags) <= 15
    assert not any(t.startswith("#") for t in tags)
    assert any(
        any(k in t.lower() for k in ["color", "grading", "shadow", "dynamic", "export", "video", "creator"])
        for t in tags
    )

    # Hashtags verification (separate list with #)
    hashtags = data["hashtags"]
    assert isinstance(hashtags, list)
    assert len(hashtags) >= 3
    assert all(h.startswith("#") for h in hashtags)

    # Verify discovered_clips session persistence
    persisted_clip = discovered_clips[clip_id]
    assert persisted_clip["title"] == title
    assert persisted_clip["tags"] == tags
    assert persisted_clip["description"] == desc


def test_distinct_clips_receive_distinct_metadata():
    """Verifies that two different clips receive completely distinct, context-relevant metadata."""
    clip_python = "clip_python_tech"
    clip_lighting = "clip_camera_lighting"

    discovered_clips[clip_python] = {
        "clip_id": clip_python,
        "transcript_segment": "Python generators save massive amounts of memory because they yield items lazily instead of storing everything in RAM.",
        "opening_hook": "Python generators save massive memory",
        "headline": "Python Memory Trick",
        "cues": [{"start": 0.0, "end": 4.0, "text": "Python generators save massive memory"}],
    }

    discovered_clips[clip_lighting] = {
        "clip_id": clip_lighting,
        "transcript_segment": "The key light should always be positioned forty-five degrees from your subject with a soft diffusion box for cinematic skin tones.",
        "opening_hook": "Key light at forty-five degrees",
        "headline": "Cinematic Lighting Setup",
        "cues": [{"start": 0.0, "end": 4.0, "text": "The key light should always be positioned"}],
    }

    res_py = client.post(f"/api/v1/shorts/clips/{clip_python}/metadata")
    res_light = client.post(f"/api/v1/shorts/clips/{clip_lighting}/metadata")

    assert res_py.status_code == 200
    assert res_light.status_code == 200

    data_py = res_py.json()
    data_light = res_light.json()

    # Verify completely distinct titles
    assert data_py["title"] != data_light["title"]
    assert "python" in data_py["title"].lower() or "generator" in data_py["title"].lower() or "memory" in data_py["title"].lower()
    assert "light" in data_light["title"].lower() or "forty" in data_light["title"].lower() or "cinematic" in data_light["title"].lower()

    # Verify distinct tags
    tags_py = set(t.lower() for t in data_py["tags"])
    tags_light = set(t.lower() for t in data_light["tags"])
    assert tags_py != tags_light
    assert any("python" in t or "generator" in t or "memory" in t for t in tags_py)
    assert any("light" in t or "cinematic" in t or "subject" in t for t in tags_light)


def test_schedule_payload_preserves_custom_ai_metadata():
    """Verifies that scheduling a clip records the exact AI/edited title, description, and tags."""
    clip_id = "clip_to_schedule_01"
    discovered_clips[clip_id] = {
        "clip_id": clip_id,
        "title": "Master Camera Lighting Fast | #Shorts",
        "description": "Essential cinematic lighting breakdown.\n\n#Shorts #Lighting",
        "tags": ["Lighting", "Cinematic", "CameraGear", "YouTubeShorts"],
        "rendered_file": "backend/storage/renders/short_clip_to_schedule_01.mp4",
    }

    schedule_payload = {
        "clip_id": clip_id,
        "title": "Master Camera Lighting Fast | #Shorts",
        "description": "Essential cinematic lighting breakdown.\n\n#Shorts #Lighting",
        "tags": ["Lighting", "Cinematic", "CameraGear", "YouTubeShorts"],
        "video_file_path": "backend/storage/renders/short_clip_to_schedule_01.mp4",
        "thumbnail_url": "http://localhost:8000/api/v1/shorts/preview/short_clip_to_schedule_01.mp4",
        "scheduled_time": "2026-11-20T18:00:00",
        "target_channel_id": "UC_abhyodaya_clips_sandbox",
        "visibility": "unlisted",
    }

    res = client.post("/api/v1/youtube/schedule", json=schedule_payload)
    assert res.status_code == 200
    job = res.json()["scheduled_job"]

    assert job["clip_id"] == clip_id
    assert job["title"] == "Master Camera Lighting Fast | #Shorts"
    assert job["description"] == "Essential cinematic lighting breakdown.\n\n#Shorts #Lighting"
    assert job["tags"] == ["Lighting", "Cinematic", "CameraGear", "YouTubeShorts"]
    assert job["status"] == "scheduled"


def test_metadata_caching_and_regeneration():
    """Verifies multi-dimensional caching returns cached metadata until regenerate=True."""
    clip_id = "clip_cache_test"
    discovered_clips[clip_id] = {
        "clip_id": clip_id,
        "transcript_segment": "Audio quality is more important than video quality for viewer retention.",
        "opening_hook": "Audio is more important than video",
        "headline": "Audio Retention Rule",
        "cues": [{"start": 0.0, "end": 3.0, "text": "Audio quality is more important than video"}],
    }

    # Initial generation
    res1 = client.post(f"/api/v1/shorts/clips/{clip_id}/metadata")
    assert res1.status_code == 200
    data1 = res1.json()

    # Second call should fetch cached version
    res2 = client.get(f"/api/v1/shorts/clips/{clip_id}/metadata")
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["title"] == data1["title"]
    assert data2["tags"] == data1["tags"]
    assert data2["source"] == "cached_session"

    # Force regenerate
    res3 = client.post(f"/api/v1/shorts/clips/{clip_id}/metadata?regenerate=true")
    assert res3.status_code == 200
    data3 = res3.json()
    assert data3["source"] == "ai_generated"
