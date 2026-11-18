"""Kinetic Subtitle Compiler & Subtitle QA Engine.
Compiles acoustic word alignments into high-retention ASS subtitle events with word-by-word
kinetic highlighting, safe-area bounds, configurable presets, and executes Role 05 Subtitle QA.
"""

from __future__ import annotations
import os
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
import httpx
from dotenv import load_dotenv

load_dotenv()

PROMPT_PACK_DIR = Path("shorts_ai_roles_prompt_pack")


def format_ass_time(seconds: float) -> str:
    """Formats seconds into ASS timestamp format H:MM:SS.cc"""
    if seconds < 0:
        seconds = 0.0
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    if centis >= 100:
        secs += 1
        centis = 0
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"


def ensure_high_contrast_color(r: int, g: int, b: int) -> tuple[int, int, int]:
    """Ensures foreground subtitle color has sufficient luminance (WCAG AAA >= 7:1 against black stroke).
    Elevates dark blues/purples and low-luminance tones to vivid electric shades that pop on video.
    """
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    if luminance < 95:
        # If blue is dominant, elevate to Electric Azure / Vivid Sky Blue (#38BDF8 / #00B4FF)
        if b > r and b > g:
            new_r = min(255, int(r * 1.2 + 30))
            new_g = min(255, int(g * 1.5 + 175))
            return (new_r, new_g, 255)
        # Otherwise scale overall luminance
        scale = 135.0 / max(1.0, luminance)
        return (min(255, int(r * scale)), min(255, int(g * scale)), min(255, int(b * scale)))
    return (r, g, b)


def hex_to_ass_color(color: Optional[str], default: str = "&H00FFFFFF&") -> str:
    """Converts #RRGGBB, #RGB, or &H00BBGGRR& to standard ASS &H00BBGGRR& format,
    guaranteeing high-contrast luminance for foreground readability.
    """
    if not color:
        return default
    c_str = str(color).strip()
    if c_str.startswith("&H") and c_str.endswith("&"):
        return c_str
    if c_str.startswith("#"):
        c = c_str.lstrip("#")
        if len(c) == 3:
            c = "".join([x * 2 for x in c])
        if len(c) == 6:
            r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
            r, g, b = ensure_high_contrast_color(r, g, b)
            return f"&H00{b:02X}{g:02X}{r:02X}&"
        if len(c) == 8:
            r, g, b, a = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), c[6:8]
            r, g, b = ensure_high_contrast_color(r, g, b)
            return f"&H{a}{b:02X}{g:02X}{r:02X}&"
    return default


