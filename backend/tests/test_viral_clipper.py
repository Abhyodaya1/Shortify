"""Tests for Viral Clipper, Hook Scoring, and Dead-Air Editing Engine."""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.viral_clipper import ViralHookScorer, DeadAirDetector, ViralClipperService

client = TestClient(app)

SAMPLE_TRANSCRIPT = """
1
00:00:00,000 --> 00:00:03,500
Um, basically today we are going to look at YouTube hooks.

2
00:00:05,000 --> 00:00:10,200
You are losing 14 hours every single week editing clips manually before you discover this AI tool.

3
00:00:11,500 --> 00:00:17,800
Here is the exact mechanism that saves your channel from dying on the 0:30 retention cliff.

4
00:00:18,200 --> 00:00:24,500
We tested this across 50 videos and the completion rate jumped by 42 percent immediately.

5
00:00:25,000 --> 00:00:30,000
So stop doing it by hand and let the autonomous pipeline assemble your vertical compositions.
"""


def test_hook_scorer_direct():
    res = ViralHookScorer.score_hook(
        "You are losing 14 hours every week editing clips manually before you discover this AI"
    )
    assert "overall_score" in res
    assert "verdict" in res
    assert res["verdict"] in ("WORKABLE", "STRONG")
    assert res["metrics"]["stakes"] >= 50
    assert res["metrics"]["brevity"] == 100
    assert "weakest" in res


def test_dead_air_detection():
    cues = DeadAirDetector.load_transcript(SAMPLE_TRANSCRIPT)
    assert len(cues) == 5
    analysis = DeadAirDetector.find_dead_air(cues, floor=0.4)
    assert analysis["total_cuts"] >= 1
    assert analysis["time_saved_sec"] > 0
    # Cues have a gap between 03.500 and 05.000 (1.5s silence)
    gap_cuts = [c for c in analysis["cuts"] if c["type"] == "DEAD_AIR"]
    assert len(gap_cuts) >= 1


def test_viral_clipper_service():
    res = ViralClipperService.process_transcript_to_clips(SAMPLE_TRANSCRIPT)
    assert res["status"] == "success"
    assert len(res["top_candidates"]) >= 1
    top_cand = res["top_candidates"][0]
    assert "best_hook" in top_cand
    assert top_cand["best_hook"]["overall_score"] >= 40

    timeline = ViralClipperService.assemble_short_timeline(top_cand, aspect_ratio="9:16")
    assert timeline.width == 1080
    assert timeline.height == 1920
    assert timeline.tracks[0].track_type.value == "video"
    assert timeline.tracks[1].track_type.value == "caption"


def test_viral_api_endpoints():
    # 1. Score hook
    score_res = client.post(
        "/api/v1/viral/score-hook",
        json={"hook_text": "Stop wasting 20 hours editing videos before you check this out"},
    )
    assert score_res.status_code == 200
    data = score_res.json()
    assert data["verdict"] in ("WORKABLE", "STRONG")

    # 2. Analyze transcript
    trans_res = client.post(
        "/api/v1/viral/analyze-transcript",
        json={"transcript_text": SAMPLE_TRANSCRIPT, "target_platform": "shorts"},
    )
    assert trans_res.status_code == 200
    trans_data = trans_res.json()
    assert len(trans_data["top_candidates"]) >= 1

    # 3. Create Short Timeline
    candidate = trans_data["top_candidates"][0]
    short_res = client.post(
        "/api/v1/viral/create-short",
        json={"candidate_data": candidate, "aspect_ratio": "9:16"},
    )
    assert short_res.status_code == 201
    short_data = short_res.json()
    assert "job_id" in short_data
    assert short_data["timeline"]["height"] == 1920

