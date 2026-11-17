"""Animation and Visual Style Studio Data Models."""

from __future__ import annotations
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


class OpeningHookIntroConfig(BaseModel):
    enabled: bool = Field(default=True, description="Whether opening hook animation is enabled")
    hook_text: Optional[str] = Field(default=None, description="Opening viral hook text")
    style: str = Field(default="slam_in", description="Animation style: slam_in, neon_glow, typewriter, slide_up, brush_reveal")
    duration_sec: float = Field(default=3.0, ge=0.5, le=10.0, description="Duration of intro presentation")
    enter_duration_sec: float = Field(default=0.4, ge=0.05, le=2.0)
    exit_duration_sec: float = Field(default=0.3, ge=0.05, le=2.0)
    font_size: int = Field(default=48, ge=20, le=120)
    color: str = Field(default="#FFE600")
    secondary_color: str = Field(default="#FFFFFF")
    easing: str = Field(default="ease_out_back")


class AnimatedTextElementConfig(BaseModel):
    text: str = Field(default="", description="Text to animate")
    animation_type: str = Field(default="word_pop", description="word_pop, slam_in, typewriter, bounce, kinetic_fade")
    start_sec: float = Field(default=0.0, ge=0.0)
    duration_sec: float = Field(default=3.0, gt=0.0)
    font_name: str = Field(default="Arial Black")
    font_size: int = Field(default=36, ge=14, le=96)
    primary_color: str = Field(default="#FFFFFF")
    highlight_color: str = Field(default="#FFE600")
    y_position_percent: float = Field(default=20.0, ge=0.0, le=100.0)
    all_caps: bool = Field(default=True)


class MotionGraphicElementConfig(BaseModel):
    graphic_type: str = Field(default="arrow", description="arrow, callout, box, circle, highlight_brush")
    start_sec: float = Field(default=0.0, ge=0.0)
    duration_sec: float = Field(default=2.0, gt=0.0)
    x_percent: float = Field(default=50.0, ge=0.0, le=100.0)
    y_percent: float = Field(default=50.0, ge=0.0, le=100.0)
    color: str = Field(default="#00E297")
    stroke_width: int = Field(default=4, ge=1, le=20)


class GlobalVisualConfig(BaseModel):
    caption_preset_id: str = Field(default="creator_hormozi")
    layout_preset_id: str = Field(default="full_screen")
    social_card_preset_id: str = Field(default="reddit_card")
    background_preset_id: str = Field(default="dark")
    card_text_mode: Literal["hook", "title", "custom"] = Field(default="hook")
    custom_card_text: Optional[str] = None
    custom_card_author: Optional[str] = None
    custom_card_handle: Optional[str] = None
    card_vertical_position: int = Field(default=20, ge=0, le=100)
    card_width_percent: int = Field(default=92, ge=40, le=100)
    subtitle_vertical_position: int = Field(default=76, ge=0, le=100)
    custom_active_color: str = Field(default="#FFE600")
    custom_text_color: str = Field(default="#FFFFFF")
    custom_font_name: str = Field(default="Impact")
    custom_animation: str = Field(default="word_pop")
    custom_all_caps: bool = Field(default=True)
    custom_outline_width: float = Field(default=5.0, ge=0.0, le=12.0)
    intro: Optional[OpeningHookIntroConfig] = None
    hook_animation: Optional[AnimatedTextElementConfig] = None
    title_animation: Optional[AnimatedTextElementConfig] = None
    motion_graphics: List[MotionGraphicElementConfig] = Field(default_factory=list)