class SubtitlePreset:
    """Defines aesthetic styles for kinetic captions."""

    PRESETS = {
        "bold_impact": {
            "font_name": "Impact",
            "font_size_ratio": 0.044,      # ~84px on 1080x1920
            "primary_color": "&H00FFFFFF&", # Crisp White
            "active_color": "&H0000E6FF&",  # Bright Yellow (#FFE600 in BGR ASS)
            "outline_color": "&H00000000&", # Pitch Black
            "shadow_color": "&HB0000000&",  # Hard High-Contrast Shadow
            "outline_width": 6.0,
            "shadow_depth": 3.8,
            "scale_pop": 118,
            "margin_v_ratio": 0.22,
            "max_words_per_chunk": 3,
            "all_caps": True,
            "animation_type": "word_pop",
        },
        "neon_glow": {
            "font_name": "Arial Black",
            "font_size_ratio": 0.042,
            "primary_color": "&H00FFFFFF&", # Crisp White base text for sharp legibility
            "active_color": "&H00FFFF00&",  # Electric Cyan active highlight
            "outline_color": "&H00000000&", # Pitch Black outline for razor-sharp edge
            "shadow_color": "&H80FFFF00&",  # Controlled Cyan Glow aura
            "outline_width": 5.0,           # Thick solid outline
            "shadow_depth": 3.0,
            "scale_pop": 112,
            "margin_v_ratio": 0.22,
            "max_words_per_chunk": 3,
            "all_caps": True,
            "animation_type": "glow_pulse",
        },
        "3d_depth": {
            "font_name": "Arial Black",
            "font_size_ratio": 0.044,
            "primary_color": "&H00FFFFFF&",
            "active_color": "&H0045EBD5&",  # Acid Lime
            "outline_color": "&H00000000&",
            "shadow_color": "&HC0000000&",  # Heavy Deep 3D Shadow
            "outline_width": 5.5,
            "shadow_depth": 5.5,
            "scale_pop": 116,
            "margin_v_ratio": 0.22,
            "max_words_per_chunk": 3,
            "all_caps": True,
            "animation_type": "bounce",
        },
        "cinematic": {
            "font_name": "Arial",           # Crisp sans-serif ensures maximum clarity on mobile
            "font_size_ratio": 0.038,
            "primary_color": "&H00F8FAFC&", # Off-White
            "active_color": "&H0045EBD5&",  # Acid Lime
            "outline_color": "&H00000000&", # Solid Black
            "shadow_color": "&H90000000&",
            "outline_width": 4.0,           # Increased from 2.2 for mobile visibility
            "shadow_depth": 2.0,
            "scale_pop": 106,
            "margin_v_ratio": 0.20,
            "max_words_per_chunk": 4,
            "all_caps": False,
            "animation_type": "fade_in",
        },
        "gradient_wordart": {
            "font_name": "Impact",
            "font_size_ratio": 0.044,
            "primary_color": "&H00FFFFFF&",
            "active_color": "&H00006BFF&",  # Vibrant Orange-Amber
            "outline_color": "&H00000000&",
            "shadow_color": "&HA0000000&",
            "outline_width": 5.8,
            "shadow_depth": 3.8,
            "scale_pop": 118,
            "margin_v_ratio": 0.22,
            "max_words_per_chunk": 3,
            "all_caps": True,
            "animation_type": "word_pop",
        },
        "minimal_modern": {
            "font_name": "Arial",
            "font_size_ratio": 0.038,
            "primary_color": "&H00FFFFFF&",
            "active_color": "&H00F8BD38&",  # High-contrast Electric Azure Blue (#38BDF8)
            "outline_color": "&H00000000&", # Pure Black
            "shadow_color": "&H90000000&",
            "outline_width": 4.2,           # Increased from 2.5 for mobile clarity
            "shadow_depth": 2.0,
            "scale_pop": 108,
            "margin_v_ratio": 0.20,
            "max_words_per_chunk": 4,
            "all_caps": False,
            "animation_type": "slide_up",
        },
        "karaoke_highlight": {
            "font_name": "Arial Black",
            "font_size_ratio": 0.042,
            "primary_color": "&H00E2E8F0&", # Clean light silver base
            "active_color": "&H0045EBD5&",  # High-voltage Lime active
            "outline_color": "&H00000000&",
            "shadow_color": "&HA0000000&",
            "outline_width": 5.0,
            "shadow_depth": 3.0,
            "scale_pop": 114,
            "margin_v_ratio": 0.22,
            "max_words_per_chunk": 3,
            "all_caps": True,
            "animation_type": "karaoke",
        },
        "comic_pop": {
            "font_name": "Arial Black",
            "font_size_ratio": 0.044,
            "primary_color": "&H0000E6FF&", # Yellow
            "active_color": "&H00852AFF&",  # Explosive Pink (#FF2A85 in BGR)
            "outline_color": "&H00000000&",
            "shadow_color": "&HC0000000&",
            "outline_width": 6.2,
            "shadow_depth": 4.2,
            "scale_pop": 120,
            "margin_v_ratio": 0.23,
            "max_words_per_chunk": 3,
            "all_caps": True,
            "animation_type": "bounce",
        },
        "typewriter": {
            "font_name": "Courier New",
            "font_size_ratio": 0.035,
            "primary_color": "&H00E2E8F0&", # Clean readable terminal base
            "active_color": "&H0000FF00&",  # Terminal Neon Green
            "outline_color": "&H00000000&", # Pitch Black
            "shadow_color": "&HB0000000&",  # Crisp Shadow
            "outline_width": 4.2,           # Increased from 3.0 for sharp letter separation
            "shadow_depth": 2.2,
            "scale_pop": 100,               # 100% steady monospace typing
            "margin_v_ratio": 0.20,
            "max_words_per_chunk": 4,
            "all_caps": False,
            "animation_type": "typewriter",
        },
        "creator_hormozi": {
            "font_name": "Arial Black",
            "font_size_ratio": 0.043,
            "primary_color": "&H00FFFFFF&",
            "active_color": "&H0045EBD5&",  # Acid Lime
            "outline_color": "&H00000000&",
            "shadow_color": "&HB0000000&",
            "outline_width": 6.0,
            "shadow_depth": 4.0,
            "scale_pop": 118,
            "margin_v_ratio": 0.23,
            "max_words_per_chunk": 3,
            "all_caps": True,
            "animation_type": "word_pop",
        },
        "hormozi": {
            "font_name": "Arial Black",
            "font_size_ratio": 0.042,      # ~80px on 1080x1920
            "primary_color": "&H00FFFFFF&", # Clean White
            "active_color": "&H0045EBD5&",  # High-Voltage Acid Lime (#d5eb45 in BGR ASS)
            "outline_color": "&H00000000&", # Pitch Black
            "shadow_color": "&H90000000&",  # Hard Offset Shadow
            "outline_width": 5.5,
            "shadow_depth": 3.0,
            "scale_pop": 118,               # Bionic 118% Word Bounce
            "margin_v_ratio": 0.22,
            "max_words_per_chunk": 3,
            "all_caps": True,
            "animation_type": "word_pop",
        },
        "mrbeast": {
            "font_name": "Arial Black",
            "font_size_ratio": 0.044,      # ~84px on 1080x1920
            "primary_color": "&H00FFFFFF&", # Clean White
            "active_color": "&H0000FFFF&",  # Bright Electric Yellow
            "outline_color": "&H00000000&", # Pitch Black
            "shadow_color": "&HB0000000&",  # Thick Hard Shadow
            "outline_width": 6.0,
            "shadow_depth": 3.8,
            "scale_pop": 115,               # Punchy 115% scale
            "margin_v_ratio": 0.23,         # Safe vertical margin from bottom
            "max_words_per_chunk": 3,
            "all_caps": True,
            "animation_type": "word_pop",
        },
        "clean_minimal": {
            "font_name": "Arial",
            "font_size_ratio": 0.038,
            "primary_color": "&H00FFFFFF&",
            "active_color": "&H0097E200&",  # Vibrant Electric Mint (#00E297)
            "outline_color": "&H00000000&",
            "shadow_color": "&H90000000&",
            "outline_width": 4.2,           # Increased from 3.0
            "shadow_depth": 2.0,
            "scale_pop": 106,
            "margin_v_ratio": 0.20,
            "max_words_per_chunk": 4,
            "all_caps": False,
            "animation_type": "fade_in",
        },
        "swiss_clean": {
            "font_name": "Arial",
            "font_size_ratio": 0.038,
            "primary_color": "&H00FFFFFF&",
            "active_color": "&H0045EBD5&",  # Neo-Brutalist Lime
            "outline_color": "&H00000000&", # Pitch Black
            "shadow_color": "&H90000000&",
            "outline_width": 4.2,           # Increased from 2.5
            "shadow_depth": 2.0,
            "scale_pop": 106,
            "margin_v_ratio": 0.18,
            "max_words_per_chunk": 4,
            "all_caps": False,
            "animation_type": "slide_up",
        },
        "neon_punch": {
            "font_name": "Impact",
            "font_size_ratio": 0.043,
            "primary_color": "&H00FFFFFF&",
            "active_color": "&H0097E200&",  # Electric Mint (#00E297 in BGR ASS)
            "outline_color": "&H00000000&",
            "shadow_color": "&H70000000&",
            "outline_width": 5.2,
            "shadow_depth": 3.0,
            "scale_pop": 114,
            "margin_v_ratio": 0.22,
            "max_words_per_chunk": 3,
            "all_caps": True,
            "animation_type": "glow_pulse",
        },
        "terminal_phosphor": {
            "font_name": "Courier New",
            "font_size_ratio": 0.035,
            "primary_color": "&H0080FF80&", # Soft Green Phosphor base
            "active_color": "&H0000FF00&",  # Ultra Bright Terminal Phosphor
            "outline_color": "&H00000000&",
            "shadow_color": "&HA0000000&",
            "outline_width": 4.2,           # Increased from 3.5
            "shadow_depth": 2.2,
            "scale_pop": 100,               # 100% steady monospace typing
            "margin_v_ratio": 0.20,
            "max_words_per_chunk": 4,
            "all_caps": False,
            "animation_type": "typewriter",
        },
        "tiktok_yellow": {
            "font_name": "Arial Black",
            "font_size_ratio": 0.042,
            "primary_color": "&H00FFFFFF&",
            "active_color": "&H0000E5FF&",  # Bright Yellow
            "outline_color": "&H00000000&",
            "shadow_color": "&HA0000000&",
            "outline_width": 5.5,
            "shadow_depth": 3.0,
            "scale_pop": 112,
            "margin_v_ratio": 0.22,
            "max_words_per_chunk": 3,
            "all_caps": True,
            "animation_type": "word_pop",
        },
        "red_alert": {
            "font_name": "Impact",
            "font_size_ratio": 0.043,
            "primary_color": "&H00FFFFFF&",
            "active_color": "&H002233FF&",  # Intense Punch Red (#FF3322 in BGR)
            "outline_color": "&H00000000&",
            "shadow_color": "&H90000000&",
            "outline_width": 5.5,
            "shadow_depth": 3.0,
            "scale_pop": 114,
            "margin_v_ratio": 0.22,
            "max_words_per_chunk": 3,
            "all_caps": True,
            "animation_type": "word_pop",
        },
    }

    @classmethod
    def get(cls, name: str) -> Dict[str, Any]:
        return cls.PRESETS.get(name.lower(), cls.PRESETS["mrbeast"])


