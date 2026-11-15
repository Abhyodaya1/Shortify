"""Tests for Dynamic Shorts Selection, Bulk Publishing & IST Automated Scheduling
Validates all requirements of the Master Implementation Specification.
"""

import pytest
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from fastapi.testclient import TestClient

from backend.app.services.clip_selector import SmartClipSelector
from backend.app.services.timezone_service import TimezoneService, IST
from backend.app.services.persistent_scheduler import PersistentScheduler
from backend.app.main import app

client = TestClient(app)


def test_dynamic_selection_spec_examples():
    """Validates the exact virality threshold (> 60) and fallback rule examples from the spec.

    Spec table:
    1. [92, 85, 76, 68, 61, 49, 35] -> 5 qualifying Shorts
    2. [99, 91, 82, 75, 63, 60, 42] -> 5 qualifying Shorts (60 doesn't qualify)
    3. [88, 74, 61, 60, 55, 43]     -> 3 qualifying Shorts
    4. [60, 58, 55, 42, 31]         -> Top 5 fallback
    5. [59, 52, 41]                 -> All 3 fallback
    6. [85, 78]                     -> 2 qualifying Shorts
    7. []                           -> 0 Shorts
    """
    def make_cands(scores):
        return [{"clip_id": f"c_{i}", "virality_score": s, "visual_headline": f"Hook {i}"} for i, s in enumerate(scores)]

    # Example 1: [92, 85, 76, 68, 61, 49, 35] -> 5 qualifying
    res1 = SmartClipSelector.apply_dynamic_selection(make_cands([92, 85, 76, 68, 61, 49, 35]))
    assert len(res1["selected_clips"]) == 5
    assert res1["is_fallback"] is False
    assert res1["selection_mode"] == "threshold"
    assert res1["batch_message"] == "Selected all 5 Shorts with virality scores above 60."
    assert all(c["passed_threshold"] is True for c in res1["selected_clips"])
    assert all(c["is_fallback"] is False for c in res1["selected_clips"])
    # Clip titles reindexed 1..5
    assert res1["selected_clips"][0]["title"].startswith("#1 ")
    assert res1["selected_clips"][4]["title"].startswith("#5 ")

    # Example 2: [99, 91, 82, 75, 63, 60, 42] -> 5 qualifying (score of 60 does NOT qualify)
    res2 = SmartClipSelector.apply_dynamic_selection(make_cands([99, 91, 82, 75, 63, 60, 42]))
    assert len(res2["selected_clips"]) == 5
    assert res2["is_fallback"] is False
    assert res2["selection_mode"] == "threshold"
    assert [c["virality_score"] for c in res2["selected_clips"]] == [99, 91, 82, 75, 63]

    # Example 3: [88, 74, 61, 60, 55, 43] -> 3 qualifying
    res3 = SmartClipSelector.apply_dynamic_selection(make_cands([88, 74, 61, 60, 55, 43]))
    assert len(res3["selected_clips"]) == 3
    assert res3["is_fallback"] is False
    assert [c["virality_score"] for c in res3["selected_clips"]] == [88, 74, 61]

    # Example 4: [60, 58, 55, 42, 31] -> Top 5 fallback (zero scored > 60)
    res4 = SmartClipSelector.apply_dynamic_selection(make_cands([60, 58, 55, 42, 31]))
    assert len(res4["selected_clips"]) == 5
    assert res4["is_fallback"] is True
    assert res4["selection_mode"] == "fallback"
    assert res4["batch_message"] == "No Shorts scored above 60. Showing the top 5 available candidates."
    assert all(c["passed_threshold"] is False for c in res4["selected_clips"])
    assert all(c["is_fallback"] is True for c in res4["selected_clips"])

    # Example 5: [59, 52, 41] -> All 3 fallback
    res5 = SmartClipSelector.apply_dynamic_selection(make_cands([59, 52, 41]))
    assert len(res5["selected_clips"]) == 3
    assert res5["is_fallback"] is True
    assert res5["batch_message"] == "No Shorts scored above 60. Showing the top 3 available candidates."

    # Example 6: [85, 78] -> 2 qualifying Shorts
    res6 = SmartClipSelector.apply_dynamic_selection(make_cands([85, 78]))
    assert len(res6["selected_clips"]) == 2
    assert res6["is_fallback"] is False
    assert res6["batch_message"] == "Selected all 2 Shorts with virality scores above 60."

    # Example 7: [] -> 0 Shorts
    res7 = SmartClipSelector.apply_dynamic_selection([])
    assert len(res7["selected_clips"]) == 0
    assert res7["selection_mode"] == "empty"


