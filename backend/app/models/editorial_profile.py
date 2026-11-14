"""Editorial Profile: Centralized, validated user preferences and quality guidelines."""

from __future__ import annotations
from typing import Optional, Literal
from pydantic import BaseModel, Field


class EditorialProfile(BaseModel):
    """Immutable or validated configuration governing clip selection, hook, subtitles, and framing."""

    profile_id: str = Field(default="personal_default", description="Unique profile identifier")
    version: int = Field(default=1, description="Configuration revision version")
    profile_name: str = Field(default="Personal Default", description="Human-readable profile name")

    # Core Editorial Dimensions
    hook_style: Literal["strong", "curiosity", "contrarian", "educational", "story"] = Field(
        default="strong", description="Default style for opening hooks"
    )
    subtitle_style: Literal["kinetic_editorial", "clean_podcast", "cinematic_minimal"] = Field(
        default="kinetic_editorial", description="Subtitle visual styling preset"
    )
    framing_style: Literal["speaker", "center", "two_shot"] = Field(
        default="speaker", description="Subject framing strategy"
    )
    pacing_style: Literal["balanced", "snappy", "relaxed"] = Field(
        default="balanced", description="Speech and pause pacing"
    )

    # Durations & Limits
    target_duration_seconds: int = Field(default=31, description="Target duration: 31 or 45 seconds")
    duration_tolerance_seconds: float = Field(default=2.0, description="Allowed deviation in seconds (±)")
    max_hook_words: int = Field(default=10, description="Max word count for opening hook badge")
    max_subtitle_lines: int = Field(default=2, description="Maximum subtitle lines displayed at once")

    # Typography & Subtitles
    highlight_strategy: Literal["semantic_keywords", "all_words", "punchline"] = Field(
        default="semantic_keywords", description="Word-level kinetic highlighting strategy"
    )
    accent_color_bgr: str = Field(default="&H0000D7FF&", description="ASS color for highlighted keywords (Gold/Yellow)")
    primary_color_bgr: str = Field(default="&H00FFFFFF&", description="ASS color for primary spoken words (White)")
    subtitle_safe_margin_v_ratio: float = Field(default=0.20, description="Vertical margin from bottom (0.18 - 0.22)")

    # Framing & Vision
    face_position: Literal["upper_middle", "center"] = Field(
        default="upper_middle", description="Desired face region in vertical frame"
    )
    enable_camera_pan_smoothing: bool = Field(default=True, description="Enable EMA smoothed panning between speakers")
    ema_alpha: float = Field(default=0.20, description="Exponential moving average alpha for camera pan smoothing")

    # Editorial Quality Gates
    preserve_natural_pauses: bool = Field(default=True, description="Preserve natural speech breaths and pauses")
    allow_editorial_hook_overlay: bool = Field(default=True, description="Allow overlay badge if hook is not verbatim spoken")
    require_contextual_payoff: bool = Field(default=True, description="Hard reject clips without meaningful payoff")
    reject_misleading_hooks: bool = Field(default=True, description="Hard reject sensational hooks that clip does not deliver")

    def snapshot(self) -> dict:
        """Produces a JSON-serializable snapshot of this profile at this exact point in time."""
        return self.model_dump()

