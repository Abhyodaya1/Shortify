"""Dataset Store: Local storage and JSONL export for human preferences, feedback, and reference examples.
Conforms to 05_DATASET_AND_FINE_TUNING_ROADMAP.md.
"""

from __future__ import annotations
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

DATASET_DIR = Path("data/dataset")
DATASET_DIR.mkdir(parents=True, exist_ok=True)

PREFERENCES_FILE = DATASET_DIR / "preferences.jsonl"
REFERENCES_FILE = DATASET_DIR / "references.jsonl"


class ClipFeedbackSubmission(BaseModel):
    """Structured feedback submitted by human reviewer."""
    clip_id: str
    overall_rating: str = Field(default="good", description="'good', 'acceptable', or 'poor'")
    hook_rating: str = Field(default="strong", description="'strong', 'acceptable', or 'weak'")
    subtitle_rating: str = Field(default="good", description="'good', 'acceptable', or 'poor'")
    framing_rating: str = Field(default="correct", description="'correct', 'acceptable', or 'poor'")
    pacing_rating: str = Field(default="balanced", description="'balanced', 'too_fast', or 'too_slow'")
    approved_for_reference: bool = Field(default=False, description="Whether to include in benchmark references")
    rejection_reasons: List[str] = Field(default_factory=list, description="Specific failure reasons if rejected")
    edited_hook: Optional[str] = Field(default=None, description="Human-edited hook text (supervised signal)")
    edited_start_sec: Optional[float] = Field(default=None, description="Human-adjusted start timestamp")
    edited_end_sec: Optional[float] = Field(default=None, description="Human-adjusted end timestamp")
    notes: Optional[str] = Field(default="", description="Human reviewer notes")


class DatasetStore:
    """Manages appending and exporting structured human feedback records."""

    @classmethod
    def record_feedback(
        cls,
        clip_data: Dict[str, Any],
        feedback: ClipFeedbackSubmission,
    ) -> Dict[str, Any]:
        """Appends a structured preference record to preferences.jsonl."""
        record_id = f"pref_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{clip_data.get('clip_id', 'clip')}"

        record = {
            "record_id": record_id,
            "source_id": clip_data.get("parent_video_id", "source_001"),
            "candidate_id": clip_data.get("clip_id"),
            "profile_snapshot": clip_data.get("profile_snapshot", {}),
            "input": {
                "spoken_text": clip_data.get("spoken_text", ""),
                "target_duration_seconds": clip_data.get("target_duration_seconds", 31),
                "proposed_start_sec": clip_data.get("start_sec"),
                "proposed_end_sec": clip_data.get("end_sec"),
                "proposed_hook": clip_data.get("opening_hook"),
                "hook_formula": clip_data.get("hook_formula"),
                "hook_score": clip_data.get("hook_score"),
            },
            "decision": {
                "overall_rating": feedback.overall_rating,
                "hook_rating": feedback.hook_rating,
                "subtitle_rating": feedback.subtitle_rating,
                "framing_rating": feedback.framing_rating,
                "pacing_rating": feedback.pacing_rating,
                "approved_for_reference": feedback.approved_for_reference,
                "rejection_reasons": feedback.rejection_reasons,
                "notes": feedback.notes or "",
                "human_supervised_edits": {
                    "edited_hook": feedback.edited_hook,
                    "edited_start_sec": feedback.edited_start_sec,
                    "edited_end_sec": feedback.edited_end_sec,
                },
            },
            "provenance": {
                "source_rights_status": "personal_use_fair_evaluation",
                "training_eligible": feedback.approved_for_reference,
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        DATASET_DIR.mkdir(parents=True, exist_ok=True)
        with open(PREFERENCES_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

        # If approved for reference, also append to references.jsonl
        if feedback.approved_for_reference:
            with open(REFERENCES_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")

        return record

    @classmethod
    def export_dataset(cls, dataset_type: str = "preferences") -> List[Dict[str, Any]]:
        """Reads and exports all dataset records."""
        target_file = REFERENCES_FILE if dataset_type == "references" else PREFERENCES_FILE
        if not target_file.exists():
            return []

        records = []
        with open(target_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        records.append(json.loads(line.strip()))
                    except Exception:
                        pass
        return records

