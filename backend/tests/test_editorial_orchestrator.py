"""Integration test for Step 2: Editorial Pipeline Orchestrator (Roles 01, 02, 03, 04)."""

import os
import json
import time
from pathlib import Path
import pytest
from backend.app.services.editorial_orchestrator import EditorialOrchestrator

OUTPUT_DIR = "backend/storage/clips/test_editorial_step2"


def test_editorial_orchestrator_full_chain():
    # 1. Prepare sample transcript data from actual video slice
    transcript_data = {
        "full_text": (
            "Love never hesitates. Only trust as a plaster pen, like a roaring hurricane. "
            "I will die before I walk away from what we built here. That is the ultimate test."
        ),
        "segments": [
            {"id": 0, "start": 0.0, "end": 2.5, "text": "Love never hesitates."},
            {"id": 1, "start": 2.5, "end": 6.0, "text": "Only trust as a plaster pen, like a roaring hurricane."},
            {"id": 2, "start": 6.0, "end": 9.2, "text": "I will die before I walk away from what we built here."},
            {"id": 3, "start": 9.2, "end": 12.0, "text": "That is the ultimate test."},
        ],
    }

    out_dir = Path(OUTPUT_DIR)
    t0 = time.time()

    print("\nExecuting 4-role editorial pipeline (Roles 01 -> 02 -> 03 -> 04)...")
    res = EditorialOrchestrator.run_pipeline(
        clip_id="test_clip_step2",
        transcript_data=transcript_data,
        duration_seconds=12.0,
        channel_niche="Mindset & Storytelling",
        target_audience="High-achieving creators and entrepreneurs",
        output_dir=str(out_dir),
    )
    elapsed = round(time.time() - t0, 2)
    print(f"Pipeline executed in {elapsed}s!")

    # 2. Verify hooks.json artifact was created
    hooks_json_path = out_dir / "hooks.json"
    assert hooks_json_path.exists(), "hooks.json artifact was not written"
    assert os.path.getsize(hooks_json_path) > 500

    # 3. Verify Role 01 (Analyst)
    summary = res["transcript_summary"]
    assert summary["central_idea"], "Missing central idea"
    assert summary["key_insight"], "Missing key insight"
    print(f"\n[Role 01 - Analyst] Central Idea: {summary['central_idea']}")
    print(f"[Role 01 - Analyst] Key Insight: {summary['key_insight']}")

    # 4. Verify Role 02 (Hook Strategist)
    open_cands = res["opening_candidates"]
    assert len(open_cands) >= 1, "Expected opening hook candidates"
    print(f"\n[Role 02 - Hook Strategist] Opening Candidates ({len(open_cands)}):")
    for c in open_cands:
        print(f"   - [{c.get('id')}] \"{c.get('text')}\" (Angle: {c.get('angle')})")
    assert res["recommended_selection"]["opening_hook"], "Missing recommended opening hook"

    # 5. Verify Role 03 (Headline Writer)
    headlines = res["headline_candidates"]
    assert len(headlines) >= 1, "Expected visual headline candidates"
    print(f"\n[Role 03 - Headline Writer] Visual Headlines ({len(headlines)}):")
    for h in headlines:
        print(f"   - \"{h.get('text')}\" (Emphasis: {h.get('emphasis_word')})")

    # 6. Verify Role 04 (Editorial Judge)
    audit = res["editorial_audit"]
    assert audit["decision"] in ["approved", "revise", "rejected"], f"Unexpected decision {audit['decision']}"
    assert "scores" in audit, "Missing audit scores"
    print(f"\n[Role 04 - Editorial Judge] Decision: {audit['decision'].upper()}")
    print(f"[Role 04 - Editorial Judge] Scores: {json.dumps(audit['scores'])}")
    if audit.get("critical_issues"):
        print(f"[Role 04 - Editorial Judge] Critical issues flagged: {audit['critical_issues']}")

