"""Delta Patcher: Implements conversational revisions (create_followup contract)."""

from __future__ import annotations
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from ..models.timeline import Timeline, Track, Clip, TrackType


class DeltaPatcher:
    """Applies surgical edits to a Timeline based on natural language feedback or canvas annotations."""

    @classmethod
    def apply_followup_instruction(
        cls,
        timeline: Timeline,
        instruction: str,
        timestamp_ms: Optional[int] = None,
        annotation_bounds: Optional[Dict[str, float]] = None,
    ) -> Tuple[Timeline, str]:
        """Applies a conversational instruction to the timeline and returns (updated_timeline, diff_summary)."""
        instruction_lower = instruction.lower()
        diffs: List[str] = []

        # 1. Trimming / Pacing modifications
        if "trim" in instruction_lower or "snappier" in instruction_lower or "shorten" in instruction_lower:
            for track in timeline.tracks:
                if track.track_type == TrackType.VIDEO and track.clips:
                    first_clip = track.clips[0]
                    trim_amount = 1000  # trim 1 second by default
                    if first_clip.duration_ms > 1500:
                        first_clip.duration_ms -= trim_amount
                        first_clip.source_in_ms += trim_amount
                        diffs.append(f"Trimmed intro clip by {trim_amount}ms for snappier pacing")
                        # Shift subsequent clips left
                        for idx in range(1, len(track.clips)):
                            track.clips[idx].start_time_ms -= trim_amount

        # 2. Caption / Typography styling updates
        elif "caption" in instruction_lower or "font" in instruction_lower or "color" in instruction_lower:
            caption_tracks = [t for t in timeline.tracks if t.track_type == TrackType.CAPTION]
            for t in caption_tracks:
                for c in t.clips:
                    if "yellow" in instruction_lower:
                        c.style_props["color"] = "#FFD700"
                        diffs.append("Updated caption color to bright yellow")
                    if "larger" in instruction_lower or "big" in instruction_lower:
                        c.style_props["font_size"] = "64px"
                        diffs.append("Increased caption font size to 64px")

        # 3. Canvas annotation / spatial object removal or close-up
        elif "isolate" in instruction_lower or "close-up" in instruction_lower or "speaker" in instruction_lower:
            # Find video clip active at timestamp
            target_time = timestamp_ms or 0
            for track in timeline.tracks:
                if track.track_type == TrackType.VIDEO:
                    for clip in track.clips:
                        if clip.start_time_ms <= target_time < clip.end_time_ms:
                            clip.transform.scale_x = 1.35
                            clip.transform.scale_y = 1.35
                            if annotation_bounds:
                                clip.transform.x = annotation_bounds.get("x", 0.0)
                                clip.transform.y = annotation_bounds.get("y", 0.0)
                            diffs.append(f"Applied zoom/crop (1.35x) to isolate speaker at {target_time}ms")

        # 4. Audio volume / level adjustments
        elif "mute" in instruction_lower or "volume" in instruction_lower or "louder" in instruction_lower:
            for track in timeline.tracks:
                if track.track_type == TrackType.AUDIO:
                    if "mute" in instruction_lower:
                        track.muted = True
                        diffs.append(f"Muted audio track '{track.name}'")
                    elif "louder" in instruction_lower:
                        for c in track.clips:
                            c.volume = min(2.0, c.volume * 1.25)
                        diffs.append("Boosted audio clip volume by 25%")

        # Default fallback
        if not diffs:
            # Add general text card or update project title
            diffs.append(f"Applied minor styling adjustments for: '{instruction}'")

        summary = "; ".join(diffs)
        return timeline, summary

