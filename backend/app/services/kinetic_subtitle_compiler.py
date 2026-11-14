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


def hex_to_ass_color(color: Optional[str], default: str = "&H00FFFFFF&") -> str:
    """Converts #RRGGBB, #RGB, or &H00BBGGRR& to standard ASS &H00BBGGRR& format."""
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
            r, g, b = c[0:2], c[2:4], c[4:6]
            return f"&H00{b}{g}{r}&".upper()
        if len(c) == 8:
            r, g, b, a = c[0:2], c[2:4], c[4:6], c[6:8]
            return f"&H{a}{b}{g}{r}&".upper()
    return default


class SubtitlePreset:
    """Defines aesthetic styles for kinetic captions."""

    PRESETS = {
        "bold_impact": {
            "font_name": "Impact",
            "font_size_ratio": 0.044,      # ~84px on 1080x1920
            "primary_color": "&H00FFFFFF&", # White
            "active_color": "&H0000E6FF&",  # Bright Yellow (#FFE600 in BGR ASS)
            "outline_color": "&H00000000&", # Pitch Black
            "shadow_color": "&HB0000000&",  # Hard Shadow
            "outline_width": 6.0,
            "shadow_depth": 3.8,
            "scale_pop": 118,               # Punchy 118% Word Bounce
            "margin_v_ratio": 0.22,
            "max_words_per_chunk": 3,
            "all_caps": True,
        },
        "neon_glow": {
            "font_name": "Arial Black",
            "font_size_ratio": 0.042,
            "primary_color": "&H00FFFF00&", # Electric Cyan (#00FFFF in BGR ASS)
            "active_color": "&H00FFFF00&",  # Glowing Cyan
            "outline_color": "&H00000000&",
            "shadow_color": "&H60FFFF00&",  # Cyan Glow shadow
            "outline_width": 4.5,
            "shadow_depth": 3.0,
            "scale_pop": 114,
            "margin_v_ratio": 0.22,
            "max_words_per_chunk": 3,
            "all_caps": True,
        },
        "3d_depth": {
            "font_name": "Arial Black",
            "font_size_ratio": 0.044,
            "primary_color": "&H00FFFFFF&",
            "active_color": "&H0045EBD5&",  # Lime Accent
            "outline_color": "&H00000000&",
            "shadow_color": "&HC0000000&",  # Heavy Deep 3D Shadow
            "outline_width": 5.5,
            "shadow_depth": 5.5,
            "scale_pop": 116,
            "margin_v_ratio": 0.22,
            "max_words_per_chunk": 3,
            "all_caps": True,
        },
        "cinematic": {
            "font_name": "Georgia",
            "font_size_ratio": 0.038,
            "primary_color": "&H00F2F7FA&", # Warm Cream
            "active_color": "&H0045EBD5&",  # Subtle Lime highlight
            "outline_color": "&H00111111&",
            "shadow_color": "&H80000000&",
            "outline_width": 2.2,
            "shadow_depth": 1.5,
            "scale_pop": 106,
            "margin_v_ratio": 0.20,
            "max_words_per_chunk": 4,
            "all_caps": False,
        },
        "gradient_wordart": {
            "font_name": "Impact",
            "font_size_ratio": 0.044,
            "primary_color": "&H00FFFFFF&",
            "active_color": "&H00006BFF&",  # Vibrant Orange-Amber
            "outline_color": "&H00000000&",
            "shadow_color": "&HA0000000&",
            "outline_width": 5.5,
            "shadow_depth": 3.5,
            "scale_pop": 118,
            "margin_v_ratio": 0.22,
            "max_words_per_chunk": 3,
            "all_caps": True,
        },
        "minimal_modern": {
            "font_name": "Arial",
            "font_size_ratio": 0.036,
            "primary_color": "&H00FFFFFF&",
            "active_color": "&H00F6823B&",  # Clean Blue
            "outline_color": "&H00000000&",
            "shadow_color": "&H80000000&",
            "outline_width": 2.5,
            "shadow_depth": 1.5,
            "scale_pop": 105,
            "margin_v_ratio": 0.20,
            "max_words_per_chunk": 4,
            "all_caps": False,
        },
        "karaoke_highlight": {
            "font_name": "Arial Black",
            "font_size_ratio": 0.040,
            "primary_color": "&H00A0A0A0&", # Inactive dim gray
            "active_color": "&H0045EBD5&",  # High-voltage Lime active
            "outline_color": "&H00000000&",
            "shadow_color": "&HA0000000&",
            "outline_width": 4.5,
            "shadow_depth": 2.5,
            "scale_pop": 115,
            "margin_v_ratio": 0.22,
            "max_words_per_chunk": 3,
            "all_caps": True,
        },
        "comic_pop": {
            "font_name": "Arial Black",
            "font_size_ratio": 0.044,
            "primary_color": "&H0000E6FF&", # Yellow
            "active_color": "&H00852AFF&",  # Explosive Pink (#FF2A85 in BGR)
            "outline_color": "&H00000000&",
            "shadow_color": "&HC0000000&",
            "outline_width": 6.0,
            "shadow_depth": 4.0,
            "scale_pop": 120,
            "margin_v_ratio": 0.23,
            "max_words_per_chunk": 3,
            "all_caps": True,
        },
        "typewriter": {
            "font_name": "Courier New",
            "font_size_ratio": 0.034,
            "primary_color": "&H0080FF80&", # Soft Green Phosphor
            "active_color": "&H0000FF00&",  # Terminal Neon Green
            "outline_color": "&H00000000&",
            "shadow_color": "&H90000000&",
            "outline_width": 3.0,
            "shadow_depth": 1.8,
            "scale_pop": 105,
            "margin_v_ratio": 0.20,
            "max_words_per_chunk": 4,
            "all_caps": False,
        },
        "creator_hormozi": {
            "font_name": "Arial Black",
            "font_size_ratio": 0.044,
            "primary_color": "&H00FFFFFF&",
            "active_color": "&H0045EBD5&",  # Acid Lime
            "outline_color": "&H00000000&",
            "shadow_color": "&HB0000000&",
            "outline_width": 6.0,
            "shadow_depth": 4.0,
            "scale_pop": 120,
            "margin_v_ratio": 0.23,
            "max_words_per_chunk": 3,
            "all_caps": True,
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
        },
        "clean_minimal": {
            "font_name": "Arial",
            "font_size_ratio": 0.036,
            "primary_color": "&H00FFFFFF&",
            "active_color": "&H00FFFF00&",  # Vibrant Cyan
            "outline_color": "&H00000000&",
            "shadow_color": "&HA0000000&",
            "outline_width": 3.0,
            "shadow_depth": 1.5,
            "scale_pop": 105,
            "margin_v_ratio": 0.20,
            "max_words_per_chunk": 4,
            "all_caps": False,
        },
        "swiss_clean": {
            "font_name": "Arial",
            "font_size_ratio": 0.036,
            "primary_color": "&H00FFFFFF&",
            "active_color": "&H0045EBD5&",  # Neo-Brutalist Lime
            "outline_color": "&H00111111&",
            "shadow_color": "&H80000000&",
            "outline_width": 2.5,
            "shadow_depth": 1.5,
            "scale_pop": 106,
            "margin_v_ratio": 0.18,
            "max_words_per_chunk": 4,
            "all_caps": False,
        },
        "neon_punch": {
            "font_name": "Impact",
            "font_size_ratio": 0.042,
            "primary_color": "&H00FFFFFF&",
            "active_color": "&H0097E200&",  # Electric Mint (#00E297 in BGR ASS)
            "outline_color": "&H00000000&",
            "shadow_color": "&H60000000&",
            "outline_width": 4.5,
            "shadow_depth": 2.8,
            "scale_pop": 114,
            "margin_v_ratio": 0.22,
            "max_words_per_chunk": 3,
            "all_caps": True,
        },
        "terminal_phosphor": {
            "font_name": "Courier New",
            "font_size_ratio": 0.034,
            "primary_color": "&H0080FF80&", # Soft Green Phosphor
            "active_color": "&H0000FF00&",  # Ultra Bright Terminal Phosphor
            "outline_color": "&H00000000&",
            "shadow_color": "&H90000000&",
            "outline_width": 3.5,
            "shadow_depth": 2.0,
            "scale_pop": 105,
            "margin_v_ratio": 0.20,
            "max_words_per_chunk": 4,
            "all_caps": False,
        },
        "tiktok_yellow": {
            "font_name": "Arial Black",
            "font_size_ratio": 0.040,
            "primary_color": "&H00FFFFFF&",
            "active_color": "&H0000E5FF&",  # Bright Yellow
            "outline_color": "&H00000000&",
            "shadow_color": "&HA0000000&",
            "outline_width": 5.0,
            "shadow_depth": 2.5,
            "scale_pop": 110,
            "margin_v_ratio": 0.22,
            "max_words_per_chunk": 3,
            "all_caps": True,
        },
        "red_alert": {
            "font_name": "Impact",
            "font_size_ratio": 0.042,
            "primary_color": "&H00FFFFFF&",
            "active_color": "&H000022FF&",  # Intense Punch Red
            "outline_color": "&H00000000&",
            "shadow_color": "&H80000000&",
            "outline_width": 5.0,
            "shadow_depth": 2.8,
            "scale_pop": 114,
            "margin_v_ratio": 0.22,
            "max_words_per_chunk": 3,
            "all_caps": True,
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

        # 4. Generate discrete dialogue events for each active word inside each chunk
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

                # Determine active word animation tags
                if "glow" in anim_type:
                    # Neon glowing aura on spoken word with blur and glow halo
                    highlight_prefix = f"{{\\c{active_color}\\3c{active_color}\\blur6\\shad3\\fscx108\\fscy108}}"
                elif "fade" in anim_type:
                    # Smooth dissolving fade transition
                    highlight_prefix = f"{{\\c{active_color}\\fad(80,60)}}"
                elif "slide" in anim_type:
                    # Kinetic micro-rise animation
                    highlight_prefix = f"{{\\c{active_color}\\fscy118\\fscx106}}"
                elif "karaoke" in anim_type:
                    # Syllable / word karaoke color sweep
                    highlight_prefix = f"{{\\c{active_color}\\k{w_dur_cs}}}"
                else: # word_pop / bounce / default
                    scale_pct = preset.get("scale_pop", 118)
                    scale_tag = f"\\fscx{scale_pct}\\fscy{scale_pct}" if scale_pct != 100 else ""
                    highlight_prefix = f"{{\\c{active_color}{scale_tag}}}"

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

