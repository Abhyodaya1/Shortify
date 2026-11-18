"""Motion Graphics & Animated Callouts Renderer.
Renders broadcast-grade vector-like motion graphics: arrows, highlight circles,
callout boxes, and animated brush strokes.
"""

from __future__ import annotations
import math
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
from PIL import Image, ImageDraw, ImageFont

from backend.app.services.easing import compute_animation_phase, evaluate_easing
from backend.app.services.wordart_renderer import WordArtRenderer
from backend.app.models.visual_config import MotionGraphicElementConfig


class MotionGraphicsRenderer:
    """Renders animated callouts and graphic elements onto transparent RGBA canvases."""

    @classmethod
    def render_arrow(
        cls,
        progress: float,
        color: str = "#00E297",
        stroke_width: int = 6,
        canvas_size: Tuple[int, int] = (240, 240),
        angle_deg: float = 30.0,
    ) -> Image.Image:
        """Renders an animated drawing arrow pointing towards a focal point."""
        w, h = canvas_size
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Draw shaft up to progress
        start_x, start_y = 30, h - 30
        end_x, end_y = w - 40, 40

        cur_x = start_x + (end_x - start_x) * progress
        cur_y = start_y + (end_y - start_y) * progress

        c_rgba = WordArtRenderer._hex_to_rgba(color)

        # Shaft
        if progress > 0.05:
            draw.line([(start_x, start_y), (cur_x, cur_y)], fill=c_rgba, width=stroke_width)

        # Arrowhead (appears in last 30% of progress)
        if progress >= 0.7:
            head_progress = (progress - 0.7) / 0.3
            head_len = 24.0 * head_progress
            angle = math.atan2(end_y - start_y, end_x - start_x)

            # Two wings of arrowhead
            left_angle = angle + math.radians(145)
            right_angle = angle - math.radians(145)

            p1 = (cur_x + head_len * math.cos(left_angle), cur_y + head_len * math.sin(left_angle))
            p2 = (cur_x + head_len * math.cos(right_angle), cur_y + head_len * math.sin(right_angle))

            draw.line([(cur_x, cur_y), p1], fill=c_rgba, width=stroke_width)
            draw.line([(cur_x, cur_y), p2], fill=c_rgba, width=stroke_width)

        return img

    @classmethod
    def render_circle_highlight(
        cls,
        progress: float,
        color: str = "#FFE600",
        stroke_width: int = 5,
        canvas_size: Tuple[int, int] = (260, 260),
    ) -> Image.Image:
        """Renders an animated circular loop drawing around a subject."""
        w, h = canvas_size
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        margin = stroke_width * 2 + 10
        bbox = [margin, margin, w - margin, h - margin]

        c_rgba = WordArtRenderer._hex_to_rgba(color)
        start_angle = -90
        end_angle = start_angle + int(360 * max(0.0, min(1.0, progress)))

        if progress > 0.02:
            draw.arc(bbox, start=start_angle, end=end_angle, fill=c_rgba, width=stroke_width)

        return img

    @classmethod
    def render_callout_box(
        cls,
        title: str,
        subtitle: Optional[str] = None,
        progress: float = 1.0,
        color: str = "#00E297",
        bg_color: str = "#11141A",
        max_width: int = 400,
    ) -> Image.Image:
        """Renders an animated neo-brutalist / glassmorphic callout card."""
        font_title = WordArtRenderer.get_font("Arial Black", 24)
        font_sub = WordArtRenderer.get_font("Arial", 18)

        dummy = Image.new("RGBA", (10, 10))
        d_dummy = ImageDraw.Draw(dummy)

        bbox_t = d_dummy.textbbox((0, 0), title, font=font_title)
        title_w = bbox_t[2] - bbox_t[0]
        title_h = bbox_t[3] - bbox_t[1]

        sub_w, sub_h = 0, 0
        if subtitle:
            bbox_s = d_dummy.textbbox((0, 0), subtitle, font=font_sub)
            sub_w = bbox_s[2] - bbox_s[0]
            sub_h = bbox_s[3] - bbox_s[1]

        content_w = max(title_w, sub_w)
        pad_x, pad_y = 24, 16
        card_w = min(max_width, content_w + pad_x * 2)
        card_h = title_h + (sub_h + 8 if subtitle else 0) + pad_y * 2

        img = Image.new("RGBA", (card_w + 10, card_h + 10), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        c_rgba = WordArtRenderer._hex_to_rgba(color)
        bg_rgba = WordArtRenderer._hex_to_rgba(bg_color, alpha=235)

        # Scale card with progress
        cur_w = max(10, int(card_w * progress))
        cur_h = max(10, int(card_h * progress))

        draw.rounded_rectangle([2, 2, cur_w, cur_h], radius=16, fill=bg_rgba, outline=c_rgba, width=3)

        if progress >= 0.8:
            opacity_ratio = (progress - 0.8) / 0.2
            text_alpha = int(255 * opacity_ratio)
            draw.text((pad_x, pad_y), title, font=font_title, fill=(255, 255, 255, text_alpha))
            if subtitle:
                draw.text((pad_x, pad_y + title_h + 6), subtitle, font=font_sub, fill=(180, 195, 210, text_alpha))

        return img

    @classmethod
    def render_motion_graphic_frame(
        cls,
        config: MotionGraphicElementConfig,
        current_time_sec: float,
        canvas_dimensions: Tuple[int, int] = (1080, 1920),
    ) -> Optional[Image.Image]:
        """Renders one frame of the animated graphic element positioned on a 1080x1920 canvas."""
        phase_info = compute_animation_phase(
            current_time_sec=current_time_sec,
            start_time_sec=config.start_sec,
            duration_sec=config.duration_sec,
            enter_duration_sec=0.35,
            exit_duration_sec=0.3,
            enter_easing="ease_out_back",
            exit_easing="ease_in_cubic",
        )

        if not phase_info["is_visible"]:
            return None

        progress = phase_info["eased_progress"] if phase_info["phase"] == "enter" else 1.0
        g_type = config.graphic_type

        if g_type == "arrow":
            elem_img = cls.render_arrow(progress=progress, color=config.color, stroke_width=config.stroke_width)
        elif g_type == "circle":
            elem_img = cls.render_circle_highlight(progress=progress, color=config.color, stroke_width=config.stroke_width)
        elif g_type == "callout":
            elem_img = cls.render_callout_box(title="KEY INSIGHT", subtitle="High Retention Concept", progress=progress, color=config.color)
        else:
            elem_img = cls.render_arrow(progress=progress, color=config.color, stroke_width=config.stroke_width)

        # Apply exit opacity
        if phase_info["phase"] == "exit" and phase_info["opacity"] < 0.99:
            alpha = elem_img.split()[3].point(lambda p: int(p * phase_info["opacity"]))
            elem_img.putalpha(alpha)

        target_w, target_h = canvas_dimensions
        frame_canvas = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))

        pos_x = int(target_w * (config.x_percent / 100.0) - elem_img.width // 2)
        pos_y = int(target_h * (config.y_percent / 100.0) - elem_img.height // 2)

        frame_canvas.paste(elem_img, (pos_x, pos_y), elem_img)
        return frame_canvas
