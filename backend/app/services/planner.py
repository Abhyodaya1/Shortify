"""Sequence Planner: Converts user briefs and media into structured Timelines."""

from __future__ import annotations
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from ..models.timeline import Timeline, Track, Clip, TrackType, ClipTransform
from .llm_provider import BaseLLMProvider, get_llm_provider


class SequencePlanner:
    """Plans and constructs a full video Timeline using LLM reasoning and media analysis."""

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self.llm_provider = llm_provider or get_llm_provider()

    async def plan_timeline(
        self,
        prompt: str,
        engine: str = "gva",
        effort: str = "standard",
        aspect_ratio: str = "16:9",
        attachments: Optional[List[str]] = None,
        style_reference_url: Optional[str] = None,
        design_md: Optional[str] = None,
    ) -> Timeline:
        attachments = attachments or []
        width, height = self._dimensions_from_aspect_ratio(aspect_ratio)

        system_instruction = (
            "You are the General Video Agent (GVA) Sequence Planner. "
            "Your task is to analyze the user's video brief, style reference, and media attachments, "
            "then produce a structured JSON timeline plan with video, audio, and caption tracks. "
            "Ensure that clips on the same track NEVER overlap. "
            "Every clip must have start_time_ms, duration_ms, and appropriate source offsets."
        )

        user_prompt = (
            f"Video Brief: {prompt}\n"
            f"Engine: {engine} (Effort: {effort})\n"
            f"Target Aspect Ratio: {aspect_ratio} ({width}x{height})\n"
            f"Available Media Attachments: {attachments}\n"
            f"Style Reference: {style_reference_url or 'None'}\n"
            f"Brand Design Guidelines: {design_md or 'Default clean styling'}\n"
            "Return JSON matching the track and clip schema."
        )

        response = await self.llm_provider.generate_completion(
            prompt=user_prompt,
            system_instruction=system_instruction,
        )

        plan_data = response.parsed_json or {}
        return self._build_timeline_from_plan(
            plan_data=plan_data,
            title=plan_data.get("title", "GVA Generated Project"),
            width=width,
            height=height,
            fps=30,
        )

    def _build_timeline_from_plan(
        self,
        plan_data: Dict[str, Any],
        title: str,
        width: int,
        height: int,
        fps: int = 30,
    ) -> Timeline:
        timeline = Timeline(
            title=title,
            width=width,
            height=height,
            fps=fps,
        )

        raw_tracks = plan_data.get("tracks", [])
        if not isinstance(raw_tracks, list) or not raw_tracks:
            raw_tracks = [
                {
                    "name": "Video Track 1",
                    "track_type": "video",
                    "clips": [{"start_time_ms": 0, "duration_ms": 5000, "source": "video_clip_1", "source_in_ms": 0}],
                },
                {
                    "name": "Audio Track 1",
                    "track_type": "audio",
                    "clips": [{"start_time_ms": 0, "duration_ms": 5000, "source": "audio_clip_1"}],
                },
                {
                    "name": "Caption Track 1",
                    "track_type": "caption",
                    "clips": [{"start_time_ms": 0, "duration_ms": 5000, "text_content": "Introduction", "style_props": {"color": "#FFFFFF", "font_size": "48px"}}],
                },
            ]

        for order_idx, raw_track in enumerate(raw_tracks):
            if isinstance(raw_track, str):
                raw_track = {"track_type": raw_track, "name": f"{raw_track.title()} Track"}
            elif not isinstance(raw_track, dict):
                continue

            raw_type = raw_track.get("track_type", raw_track.get("type", "video"))
            if not isinstance(raw_type, str):
                raw_type = "video"
            raw_type = raw_type.lower()
            try:
                track_type = TrackType(raw_type)
            except ValueError:
                track_type = TrackType.VIDEO

            track_name = raw_track.get("name", f"Track {order_idx + 1}")
            track = timeline.add_track(name=track_name, track_type=track_type, order=order_idx)

            raw_clips = raw_track.get("clips", [])
            if not isinstance(raw_clips, list):
                raw_clips = []
            for c in raw_clips:
                if not isinstance(c, dict):
                    continue
                clip = Clip(
                    asset_id=c.get("asset_id") or c.get("source"),
                    start_time_ms=int(c.get("start_time_ms", 0)),
                    duration_ms=int(c.get("duration_ms", 1000)),
                    source_in_ms=int(c.get("source_in_ms", c.get("source_offset_ms", 0))),
                    source_out_ms=int(c["source_out_ms"]) if c.get("source_out_ms") is not None else None,
                    volume=float(c.get("volume", 1.0)),
                    text_content=c.get("text_content"),
                    style_props=c.get("style_props", {}) if isinstance(c.get("style_props"), dict) else {},
                )
                try:
                    timeline.add_clip(track.track_id, clip)
                except Exception:
                    pass

        if len(timeline.tracks) < 2:
            timeline.add_track(name="Audio Master", track_type=TrackType.AUDIO, order=len(timeline.tracks))

        return timeline

    @staticmethod
    def _dimensions_from_aspect_ratio(aspect_ratio: str) -> tuple[int, int]:
        mapping = {
            "16:9": (1920, 1080),
            "9:16": (1080, 1920),
            "1:1": (1080, 1080),
            "4:5": (1080, 1350),
            "21:9": (2560, 1080),
        }
        return mapping.get(aspect_ratio, (1920, 1080))

