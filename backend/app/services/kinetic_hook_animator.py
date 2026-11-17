"""Kinetic Hook, Title & Supporting Caption Animator.
Synthesizes animated viral hooks, typewriter reveals, slam-in typography,
and supporting subtitles within reels/shorts safe bounds.
"""

from __future__ import annotations
import math
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
from PIL import Image, ImageDraw, ImageFont

from backend.app.services.easing import compute_animation_phase, evaluate_easing
from backend.app.services.wordart_renderer import WordArtRenderer, WordArtPreset
from backend.app.models.visual_config import OpeningHookIntroConfig


class KineticHookAnimator:
    """Renders composite animated hooks and supporting subtitles for vertical 9:16 video."""

    @classmethod
    def wrap_text_to_lines(
        cls,
        text: str,
        font: ImageFont.ImageFont,
        max_width: int,
    ) -> List[str]:
        """Wraps text into lines that do not exceed max_width."""
        words = (text or "").strip().split()
        if not words:
            return []

        dummy_img = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
        draw = ImageDraw.Draw(dummy_img)

        lines: List[str] = []
        cur_line: List[str] = []

        for w in words:
            test_line = " ".join(cur_line + [w])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            line_w = bbox[2] - bbox[0]
            if line_w > max_width and cur_line:
                lines.append(" ".join(cur_line))
                cur_line = [w]
            else:
                cur_line.append(w)

        if cur_line:
            lines.append(" ".join(cur_line))

        return lines

    @classmethod
    def render_supporting_caption(
        cls,
        text: str,
        font_size: int = 28,
        text_color: str = "#E2E8F0",
        canvas_width: int = 1080,
    ) -> Image.Image:
        """Renders a modern, subtle supporting sub-caption inside a soft dark badge."""
        t_str = (text or "").strip()
        if not t_str:
            return Image.new("RGBA", (10, 10), (0, 0, 0, 0))

        font = WordArtRenderer.get_font("Arial", font_size)
        dummy_img = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
        draw = ImageDraw.Draw(dummy_img)
        bbox = draw.textbbox((0, 0), t_str, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        pad_x = 20
        pad_y = 8
        badge_w = text_w + pad_x * 2
        badge_h = text_h + pad_y * 2

        img = Image.new("RGBA", (badge_w + 4, badge_h + 4), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)

        # Soft rounded translucent pill backing
        d.rounded_rectangle([0, 0, badge_w, badge_h], radius=14, fill=(10, 12, 16, 200), outline=(255, 255, 255, 30), width=1)
        # Text
        d.text((pad_x - bbox[0], pad_y - bbox[1]), t_str, font=font, fill=(230, 235, 245, 255))
        return img

    @classmethod
    def render_composite_frame(
        cls,
        current_time_sec: float,
        config: OpeningHookIntroConfig,
        canvas_dimensions: Tuple[int, int] = (1080, 1920),
    ) -> Optional[Image.Image]:
        """Renders one frame of the animated hook + supporting caption composition."""
        if not config.enabled or not config.hook_text:
            return None

        phase_info = compute_animation_phase(
            current_time_sec=current_time_sec,
            start_time_sec=0.0,
            duration_sec=config.duration_sec,
            enter_duration_sec=config.enter_duration_sec,
            exit_duration_sec=config.exit_duration_sec,
            enter_easing="slam_in" if config.animation_type == "slam_in" else config.easing,
            exit_easing="ease_in_cubic",
        )

        if not phase_info["is_visible"]:
            return None

        target_w, target_h = canvas_dimensions
        frame_canvas = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))

        # Handle typewriter animation progression
        hook_text = config.hook_text
        if config.animation_type == "typewriter":
            if phase_info["phase"] == "enter":
                # Reveal characters progressively
                reveal_ratio = phase_info["progress"]
                char_count = max(1, int(len(hook_text) * reveal_ratio))
                visible_text = hook_text[:char_count]
                # Blinking cursor while typing
                cursor = "|" if int(current_time_sec * 6) % 2 == 0 else ""
                hook_text = visible_text + cursor
            elif phase_info["phase"] in ["hold", "exit"]:
                hook_text = config.hook_text

        # Render WordArt badge for main hook
        main_badge = WordArtRenderer.render_wordart_badge(
            text=hook_text,
            style=config.wordart_style,
            font_size=config.font_size,
            primary_color=config.secondary_color,
            secondary_color=config.color,
            stroke_width=max(3, int(config.font_size * 0.08)),
        )

        # Scale transform
        scale = phase_info["scale"]
        opacity = phase_info["opacity"]
        translate_y = phase_info["translate_y"]

        if config.animation_type == "slide_up" and phase_info["phase"] == "enter":
            # Extra vertical slide distance
            translate_y = (1.0 - phase_info["eased_progress"]) * 80.0

        elif config.animation_type == "fade_zoom":
            # Gentle cinematic zoom 0.95 -> 1.05
            zoom_progress = min(1.0, current_time_sec / max(0.1, config.duration_sec))
            scale = 0.96 + 0.08 * zoom_progress

        if abs(scale - 1.0) > 0.01 and scale > 0.05:
            new_w = max(1, int(main_badge.width * scale))
            new_h = max(1, int(main_badge.height * scale))
            main_badge = main_badge.resize((new_w, new_h), Image.Resampling.BILINEAR)

        # Apply opacity
        if opacity < 0.99:
            alpha = main_badge.split()[3].point(lambda p: int(p * opacity))
            main_badge.putalpha(alpha)

        # Center X placement within canvas
        pos_x = (target_w - main_badge.width) // 2
        base_y = int(target_h * (config.y_position_percent / 100.0))
        pos_y = int(base_y + translate_y - main_badge.height // 2)

        # Paste main hook
        frame_canvas.paste(main_badge, (pos_x, pos_y), main_badge)

        # Render supporting caption if present
        if config.show_supporting_caption and config.supporting_text:
            sub_badge = cls.render_supporting_caption(
                text=config.supporting_text,
                font_size=config.supporting_font_size,
                canvas_width=target_w,
            )

            # Staggered fade in: supporting caption fades in slightly after hook
            sub_opacity = opacity
            if phase_info["phase"] == "enter":
                sub_progress = max(0.0, (phase_info["progress"] - 0.25) / 0.75)
                sub_opacity = min(1.0, sub_progress * opacity)

            if sub_opacity < 0.99 and sub_opacity > 0.0:
                sub_alpha = sub_badge.split()[3].point(lambda p: int(p * sub_opacity))
                sub_badge.putalpha(sub_alpha)

            if sub_opacity > 0.01:
                sub_pos_x = (target_w - sub_badge.width) // 2
                sub_pos_y = pos_y + main_badge.height + 12
                frame_canvas.paste(sub_badge, (sub_pos_x, sub_pos_y), sub_badge)

        return frame_canvas

    @classmethod
    def export_hook_sequence(
        cls,
        config: OpeningHookIntroConfig,
        output_dir: Optional[Path] = None,
        fps: int = 30,
        canvas_dimensions: Tuple[int, int] = (1080, 1920),
        prefix: str = "hook_frame",
    ) -> List[Path]:
        """Renders complete transparent PNG sequence of the animated hook presentation."""
        if output_dir is None:
            output_dir = Path("storage/temp/kinetic_hook_seq")
        output_dir.mkdir(parents=True, exist_ok=True)

        total_frames = int(math.ceil(config.duration_sec * fps))
        frame_paths: List[Path] = []

        for frame_idx in range(total_frames):
            t = frame_idx / float(fps)
            frame = cls.render_composite_frame(
                current_time_sec=t,
                config=config,
                canvas_dimensions=canvas_dimensions,
            )
            if frame is None:
                frame = Image.new("RGBA", canvas_dimensions, (0, 0, 0, 0))

            path = output_dir / f"{prefix}_{frame_idx:05d}.png"
            frame.save(str(path), format="PNG")
            frame_paths.append(path)

        return frame_paths