def test_selection_transparency_annotations():
    """Ensures each selected candidate has virality_score, candidate_rank, passed_threshold, is_fallback, selection_reason."""
    cands = [
        {"clip_id": "c1", "virality_score": 75, "visual_headline": "Secret of Focus"},
        {"clip_id": "c2", "virality_score": 65, "visual_headline": "Why Habits Fail"},
        {"clip_id": "c3", "virality_score": 45, "visual_headline": "Morning Routine"},
    ]
    res = SmartClipSelector.apply_dynamic_selection(cands)
    assert len(res["selected_clips"]) == 2
    c0 = res["selected_clips"][0]
    assert c0["virality_score"] == 75
    assert c0["candidate_rank"] == 1
    assert c0["passed_threshold"] is True
    assert c0["is_fallback"] is False
    assert "exceeds qualification threshold of 60" in c0["selection_reason"]
    assert c0["title"] == "#1 Secret of Focus"

    c1 = res["selected_clips"][1]
    assert c1["virality_score"] == 65
    assert c1["candidate_rank"] == 2
    assert c1["passed_threshold"] is True
    assert c1["is_fallback"] is False
    assert c1["title"] == "#2 Why Habits Fail"


def test_ist_timezone_service_accuracy():
    """Validates Indian Standard Time (Asia/Kolkata) UTC conversion and display formatting."""
    # 06:30 PM IST (18:30) on 2026-11-20 is exactly 01:00 PM UTC (13:00)
    ist_time_str = "2026-11-20T18:30:00"
    utc_iso = TimezoneService.to_utc_iso(ist_time_str)
    assert utc_iso == "2026-11-20T13:00:00Z"

    # Convert back from UTC to IST
    ist_iso = TimezoneService.utc_to_ist_iso(utc_iso)
    assert "+05:30" in ist_iso
    assert "18:30:00" in ist_iso

    # Human-readable IST display
    display = TimezoneService.format_ist_display(utc_iso)
    assert "20 Nov 2026" in display
    assert "06:30 PM" in display
    assert "IST" in display

    # Validation: past time should fail, future time should succeed
    now_ist = TimezoneService.now_ist()
    future_ist = now_ist + timedelta(hours=2)
    past_ist = now_ist - timedelta(hours=2)

    is_valid_future, _ = TimezoneService.validate_future_ist(future_ist.isoformat())
    assert is_valid_future is True

    is_valid_past, err = TimezoneService.validate_future_ist(past_ist.isoformat())
    assert is_valid_past is False
    assert "must be in the future" in err


def test_bulk_ist_schedule_generation():
    """Validates generating sequential IST timestamps with interval minutes."""
    start_ist = "2026-11-20T14:00:00"
    seq = TimezoneService.generate_bulk_ist_schedule(start_ist, count=4, interval_minutes=30)
    assert len(seq) == 4

    # Clip 1: 14:00 IST -> 08:30 UTC
    assert seq[0]["utc_iso"] == "2026-11-20T08:30:00Z"
    assert "02:00 PM" in seq[0]["display_ist"]
    assert "IST" in seq[0]["display_ist"]

    # Clip 2: 14:30 IST -> 09:00 UTC
    assert seq[1]["utc_iso"] == "2026-11-20T09:00:00Z"
    assert "02:30 PM" in seq[1]["display_ist"]
    assert "IST" in seq[1]["display_ist"]

    # Clip 3: 15:00 IST -> 09:30 UTC
    assert seq[2]["utc_iso"] == "2026-11-20T09:30:00Z"

    # Clip 4: 15:30 IST -> 10:00 UTC
    assert seq[3]["utc_iso"] == "2026-11-20T10:00:00Z"