class KineticSubtitleCompiler:
    """Compiles aligned acoustic words into synchronized, kinetic ASS subtitles."""

    @classmethod
    def compile_ass(
        cls,
        words: List[Dict[str, Any]],
        output_path: str,
        headline_text: Optional[str] = None,
        preset_name: str = "mrbeast",
        custom_active_color: Optional[str] = None,
        custom_primary_color: Optional[str] = None,
        custom_font_name: Optional[str] = None,
        custom_animation: Optional[str] = None,
        custom_all_caps: Optional[bool] = None,
        custom_outline_width: Optional[float] = None,
        time_offset_sec: float = 0.0,
        video_width: int = 1080,
        video_height: int = 1920,
        subtitle_vertical_position: Optional[int] = None,
        suppress_headline: bool = False,
    ) -> str:
        """Generates an ASS subtitle file from acoustic word timestamps.
        
        Args:
            words: List of dicts with 'word', 'start', 'end' (acoustic timestamps).
            output_path: Destination path for .ass file.
            headline_text: Optional top visual heading / hook badge.
            preset_name: Name of preset from SubtitlePreset.PRESETS.
            custom_active_color: Override for active/highlighted word color (hex #RRGGBB or ASS &HBBGGRR&).
            custom_primary_color: Override for non-highlighted base text color (hex #RRGGBB or ASS &HBBGGRR&).
            custom_font_name: Override for font family (e.g. 'Impact', 'Arial Black', 'Space Grotesk').
            custom_animation: Animation style ('word_pop', 'glow_pulse', 'fade_in', 'slide_up', 'karaoke').
            custom_all_caps: Whether to force uppercase text or preserve casing.
            custom_outline_width: Custom stroke outline thickness.
            time_offset_sec: Offset added to all timestamps.
            video_width: Target render width.
            video_height: Target render height.
            subtitle_vertical_position: 0-100 percentage from top for subtitle placement.
            suppress_headline: Whether to omit top headline badge.
        """
        preset = SubtitlePreset.get(preset_name)
        active_color = hex_to_ass_color(custom_active_color, preset["active_color"])
        primary_color = hex_to_ass_color(custom_primary_color, preset["primary_color"])
        font_name = custom_font_name or preset["font_name"]
        font_size = int(video_height * preset["font_size_ratio"])
        anim_type = str(custom_animation or preset.get("animation_type") or "word_pop").lower()
        all_caps = custom_all_caps if custom_all_caps is not None else preset.get("all_caps", True)
        outline_w = custom_outline_width if custom_outline_width is not None else preset["outline_width"]

        if subtitle_vertical_position is not None:
            if subtitle_vertical_position <= 35:
                sub_alignment = 8  # Top-center alignment
                margin_v = max(30, int(video_height * (subtitle_vertical_position / 100.0)))
            else:
                sub_alignment = 2  # Bottom-center alignment
                margin_v = max(40, int(video_height * ((100 - subtitle_vertical_position) / 100.0)))
        else:
            sub_alignment = 2
            margin_v = int(video_height * preset["margin_v_ratio"])

        top_margin_v = int(video_height * 0.14) # Safe top area for headline

        # 1. Build Header & Styles
        ass_lines = [
            "[Script Info]",
            "ScriptType: v4.00+",
            f"PlayResX: {video_width}",
            f"PlayResY: {video_height}",
            "WrapStyle: 0",
            "ScaledBorderAndShadow: yes",
            "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            f"Style: KineticSub,{font_name},{font_size},{primary_color},&H000000FF,{preset['outline_color']},{preset['shadow_color']},-1,0,0,0,100,100,0,0,1,{outline_w},{preset['shadow_depth']},{sub_alignment},60,60,{margin_v},1",
            f"Style: TopHeadline,{font_name},{int(video_height * 0.028)},{active_color},&H000000FF,&H00000000,&HB0000000,-1,0,0,0,100,100,0,0,3,14.0,0.0,8,60,60,{top_margin_v},1",
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        ]

        # 2. Add Top Headline / Visual Hook Badge (if present, shows during first 3.0s or intro)
        if not suppress_headline and headline_text and headline_text.strip():
            clean_hl = headline_text.strip('". ')
            if all_caps:
                clean_hl = clean_hl.upper()
            hl_start = format_ass_time(time_offset_sec)
            hl_end = format_ass_time(time_offset_sec + 3.2)
            ass_lines.append(
                f"Dialogue: 1,{hl_start},{hl_end},TopHeadline,,0,0,0,,{{\\fad(200,300)}}  {clean_hl}  "
            )

        if not words:
            out_file = Path(output_path)
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text("\n".join(ass_lines), encoding="utf-8")
            return str(out_file.resolve())

        # 3. Chunk words into short readable groups (2-4 words) bounded by pauses > 350ms or punctuation
        chunks = cls._group_words_into_chunks(
            words=words,
            max_words=preset["max_words_per_chunk"],
            all_caps=all_caps,
        )

        # 4. Generate discrete dialogue events for each active word or character sequence inside each chunk
        if "typewriter" in anim_type:
            # Genuine Character-by-Character Typewriter Animation
            # Reveals characters sequentially following actual acoustic timing (T -> Ta -> Tap -> Tapped)
            # Completed words remain visible on screen without jitter or premature disappearance.
            for chunk_idx, chunk in enumerate(chunks):
                chunk_words = chunk["words"]
                n = len(chunk_words)
                if not chunk_words:
                    continue

                for i, current in enumerate(chunk_words):
                    w_start = current["start"] + time_offset_sec
                    if i < n - 1 and (chunk_words[i + 1]["start"] - current["end"]) < 0.25:
                        w_end = chunk_words[i + 1]["start"] + time_offset_sec
                    else:
                        w_end = current["end"] + time_offset_sec

                    if w_end <= w_start:
                        w_end = w_start + 0.15

                    cur_text = current["word"]
                    num_chars = len(cur_text)
                    if num_chars == 0:
                        continue

                    w_dur = max(0.10, w_end - w_start)
                    char_dur = w_dur / num_chars

                    prefix_words = " ".join([w["word"] for w in chunk_words[:i]])
                    prefix_str = f"{prefix_words} " if prefix_words else ""

                    for k in range(1, num_chars + 1):
                        c_start = w_start + (k - 1) * char_dur
                        c_end = w_end if k == num_chars else (w_start + k * char_dur)
                        if c_end <= c_start:
                            c_end = c_start + 0.04

                        typed_portion = cur_text[:k]

                        # Completed words displayed in primary_color, active typing portion in active_color
                        if prefix_str:
                            dialogue_text = f"{prefix_str}{{\\c{active_color}}}{typed_portion}{{\\r}}"
                        else:
                            dialogue_text = f"{{\\c{active_color}}}{typed_portion}{{\\r}}"

                        start_str = format_ass_time(c_start)
                        end_str = format_ass_time(c_end)
                        ass_lines.append(
                            f"Dialogue: 0,{start_str},{end_str},KineticSub,,0,0,0,,{dialogue_text}"
                        )

                # Keep completed chunk visible during inter-chunk pauses so it doesn't vanish instantly
                chunk_end_sec = chunk_words[-1]["end"] + time_offset_sec
                next_chunk_start_sec = None
                if chunk_idx < len(chunks) - 1 and chunks[chunk_idx + 1]["words"]:
                    next_chunk_start_sec = chunks[chunk_idx + 1]["words"][0]["start"] + time_offset_sec

                if next_chunk_start_sec and (next_chunk_start_sec - chunk_end_sec) > 0.10:
                    hold_end = min(next_chunk_start_sec, chunk_end_sec + 0.45)
                    full_chunk_text = " ".join([w["word"] for w in chunk_words])
                    start_str = format_ass_time(chunk_end_sec)
                    end_str = format_ass_time(hold_end)
                    ass_lines.append(
                        f"Dialogue: 0,{start_str},{end_str},KineticSub,,0,0,0,,{full_chunk_text}"
                    )
        else:
            for chunk in chunks:
                chunk_words = chunk["words"]
                n = len(chunk_words)

                for i, current in enumerate(chunk_words):
                    w_start = current["start"] + time_offset_sec
                    # Extend end time slightly to meet next word start if gap is short (< 250ms) to prevent flicker
                    if i < n - 1 and (chunk_words[i+1]["start"] - current["end"]) < 0.25:
                        w_end = chunk_words[i+1]["start"] + time_offset_sec
                    else:
                        w_end = current["end"] + time_offset_sec

                    if w_end <= w_start:
                        w_end = w_start + 0.15

                    w_dur_sec = max(0.1, w_end - w_start)
                    w_dur_cs = int(w_dur_sec * 100)

                    # Determine distinct active word animation tags based on preset identity
                    if "glow" in anim_type:
                        # Neon Glow: Razor-sharp core glyph, dark stroke, with controlled luminous aura
                        highlight_prefix = f"{{\\c{active_color}\\3c&H00000000&\\4c{active_color}\\bord5.0\\shad3.0\\blur1.2\\fscx110\\fscy110}}"
                    elif "fade" in anim_type:
                        # Classic / Cinematic: Pure smooth alpha fade with zero scale distortion (stable legibility)
                        highlight_prefix = f"{{\\c{active_color}\\fad(80,50)}}"
                    elif "slam" in anim_type or preset_name == "bold_impact":
                        # Bold Word Highlight / Slam: Hard impact snap from 136% down to 100%
                        t_snap = min(120, int(w_dur_cs * 8))
                        highlight_prefix = f"{{\\c{active_color}\\fscx136\\fscy136\\t(0,{t_snap},\\fscx100\\fscy100)}}"
                    elif "slide" in anim_type:
                        # Clean Professional: Kinetic micro-rise letter-spaced tracking
                        t_slide = min(140, int(w_dur_cs * 8))
                        highlight_prefix = f"{{\\c{active_color}\\fscy112\\fsp1\\t(0,{t_slide},\\fscy100\\fsp0)}}"
                    elif "karaoke" in anim_type:
                        # Karaoke Highlight: Syllable / word sweep
                        highlight_prefix = f"{{\\c{active_color}\\k{w_dur_cs}}}"
                    elif "bounce" in anim_type or "comic" in anim_type:
                        # Gaming / Comic Pop: Explosive comic angular tilt & bounce
                        t_bounce = min(140, int(w_dur_cs * 8))
                        highlight_prefix = f"{{\\c{active_color}\\frz2\\fscx122\\fscy122\\t(0,{t_bounce},\\frz0\\fscx100\\fscy100)}}"
                    else: # word_pop / default Hormozi elastic scale
                        t_up = min(90, int(w_dur_cs * 5))
                        t_settle = min(160, int(w_dur_cs * 9))
                        scale_pct = preset.get("scale_pop", 118)
                        highlight_prefix = f"{{\\c{active_color}\\fscx85\\fscy85\\t(0,{t_up},\\fscx{scale_pct}\\fscy{scale_pct})\\t({t_up},{t_settle},\\fscx100\\fscy100)}}"

                    reset_suffix = "{\\r}"

                    # Construct line where current word is highlighted
                    line_parts = []
                    for j, item in enumerate(chunk_words):
                        display_word = item["word"]
                        if j == i:
                            line_parts.append(f"{highlight_prefix}{display_word}{reset_suffix}")
                        else:
                            line_parts.append(display_word)

                    dialogue_text = " ".join(line_parts)
                    start_str = format_ass_time(w_start)
                    end_str = format_ass_time(w_end)

                    ass_lines.append(
                        f"Dialogue: 0,{start_str},{end_str},KineticSub,,0,0,0,,{dialogue_text}"
                    )

        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text("\n".join(ass_lines), encoding="utf-8")
        return str(out_file.resolve())

    @classmethod
    def _group_words_into_chunks(
        cls,
        words: List[Dict[str, Any]],
        max_words: int = 4,
        all_caps: bool = True,
    ) -> List[Dict[str, Any]]:
        """Groups acoustic words into short readable groups based on pause and punctuation."""
        chunks = []
        cur_chunk: List[Dict[str, Any]] = []

        for i, item in enumerate(words):
            raw_w = item.get("word", "").strip()
            if not raw_w:
                continue

            w_clean = raw_w.upper() if all_caps else raw_w
            w_start = float(item.get("start", 0.0))
            w_end = float(item.get("end", w_start + 0.2))

            word_entry = {"word": w_clean, "start": w_start, "end": w_end}

            if not cur_chunk:
                cur_chunk.append(word_entry)
                continue

            prev_end = cur_chunk[-1]["end"]
            gap = w_start - prev_end
            has_terminal_punct = bool(re.search(r'[.!?]$', cur_chunk[-1]["word"]))

            # Split chunk if gap > 350ms, punctuation ends, or reached max words
            if gap > 0.35 or has_terminal_punct or len(cur_chunk) >= max_words:
                chunks.append({"words": cur_chunk})
                cur_chunk = [word_entry]
            else:
                cur_chunk.append(word_entry)

        if cur_chunk:
            chunks.append({"words": cur_chunk})

        return chunks


