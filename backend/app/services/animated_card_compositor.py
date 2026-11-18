"""Animated Social Card Compositor.
Applies entrance, hold, and exit transitions to social cards (Reddit, Twitter,
Instagram, YouTube) with alpha handling and safe boundary positioning.
"""

from __future__ import annotations
import math
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
from PIL import Image

from backend.app.services.easing import compute_animation_phase
from backend.app.services.card_overlay_generator import CardOverlayGenerator


class AnimatedCardCompositor:
    """Composites animated social card overlays for 9:16 vertical video."""

    @classmethod
    def generate_static_card(
        cls,
        card_type: str,
        text: str,
        author: str,
        handle: str,
        badge: str = "2 hours ago",
        card_width: int = 940,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generates static transparent PNG for specified social platform."""
        if output_path is None:
            output_path = Path("storage/temp/social_card_static.png")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if card_type in ["reddit_card", "reddit"]:
            CardOverlayGenerator.generate_reddit_hook_card(
                subreddit=author if "r/" in author else f"r/{author}",
                author_name=handle or "u/peakheistclips",
                question_text=text,
                output_path=str(output_path),
                card_width=card_width,
            )
        elif card_type in ["instagram_card", "instagram"]:
            CardOverlayGenerator.generate_instagram_card(
                author_name=author,
                handle=handle,
                hook_text=text,
                output_path=str(output_path),
                card_width=card_width,
            )
        elif card_type in ["youtube_comment", "youtube_card", "youtube"]:
            CardOverlayGenerator.generate_comment_card(
                author_name=author,
                badge_text=badge or "CA$ 14.99 SUPERCHAT",
                comment_text=text,
                output_path=str(output_path),
                card_width=card_width,
            )
        else: # Twitter / X
            CardOverlayGenerator.generate_tweet_card(
                author_name=author,
                handle=handle,
                tweet_text=text,
                output_path=str(output_path),
                card_width=card_width,
            )

        return output_path

    @classmethod
    def render_animated_card_frame(
        cls,
        card_image: Image.Image,
        current_time_sec: float,
        start_time_sec: float = 0.0,
        duration_sec: float = 3.5,
        y_position_percent: float = 18.0,
        canvas_dimensions: Tuple[int, int] = (1080, 1920),
        animation_style: str = "slam_in",
    ) -> Optional[Image.Image]:
        """Renders single animated social card overlay frame with entrance/exit transitions."""
        phase_info = compute_animation_phase(
            current_time_sec=current_time_sec,
            start_time_sec=start_time_sec,
            duration_sec=duration_sec,
            enter_duration_sec=0.4,
            exit_duration_sec=0.35,
            enter_easing="slam_in" if animation_style == "slam_in" else "ease_out_back",
            exit_easing="ease_in_cubic",
        )

        if not phase_info["is_visible"]:
            return None

        card_copy = card_image.copy()

        # Scale transform
        scale = phase_info["scale"]
        opacity = phase_info["opacity"]
        translate_y = phase_info["translate_y"]

        if abs(scale - 1.0) > 0.01 and scale > 0.05:
            new_w = max(1, int(card_copy.width * scale))
            new_h = max(1, int(card_copy.height * scale))
            card_copy = card_copy.resize((new_w, new_h), Image.Resampling.BILINEAR)

        # Alpha opacity
        if opacity < 0.99:
            alpha = card_copy.split()[3].point(lambda p: int(p * opacity))
            card_copy.putalpha(alpha)

        target_w, target_h = canvas_dimensions
        frame_canvas = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))

        pos_x = (target_w - card_copy.width) // 2
        base_y = int(target_h * (y_position_percent / 100.0))
        pos_y = int(base_y + translate_y)

        frame_canvas.paste(card_copy, (pos_x, pos_y), card_copy)
        return frame_canvas

    @classmethod
    def export_card_sequence(
        cls,
        card_image_path: Path,
        duration_sec: float = 3.5,
        fps: int = 30,
        y_position_percent: float = 18.0,
        output_dir: Optional[Path] = None,
        prefix: str = "card_frame",
        canvas_dimensions: Tuple[int, int] = (1080, 1920),
    ) -> List[Path]:
        """Exports animated transparent PNG sequence of the card."""
        if output_dir is None:
            output_dir = Path("storage/temp/card_sequence")
        output_dir.mkdir(parents=True, exist_ok=True)

        with Image.open(card_image_path) as card_img:
            card_rgba = card_img.convert("RGBA")

            total_frames = int(math.ceil(duration_sec * fps))
            frame_paths: List[Path] = []

            for frame_idx in range(total_frames):
                t = frame_idx / float(fps)
                frame = cls.render_animated_card_frame(
                    card_image=card_rgba,
                    current_time_sec=t,
                    start_time_sec=0.0,
                    duration_sec=duration_sec,
                    y_position_percent=y_position_percent,
                    canvas_dimensions=canvas_dimensions,
                )
                if frame is None:
                    frame = Image.new("RGBA", canvas_dimensions, (0, 0, 0, 0))

                path = output_dir / f"{prefix}_{frame_idx:05d}.png"
                frame.save(str(path), format="PNG")
                frame_paths.append(path)

            return frame_paths
