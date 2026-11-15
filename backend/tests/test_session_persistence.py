"""Tests for Session Persistence (Phase 3 - Task 8)
Verifies that ingested videos and discovered clip candidates are persisted in SQLite
and safely survive simulated backend restarts (REL-02).
"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.storage.session_store import SessionStore, SessionVideosProxy, SessionClipsProxy


@pytest.fixture(autouse=True)
def setup_isolated_session_db(tmp_path):
    """Use an isolated SQLite database for each test to guarantee no side effects."""
    test_db = tmp_path / "test_session.db"
    SessionStore.set_db_path(test_db)
    yield
    # Cleanup
    SessionStore.clear()


class TestSessionStoreUnit:
    """Direct unit tests for SQLite-backed SessionStore."""

    def test_video_save_and_retrieve(self):
        video_data = {
            "video_id": "vid_abc123",
            "title": "Autonomous AI Agent Workflow",
            "filepath": "backend/storage/uploads/test.mp4",
            "duration_sec": 125.5,
            "thumbnail": "https://img.youtube.com/vi/abc/0.jpg",
            "width": 1920,
            "height": 1080,
            "transcript_cues": [
                {"start": 0.0, "end": 2.5, "text": "Here is the plan."},
                {"start": 2.5, "end": 5.0, "text": "We build with AI."},
            ],
        }

        SessionStore.save_video("vid_abc123", video_data)
        assert SessionStore.has_video("vid_abc123") is True

        retrieved = SessionStore.get_video("vid_abc123")
        assert retrieved is not None
        assert retrieved["title"] == "Autonomous AI Agent Workflow"
        assert len(retrieved["transcript_cues"]) == 2
        assert retrieved["duration_sec"] == 125.5

    def test_clip_save_and_retrieve(self):
        clip_data = {
            "clip_id": "clip_xyz789",
            "parent_video_id": "vid_abc123",
            "title": "The Golden Rule of Engineering",
            "start_sec": 12.0,
            "end_sec": 43.5,
            "opening_hook": "Why do 90% of developers fail?",
            "hook_formula": "Why Most People Fail",
            "hook_score": 88,
            "spoken_text": "Why do 90% of developers fail? It turns out...",
            "layout_mode": "split_screen",
            "rendered_file": "backend/storage/renders/short_clip_xyz789.mp4",
        }

        SessionStore.save_clip("clip_xyz789", clip_data)
        assert SessionStore.has_clip("clip_xyz789") is True

        retrieved = SessionStore.get_clip("clip_xyz789")
        assert retrieved is not None
        assert retrieved["opening_hook"] == "Why do 90% of developers fail?"
        assert retrieved["rendered_file"] == "backend/storage/renders/short_clip_xyz789.mp4"

    def test_persistence_survives_memory_cache_wipe(self):
        """Simulates server restart by wiping memory cache and re-reading from disk."""
        video_data = {"video_id": "restart_vid", "title": "Before Restart", "duration_sec": 60.0}
        clip_data = {"clip_id": "restart_clip", "parent_video_id": "restart_vid", "title": "Clip Before Restart"}

        SessionStore.save_video("restart_vid", video_data)
        SessionStore.save_clip("restart_clip", clip_data)

        # Force simulate process restart: clear in-memory caches and reinitialize
        SessionStore._videos_cache.clear()
        SessionStore._clips_cache.clear()
        SessionStore._initialized = False

        # Read back from database
        assert SessionStore.has_video("restart_vid") is True
        assert SessionStore.has_clip("restart_clip") is True

        recovered_video = SessionStore.get_video("restart_vid")
        recovered_clip = SessionStore.get_clip("restart_clip")
        assert recovered_video["title"] == "Before Restart"
        assert recovered_clip["title"] == "Clip Before Restart"

    def test_cascade_delete_video_removes_clips(self):
        video_data = {"video_id": "parent_vid", "title": "Parent Video"}
        clip_1 = {"clip_id": "c1", "parent_video_id": "parent_vid", "title": "Clip 1"}
        clip_2 = {"clip_id": "c2", "parent_video_id": "parent_vid", "title": "Clip 2"}

        SessionStore.save_video("parent_vid", video_data)
        SessionStore.save_clip("c1", clip_1)
        SessionStore.save_clip("c2", clip_2)

        assert len(SessionStore.list_clips(parent_video_id="parent_vid")) == 2

        SessionStore.delete_video("parent_vid")

        assert SessionStore.has_video("parent_vid") is False
        assert SessionStore.has_clip("c1") is False
        assert SessionStore.has_clip("c2") is False


class TestSessionDictProxies:
    """Tests dict-like MutableMapping behavior for ingested_videos and discovered_clips."""

    def test_proxy_dict_operations(self):
        videos = SessionVideosProxy()
        clips = SessionClipsProxy()

        videos["v1"] = {"video_id": "v1", "title": "Video 1"}
        assert "v1" in videos
        assert videos["v1"]["title"] == "Video 1"
        assert len(videos) == 1

        clips["c1"] = {"clip_id": "c1", "parent_video_id": "v1", "title": "Clip 1"}
        assert "c1" in clips
        assert clips.get("c1")["title"] == "Clip 1"
        assert clips.get("nonexistent", "fallback") == "fallback"

        # Check iteration
        keys = list(clips.keys())
        assert "c1" in keys

        del clips["c1"]
        assert "c1" not in clips


class TestSessionAPIEndpoints:
    """Tests HTTP endpoints for persistent session retrieval."""

    def test_session_summary_and_video_clips_api(self):
        client = TestClient(app)

        v_data = {
            "video_id": "api_vid_01",
            "title": "API Test Video",
            "filepath": "backend/storage/uploads/dummy.mp4",
            "duration_sec": 45.0,
            "transcript_cues": [{"start": 0.0, "end": 1.0, "text": "Hello"}],
        }
        c_data = {
            "clip_id": "api_clip_01",
            "parent_video_id": "api_vid_01",
            "title": "API Clip 1",
            "start_sec": 0.0,
            "end_sec": 30.0,
        }

        SessionStore.save_video("api_vid_01", v_data)
        SessionStore.save_clip("api_clip_01", c_data)

        # 1. Summary endpoint
        resp = client.get("/api/v1/shorts/sessions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["total_videos"] >= 1
        assert data["total_clips"] >= 1
        assert any(v["video_id"] == "api_vid_01" for v in data["videos"])

        # 2. Clips for specific video
        resp2 = client.get("/api/v1/shorts/sessions/videos/api_vid_01/clips")
        assert resp2.status_code == 200
        clips_data = resp2.json()
        assert clips_data["video_id"] == "api_vid_01"
        assert len(clips_data["clips"]) == 1
        assert clips_data["clips"][0]["clip_id"] == "api_clip_01"

    def test_feedback_endpoint_finds_persisted_clip_after_restart(self):
        client = TestClient(app)

        c_data = {
            "clip_id": "persisted_clip_for_feedback",
            "parent_video_id": "persisted_vid",
            "title": "Feedback Clip",
            "spoken_text": "Testing persistence for feedback",
            "start_sec": 0.0,
            "end_sec": 30.0,
        }
        SessionStore.save_clip("persisted_clip_for_feedback", c_data)

        # Wipe in-memory cache to simulate restart
        SessionStore._clips_cache.clear()

        feedback_payload = {
            "clip_id": "persisted_clip_for_feedback",
            "overall_rating": "good",
            "hook_rating": "strong",
            "subtitle_rating": "good",
            "framing_rating": "correct",
            "pacing_rating": "balanced",
            "approved_for_reference": True,
            "rejection_reasons": [],
            "notes": "Verified persistent session",
        }

        resp = client.post("/api/v1/shorts/clips/persisted_clip_for_feedback/feedback", json=feedback_payload)
        assert resp.status_code == 200
        assert resp.json()["status"] == "recorded"
        assert resp.json()["approved_for_reference"] is True