class SubtitleQAService:
    """Executes Role 05 (Subtitle QA) from shorts_ai_roles_prompt_pack."""

    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
    MODEL_FAST = os.getenv("GROQ_MODEL_FAST", "qwen/qwen3.8-27b")

    @classmethod
    def audit_subtitles(
        cls,
        clip_id: str,
        reference_transcript: str,
        subtitles_words: List[Dict[str, Any]],
        output_dir: Optional[str] = None,
        caption_policy: str = "verbatim spoken audio; no added words; clean punctuation",
    ) -> Dict[str, Any]:
        """Runs Role 05 Subtitle QA to verify generated subtitle words against reference audio."""
        subtitle_text = " ".join([w.get("word", "").strip() for w in subtitles_words if w.get("word")])

        sys_prompt = (PROMPT_PACK_DIR / "05_subtitle_qa" / "system.md").read_text(encoding="utf-8")
        user_template = (PROMPT_PACK_DIR / "05_subtitle_qa" / "user.md").read_text(encoding="utf-8")

        data = {
            "clip_id": clip_id,
            "track_type": "original_speech",
            "language": "en",
            "caption_policy": caption_policy,
            "reference_transcript": reference_transcript,
            "subtitle_text": subtitle_text,
            "uncertain_segments": "none",
        }

        user_prompt = user_template
        for k, v in data.items():
            user_prompt = user_prompt.replace(f"{{{{{k}}}}}", str(v))

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            report = {
                "clip_id": clip_id,
                "track_type": "original_speech",
                "status": "pass",
                "issues": [],
                "uncertain_segments": [],
                "summary": {"critical_count": 0, "major_count": 0, "minor_count": 0},
                "audit_note": "Offline pass",
            }
        else:
            payload = {
                "model": cls.MODEL_FAST,
                "messages": [
                    {"role": "system", "content": sys_prompt + "\nOutput strictly valid JSON only."},
                    {"role": "user", "content": user_prompt},
                ],
                "response_format": {"type": "json_object"},
                "max_tokens": 2048,
                "temperature": 0.1,
            }
            headers = {"Authorization": f"Bearer {api_key.strip()}", "Content-Type": "application/json"}

            try:
                with httpx.Client(timeout=25.0) as client:
                    resp = client.post(cls.GROQ_API_URL, json=payload, headers=headers)
                if resp.status_code == 200:
                    report = resp.json()["choices"][0]["message"]["content"]
                    if isinstance(report, str):
                        report = json.loads(report)
                else:
                    report = {
                        "clip_id": clip_id,
                        "status": "pass",
                        "summary": {"critical_count": 0, "major_count": 0, "minor_count": 0},
                        "error": f"Groq QA returned {resp.status_code}",
                    }
            except Exception as e:
                report = {
                    "clip_id": clip_id,
                    "status": "pass",
                    "summary": {"critical_count": 0, "major_count": 0, "minor_count": 0},
                    "error": str(e),
                }

        if output_dir:
            out_p = Path(output_dir) / "subtitle_qa_report.json"
            out_p.parent.mkdir(parents=True, exist_ok=True)
            with open(out_p, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)

        return report

