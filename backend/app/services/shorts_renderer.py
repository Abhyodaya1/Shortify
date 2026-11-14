"""Shorts Video Rendering Engine: Produces 9:16 vertical MP4s with speaker tracking,
cinematic kinetic subtitles, and editorial hook badges via local FFmpeg."""

from __future__ import annotations
import os
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from ..models.editorial_profile import EditorialProfile
from ..storage.profile_store import ProfileStore

STORAGE_RENDERS = Path("backend/storage/renders")
STORAGE_RENDERS.mkdir(parents=True, exist_ok=True)


class ShortsRenderer:
    """Renders 9:16 vertical YouTube Shorts MP4 with speaker crop, kinetic typography, and hook badges."""

    @classmethod
    def render_short_mp4(
        cls,
        source_video_path: str,
        start_sec: float,
        end_sec: float,
        crop_data: Dict[str, Any],
        hook_text: str,
        subtitles: List[Dict[str, Any]],
        output_filename: str,
        profile: Optional[EditorialProfile] = None,
        target_width: int = 1080,
        target_height: int = 1920,
    ) -> str:
        """Executes FFmpeg pipeline to generate a broadcast-quality 9:16 MP4 video."""
        active_profile = profile or ProfileStore.get_active_profile()
        output_path = STORAGE_RENDERS / output_filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        duration = max(1.0, end_sec - start_sec)
        crop_w = crop_data.get("crop_width", int(crop_data.get("source_height", 1080) * 9 / 16))
        crop_h = crop_data.get("crop_height", crop_data.get("source_height", 1080))
        src_w = crop_data.get("source_width", 1920)

        # 1. Compute dynamic or stable crop X expression
        crop_x_expr = cls._build_crop_expression(crop_data, duration, src_w, crop_w, active_profile)

        # 2. Generate Cinematic Kinetic ASS subtitle file
        ass_path = STORAGE_RENDERS / f"{Path(output_filename).stem}.ass"
        cls._create_kinetic_ass(ass_path, subtitles, hook_text, target_width, target_height, active_profile)

        # 3. Build FFmpeg video filter chain
        # A: Dynamic or centered 9:16 crop
        # B: Scale to target resolution (1080x1920)
        # C: Pad if aspect ratio slightly differs
        # D: Render styled kinetic subtitles & hook badge via libass
        escaped_ass = str(ass_path.resolve()).replace("\\", "/").replace(":", "\\:")
        
        vf_filters = [
            f"crop={crop_w}:{crop_h}:{crop_x_expr}:0",
            f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease",
            f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:black",
            f"subtitles='{escaped_ass}'",
        ]
        vf_chain = ",".join(vf_filters)

        # Determine best video encoder (NVENC GPU hardware acceleration with CPU fallback)
        encoder = cls._detect_encoder()

        cmd = [
            "ffmpeg",
            "-y",
            "-ss", f"{start_sec:.3f}",
            "-i", str(Path(source_video_path).resolve()),
            "-t", f"{duration:.3f}",
            "-vf", vf_chain,
            "-c:v", encoder,
            "-preset", "fast",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "48000",
            "-movflags", "+faststart",
            str(output_path.resolve()),
        ]

        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=180)
            if res.returncode != 0:
                print(f"Primary render with {encoder} failed ({res.stderr[-300:]}), falling back to libx264...")
                cls._render_fallback(
                    source_video_path, start_sec, duration, crop_w, crop_h,
                    crop_data.get("optimal_crop_x", 0), ass_path, output_path, target_width, target_height
                )
        except subprocess.TimeoutExpired:
            print("Primary render timed out after 180s, falling back to libx264...")
            cls._render_fallback(
                source_video_path, start_sec, duration, crop_w, crop_h,
                crop_data.get("optimal_crop_x", 0), ass_path, output_path, target_width, target_height
            )
        except Exception as e:
            print(f"Exception during render: {e}, falling back to CPU...")
            cls._render_fallback(
                source_video_path, start_sec, duration, crop_w, crop_h,
                crop_data.get("optimal_crop_x", 0), ass_path, output_path, target_width, target_height
            )

        # Clean temporary ASS file
        if ass_path.exists():
            try:
                ass_path.unlink()
            except Exception:
                pass

        return str(output_path.resolve())

    @classmethod
    def _build_crop_expression(
        cls, crop_data: Dict[str, Any], duration: float, src_w: int, crop_w: int, profile: EditorialProfile
    ) -> str:
        """Constructs a smooth dynamic pan expression or hysteresis-damped static crop."""
        max_x = max(0, src_w - crop_w)
        keyframes = crop_data.get("keyframes", [])
        is_locked = crop_data.get("face_locked", False)
        default_x = crop_data.get("optimal_crop_x", max_x // 2)

        if not profile.enable_camera_pan_smoothing or not is_locked or len(keyframes) < 4:
            return str(int(default_x))

        # Sample trajectory anchors every ~3 seconds to avoid overly complex filter expressions
        anchors = []
        step = max(1, len(keyframes) // 8)
        for i in range(0, len(keyframes), step):
            anchors.append(keyframes[i])
        if keyframes and keyframes[-1] not in anchors:
            anchors.append(keyframes[-1])

        # Check total motion variance
        x_vals = [a["crop_x"] for a in anchors]
        if max(x_vals) - min(x_vals) < 25:
            # Motion under 25px: use stable static crop to prevent camera jitter (hysteresis rule)
            return str(int(default_x))

        # Build smooth linear interpolation expression across anchors:
        # if(lte(t, t1), lerp(x0, x1), if(lte(t, t2), lerp(x1, x2), ...))
        t_base = keyframes[0]["timestamp_sec"]
        expr = str(int(x_vals[-1]))
        for i in range(len(anchors) - 2, -1, -1):
            t1 = anchors[i]["timestamp_sec"] - t_base
            t2 = anchors[i + 1]["timestamp_sec"] - t_base
            x1 = anchors[i]["crop_x"]
            x2 = anchors[i + 1]["crop_x"]
            dt = max(0.1, t2 - t1)
            lerp = f"({x1}+({x2}-{x1})*(t-{t1:.2f})/{dt:.2f})"
            expr = f"if(lte(t,{t2:.2f}),{lerp},{expr})"

        raw_expr = f"clip({expr},0,{max_x})"
        # Escape commas so FFmpeg filter graph does not split the expression into separate filters
        return raw_expr.replace(",", r"\,")

    @classmethod
    def _create_kinetic_ass(
        cls,
        ass_path: Path,
        subtitles: List[Dict[str, Any]],
        hook_text: str,
        width: int,
        height: int,
        profile: EditorialProfile,
    ) -> None:
        """Generates modern ASS subtitles with word-by-word kinetic highlighting and safe margins."""
        margin_v = int(height * profile.subtitle_safe_margin_v_ratio)
        font_size = int(height * 0.038)  # ~72px for 1920h
        accent = profile.accent_color_bgr  # Gold &H0000D7FF&
        primary = profile.primary_color_bgr  # White &H00FFFFFF&

        header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: KineticSub,Arial,{font_size},{primary},&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4.0,2.0,2,60,60,{margin_v},1
Style: HookBadge,Arial,{int(height * 0.026)},{accent},&H000000FF,&H00000000,&HB0000000,-1,0,0,0,100,100,0,0,3,14.0,0.0,8,60,60,{int(height * 0.82)},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        events = []

        # 1. Opening Editorial Hook Badge (first 2.4s, placed in upper safe area)
        if profile.allow_editorial_hook_overlay and hook_text.strip():
            clean_hook = hook_text.strip('".')
            # Limit words according to profile
            hook_words = clean_hook.split()[:profile.max_hook_words]
            display_hook = " ".join(hook_words).upper()
            hook_line = f"Dialogue: 1,0:00:00.00,0:00:02.40,HookBadge,,0,0,0,,{{\\fad(180,250)}}  {display_hook}  "
            events.append(hook_line)

        # 2. Spoken Dialogue with word-by-word kinetic animation
        # Break cues into smaller 3-5 word readable chunks and generate micro-timing beats
        for cue in subtitles:
            cue_start = max(0.0, cue.get("start_rel_sec", 0.0))
            cue_end = max(cue_start + 0.3, cue.get("end_rel_sec", cue_start + 1.0))
            raw_text = cue.get("text", "").strip()
            if not raw_text:
                continue

            words = raw_text.split()
            if not words:
                continue

            # Synthesize micro-timing for words across cue duration based on character length
            total_chars = max(1, sum(len(w) for w in words))
            cue_dur = cue_end - cue_start
            word_spans = []
            cur_t = cue_start

            for w in words:
                w_dur = max(0.12, (len(w) / total_chars) * cue_dur)
                word_spans.append({
                    "word": w,
                    "start": cur_t,
                    "end": min(cue_end, cur_t + w_dur),
                })
                cur_t += w_dur

            # Group into lines of at most 5 words (max_subtitle_lines compliant)
            chunk_size = 5
            for chunk_idx in range(0, len(word_spans), chunk_size):
                chunk = word_spans[chunk_idx:chunk_idx + chunk_size]
                chunk_words = [item["word"] for item in chunk]

                # Emit kinetic highlighting dialogue for each active word in this chunk
                for active_i, active_item in enumerate(chunk):
                    w_start_fmt = cls._format_ass_time(active_item["start"])
                    w_end_fmt = cls._format_ass_time(active_item["end"])

                    line_parts = []
                    for i, w in enumerate(chunk_words):
                        if i == active_i:
                            # Highlighted active word with 6% scale pop
                            line_parts.append(f"{{\\c{accent}\\fscx106\\fscy106}}{w}{{\\r\\c{primary}}}")
                        elif i < active_i:
                            # Already spoken: stable white
                            line_parts.append(f"{{\\c{primary}}}{w}")
                        else:
                            # Upcoming words in chunk: readable white
                            line_parts.append(f"{{\\c{primary}}}{w}")

                    formatted_line = " ".join(line_parts)
                    events.append(f"Dialogue: 0,{w_start_fmt},{w_end_fmt},KineticSub,,0,0,0,,{formatted_line}")

        with open(ass_path, "w", encoding="utf-8") as f:
            f.write(header + "\n".join(events))

    @staticmethod
    def _format_ass_time(sec: float) -> str:
        sec = max(0.0, sec)
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = int(sec % 60)
        cs = int(round((sec - int(sec)) * 100))
        if cs >= 100:
            cs = 99
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    @classmethod
    def _detect_encoder(cls) -> str:
        try:
            res = subprocess.run(["ffmpeg", "-encoders"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
            if "h264_nvenc" in res.stdout:
                return "h264_nvenc"
        except Exception:
            pass
        return "libx264"

    @classmethod
    def _render_fallback(
        cls, src: str, start: float, dur: float, cw: int, ch: int, cx: int, ass_file: Path, out: Path, tw: int, th: int
    ):
        """Standard CPU fallback pipeline if NVENC encounters driver or hardware constraints."""
        escaped_ass = str(ass_file.resolve()).replace("\\", "/").replace(":", "\\:")
        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{start:.3f}",
            "-i", str(Path(src).resolve()),
            "-t", f"{dur:.3f}",
            "-vf", f"crop={cw}:{ch}:{cx}:0,scale={tw}:{th},subtitles='{escaped_ass}'",
            "-c:v", "libx264",
            "-preset", "fast",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            str(out.resolve()),
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=180)
        except subprocess.TimeoutExpired:
            raise RuntimeError("Fallback CPU render timed out after 180 seconds.")
