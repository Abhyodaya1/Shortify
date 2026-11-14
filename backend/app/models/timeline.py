"""Universal Timeline data model and schema definition."""

from __future__ import annotations
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, model_validator, field_validator


class TrackType(str, Enum):
    VIDEO = "video"
    AUDIO = "audio"
    CAPTION = "caption"
    GRAPHICS = "graphics"
    OVERLAY = "overlay"


class ClipTransform(BaseModel):
    x: float = Field(default=0.0, description="Horizontal offset in pixels from center")
    y: float = Field(default=0.0, description="Vertical offset in pixels from center")
    scale_x: float = Field(default=1.0, ge=0.0, description="Horizontal scale multiplier")
    scale_y: float = Field(default=1.0, ge=0.0, description="Vertical scale multiplier")
    rotation: float = Field(default=0.0, description="Rotation in degrees")
    opacity: float = Field(default=1.0, ge=0.0, le=1.0, description="Alpha opacity between 0.0 and 1.0")


class Clip(BaseModel):
    clip_id: UUID = Field(default_factory=uuid4, description="Unique clip identifier")
    asset_id: Optional[str] = Field(default=None, description="Reference to source asset or file path")
    start_time_ms: int = Field(ge=0, description="Start time on the timeline in milliseconds")
    duration_ms: int = Field(gt=0, description="Duration on the timeline in milliseconds")
    source_in_ms: int = Field(default=0, ge=0, description="Trim start within source asset in milliseconds")
    source_out_ms: Optional[int] = Field(default=None, ge=0, description="Trim end within source asset in milliseconds")
    volume: float = Field(default=1.0, ge=0.0, le=2.0, description="Volume multiplier (1.0 = normal, 0 = mute)")
    playback_rate: float = Field(default=1.0, ge=0.1, le=10.0, description="Speed playback multiplier")
    transform: ClipTransform = Field(default_factory=ClipTransform, description="Spatial 2D transform")
    text_content: Optional[str] = Field(default=None, description="Text string for title/caption/graphics clips")
    style_props: Dict[str, Any] = Field(default_factory=dict, description="Visual styling (font, color, background)")

    @property
    def end_time_ms(self) -> int:
        return self.start_time_ms + self.duration_ms

    @model_validator(mode="after")
    def validate_source_boundaries(self) -> Clip:
        if self.source_out_ms is not None:
            if self.source_out_ms <= self.source_in_ms:
                raise ValueError(
                    f"source_out_ms ({self.source_out_ms}) must be strictly greater than source_in_ms ({self.source_in_ms})"
                )
        return self


class Track(BaseModel):
    track_id: UUID = Field(default_factory=uuid4, description="Unique track identifier")
    name: str = Field(default="Untitled Track", description="Human-readable track name")
    track_type: TrackType = Field(default=TrackType.VIDEO, description="Track classification")
    order: int = Field(default=0, ge=0, description="Z-order rendering layer (0 = bottom)")
    muted: bool = Field(default=False, description="Whether audio playback is muted for this track")
    locked: bool = Field(default=False, description="Whether track is locked against edits")
    clips: List[Clip] = Field(default_factory=list, description="Clips arranged sequentially on this track")

    @model_validator(mode="after")
    def validate_no_overlapping_clips(self) -> Track:
        if len(self.clips) <= 1:
            return self
        
        # Sort clips by start time
        sorted_clips = sorted(self.clips, key=lambda c: c.start_time_ms)
        for i in range(len(sorted_clips) - 1):
            current = sorted_clips[i]
            next_clip = sorted_clips[i + 1]
            if current.end_time_ms > next_clip.start_time_ms:
                raise ValueError(
                    f"Clip collision on track '{self.name}': Clip {current.clip_id} ends at {current.end_time_ms}ms "
                    f"which overlaps with Clip {next_clip.clip_id} starting at {next_clip.start_time_ms}ms"
                )
        return self


class Timeline(BaseModel):
    timeline_id: UUID = Field(default_factory=uuid4, description="Unique timeline identifier")
    project_id: UUID = Field(default_factory=uuid4, description="Associated project identifier")
    title: str = Field(default="Untitled Video Project", description="Project title")
    fps: int = Field(default=30, ge=1, le=120, description="Frames per second")
    width: int = Field(default=1920, gt=0, description="Canvas pixel width")
    height: int = Field(default=1080, gt=0, description="Canvas pixel height")
    tracks: List[Track] = Field(default_factory=list, description="All audio and video tracks")

    @property
    def aspect_ratio(self) -> str:
        gcd_val = self._gcd(self.width, self.height)
        return f"{self.width // gcd_val}:{self.height // gcd_val}"

    @property
    def duration_ms(self) -> int:
        max_duration = 0
        for track in self.tracks:
            for clip in track.clips:
                if clip.end_time_ms > max_duration:
                    max_duration = clip.end_time_ms
        return max_duration

    @property
    def total_frames(self) -> int:
        return int((self.duration_ms / 1000.0) * self.fps)

    @staticmethod
    def _gcd(a: int, b: int) -> int:
        while b:
            a, b = b, a % b
        return a

    def get_track_by_id(self, track_id: UUID) -> Optional[Track]:
        for t in self.tracks:
            if t.track_id == track_id:
                return t
        return None

    def add_track(self, name: str, track_type: TrackType, order: Optional[int] = None) -> Track:
        if order is None:
            order = len(self.tracks)
        track = Track(name=name, track_type=track_type, order=order)
        self.tracks.append(track)
        return track

    def add_clip(self, track_id: UUID, clip: Clip) -> None:
        track = self.get_track_by_id(track_id)
        if not track:
            raise ValueError(f"Track with id {track_id} not found on timeline")
        track.clips.append(clip)
        # Re-trigger validation
        track.validate_no_overlapping_clips()