def test_bulk_schedule_api_endpoint():
    """Validates POST /api/v1/youtube/bulk-schedule with IST timestamps."""
    start_time = (TimezoneService.now_ist() + timedelta(days=1)).strftime("%Y-%m-%dT18:00:00")
    payload = {
        "start_time_ist": start_time,
        "interval_minutes": 45,
        "items": [
            {
                "clip_id": "bulk_c1",
                "title": "#1 Master Deep Work",
                "description": "Essential focus guide.",
                "tags": ["Focus", "Productivity"],
                "scheduled_time": start_time,
                "target_channel_id": "UC_sandbox_test",
                "visibility": "unlisted"
            },
            {
                "clip_id": "bulk_c2",
                "title": "#2 Eliminate Distraction",
                "description": "How to stay in flow.",
                "tags": ["Focus", "Study"],
                "scheduled_time": start_time,
                "target_channel_id": "UC_sandbox_test",
                "visibility": "unlisted"
            }
        ]
    }

    res = client.post("/api/v1/youtube/bulk-schedule", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["total_scheduled"] == 2
    assert data["timezone"] == "Asia/Kolkata"
    assert "IST" in data["display_timezone"]

    # Verify both jobs were persisted in UTC in database
    jobs = PersistentScheduler.list_scheduled_uploads("UC_sandbox_test")
    job_ids = [j["job_id"] for j in data["jobs"]]
    matched = [j for j in jobs if j["job_id"] in job_ids]
    assert len(matched) == 2
    # Verify UTC timestamp format
    assert matched[0]["scheduled_time"].endswith("Z")
    assert matched[1]["scheduled_time"].endswith("Z")
    # Verify interval of 45 minutes between them
    t1 = datetime.fromisoformat(matched[0]["scheduled_time"].replace("Z", "+00:00"))
    t2 = datetime.fromisoformat(matched[1]["scheduled_time"].replace("Z", "+00:00"))
    assert (t2 - t1).total_seconds() == 45 * 60


def test_bulk_publish_endpoint_with_failure_isolation(tmp_path):
    """Validates POST /api/v1/youtube/bulk-publish sequential execution and error isolation."""
    # Create one valid rendered video file (> 1000 bytes)
    valid_video = tmp_path / "valid_short.mp4"
    valid_video.write_bytes(b"0" * 2000)

    # Item 1: valid video file
    # Item 2: missing video file (must record failure without aborting Item 1)
    payload = {
        "items": [
            {
                "clip_id": "pub_valid_1",
                "title": "Valid Rendered Clip",
                "description": "High quality Short",
                "tags": ["Test"],
                "video_file_path": str(valid_video),
                "visibility": "unlisted",
                "target_channel_id": "UC_sandbox_pub"
            },
            {
                "clip_id": "pub_missing_2",
                "title": "Missing Video Clip",
                "description": "Will fail file check",
                "tags": ["Test"],
                "video_file_path": str(tmp_path / "non_existent.mp4"),
                "visibility": "unlisted",
                "target_channel_id": "UC_sandbox_pub"
            }
        ]
    }

    res = client.post("/api/v1/youtube/bulk-publish", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "completed"
    assert data["total_requested"] == 2
    assert data["published_count"] == 1
    assert data["failed_count"] == 1
    assert data["published"][0]["clip_id"] == "pub_valid_1"
    assert data["failed"][0]["clip_id"] == "pub_missing_2"
    err_msg = data["failed"][0]["error"].lower()
    assert "could not be resolved" in err_msg or "missing" in err_msg


def test_batch_status_endpoint():
    """Validates GET /api/v1/youtube/batch-status."""
    res = client.get("/api/v1/youtube/batch-status")
    assert res.status_code == 200
    data = res.json()
    assert "total_jobs" in data
    assert "scheduled_count" in data
    assert "published_count" in data
    assert "verified_rendered_files_count" in data
    assert data["timezone"] == "Asia/Kolkata"
