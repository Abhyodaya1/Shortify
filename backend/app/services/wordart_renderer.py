"""WordArt Typography & Kinetic Text Rendering Engine.
Generates broadcast-grade typography treatments, multi-layer glow, 3D extrusions,
gradient fills, and animated transparent PNG sequences.
"""

from __future__ import annotations
import math
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from backend.app.services.easing import compute_animation_phase, evaluate_easing


class WordArtPreset:
    """Supported WordArt Typography Presets."""
    SLAM_IN = "slam_in"
    NEON_GLOW = "neon_glow"
    GRADIENT_FIRE = "gradient_fire"
    COMIC_POP = "comic_pop"
    CYBER_TERMINAL = "cyber_terminal"
    METALLIC_CHROME = "metallic_chrome"
    SOFT_PILL = "soft_pill"
    DUOTONE_SPLIT = "duotone_split"
    EXTRUDE_3D = "3d_extrude"
    GOLDEN_LUXURY = "golden_luxury"

    ALL_PRESETS = [
        SLAM_IN,
        NEON_GLOW,
        GRADIENT_FIRE,
        COMIC_POP,
        CYBER_TERMINAL,
        METALLIC_CHROME,
        SOFT_PILL,
        DUOTONE_SPLIT,
        EXTRUDE_3D,
        GOLDEN_LUXURY,
    ]


class WordArtRenderer:
    """Renderer for WordArt text overlays and PNG sequences."""

    _FONT_CACHE: Dict[Tuple[str, int], ImageFont.FreeTypeFont] = {}

    @classmethod
    def get_font(cls, font_family: str = "Arial Black", size: int = 54) -> ImageFont.ImageFont:
        cache_key = (font_family.lower(), size)
        if cache_key in cls._FONT_CACHE:
            return cls._FONT_CACHE[cache_key]

        font_candidates = [
            font_family,
            f"C:/Windows/Fonts/{font_family}.ttf",
            f"C:/Windows/Fonts/{font_family}.otf",
            "C:/Windows/Fonts/ariblk.ttf",
            "C:/Windows/Fonts/impact.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]

        if "impact" in font_family.lower():
            font_candidates.insert(0, "C:/Windows/Fonts/impact.ttf")
        elif "black" in font_family.lower() or "arial" in font_family.lower():
            font_candidates.insert(0, "C:/Windows/Fonts/ariblk.ttf")

        for cand in font_candidates:
            try:
                loaded = ImageFont.truetype(cand, size)
                cls._FONT_CACHE[cache_key] = loaded
                return loaded
            except Exception:
                continue

        fallback = ImageFont.load_default()
        return fallback

    @staticmethod
    def _hex_to_rgba(hex_color: str, alpha: int = 255) -> Tuple[int, int, int, int]:
        c = hex_color.strip().lstrip("#")
        if len(c) == 3:
            c = "".join([x * 2 for x in c])
        if len(c) >= 6:
            r = int(c[0:2], 16)
            g = int(c[2:4], 16)
            b = int(c[4:6], 16)
            a = int(c[6:8], 16) if len(c) == 8 else alpha
            return (r, g, b, a)
        return (255, 255, 255, alpha)

    @classmethod
    def render_wordart_badge(
        cls,
        text: str,
        style: str = WordArtPreset.SLAM_IN,
        font_size: int = 64,
        primary_color: str = "#FFFFFF",
        secondary_color: str = "#FFE600",
        stroke_color: str = "#000000",
        stroke_width: int = 6,
        padding: int = 40,
    ) -> Image.Image:
        """Renders static WordArt styled text onto an auto-sized transparent RGBA canvas."""
        text_str = (text or "").strip()
        if not text_str:
            return Image.new("RGBA", (100, 50), (0, 0, 0, 0))

        font = cls.get_font(
            "Impact" if style in [WordArtPreset.SLAM_IN, WordArtPreset.COMIC_POP] else "Arial Black",
            font_size,
        )

        dummy_img = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
        dummy_draw = ImageDraw.Draw(dummy_img)
        bbox = dummy_draw.textbbox((0, 0), text_str, font=font, stroke_width=stroke_width)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        # Canvas sizing with safety padding for glows and 3D extrusion
        extra_margin = padding * 2 + stroke_width * 4 + 40
        canvas_w = int(text_w + extra_margin)
        canvas_h = int(text_h + extra_margin)

        base_x = (canvas_w - text_w) // 2 - bbox[0]
        base_y = (canvas_h - text_h) // 2 - bbox[1]

        final_img = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))

        primary_rgba = cls._hex_to_rgba(primary_color)
        secondary_rgba = cls._hex_to_rgba(secondary_color)
        stroke_rgba = cls._hex_to_rgba(stroke_color)

        # Style 1: NEON GLOW (Multi-pass blurred glow aura)
        if style == WordArtPreset.NEON_GLOW:
            glow_img = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
            glow_draw = ImageDraw.Draw(glow_img)
            # Outer diffuse glow
            glow_draw.text((base_x, base_y), text_str, font=font, fill=secondary_rgba, stroke_width=stroke_width + 12, stroke_fill=secondary_rgba)
            glow_blurred = glow_img.filter(ImageFilter.GaussianBlur(radius=14))
            final_img = Image.alpha_composite(final_img, glow_blurred)

            # Mid glow
            mid_glow = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
            mid_draw = ImageDraw.Draw(mid_glow)
            mid_draw.text((base_x, base_y), text_str, font=font, fill=secondary_rgba, stroke_width=stroke_width + 4, stroke_fill=secondary_rgba)
            mid_blurred = mid_glow.filter(ImageFilter.GaussianBlur(radius=6))
            final_img = Image.alpha_composite(final_img, mid_blurred)

            # Core bright sharp text
            core_draw = ImageDraw.Draw(final_img)
            core_draw.text((base_x, base_y), text_str, font=font, fill=(255, 255, 255, 255), stroke_width=stroke_width, stroke_fill=(10, 10, 10, 255))

        # Style 2: SLAM IN / BOLD IMPACT (Heavy drop shadow + razor outline)
        elif style == WordArtPreset.SLAM_IN:
            draw = ImageDraw.Draw(final_img)
            # Deep hard shadow
            shadow_offset = max(4, int(stroke_width * 1.5))
            draw.text(
                (base_x + shadow_offset, base_y + shadow_offset),
                text_str,
                font=font,
                fill=(0, 0, 0, 220),
                stroke_width=stroke_width + 2,
                stroke_fill=(0, 0, 0, 220),
            )
            # Main bold text
            draw.text(
                (base_x, base_y),
                text_str,
                font=font,
                fill=secondary_rgba,
                stroke_width=stroke_width,
                stroke_fill=stroke_rgba,
            )

        # Style 3: 3D EXTRUDE (Stepped isometric shadow)
        elif style == WordArtPreset.EXTRUDE_3D:
            draw = ImageDraw.Draw(final_img)
            extrude_steps = max(6, int(stroke_width * 2))
            for i in range(extrude_steps, 0, -1):
                shade_val = max(10, int(40 - i * 3))
                draw.text(
                    (base_x + i, base_y + i),
                    text_str,
                    font=font,
                    fill=(shade_val, shade_val, shade_val, 255),
                    stroke_width=stroke_width,
                    stroke_fill=(0, 0, 0, 255),
                )
            # Top surface
            draw.text(
                (base_x, base_y),
                text_str,
                font=font,
                fill=secondary_rgba,
                stroke_width=stroke_width,
                stroke_fill=stroke_rgba,
            )

        # Style 4: COMIC POP (Bold offset shadow + pop yellow/white)
        elif style == WordArtPreset.COMIC_POP:
            draw = ImageDraw.Draw(final_img)
            # Hard black comic block shadow
            draw.text((base_x + 8, base_y + 8), text_str, font=font, fill=(0, 0, 0, 255), stroke_width=stroke_width + 4, stroke_fill=(0, 0, 0, 255))
            # Foreground pop
            draw.text((base_x, base_y), text_str, font=font, fill=secondary_rgba, stroke_width=stroke_width, stroke_fill=(0, 0, 0, 255))

        # Style 5: SOFT PILL (Keyword pill badge container)
        elif style == WordArtPreset.SOFT_PILL:
            draw = ImageDraw.Draw(final_img)
            pill_pad_x = 24
            pill_pad_y = 12
            pill_box = [
                base_x - pill_pad_x,
                base_y - pill_pad_y,
                base_x + text_w + pill_pad_x,
                base_y + text_h + pill_pad_y,
            ]
            # Soft shadow under pill
            draw.rounded_rectangle([pill_box[0] + 4, pill_box[1] + 4, pill_box[2] + 4, pill_box[3] + 4], radius=24, fill=(0, 0, 0, 140))
            # Pill body
            draw.rounded_rectangle(pill_box, radius=24, fill=(18, 22, 28, 240), outline=secondary_rgba, width=3)
            # Inside text
            draw.text((base_x, base_y), text_str, font=font, fill=primary_rgba, stroke_width=1, stroke_fill=(0, 0, 0, 180))

        # Style 6: CYBER TERMINAL (Phosphor green / cyan monospace style)
        elif style == WordArtPreset.CYBER_TERMINAL:
            draw = ImageDraw.Draw(final_img)
            terminal_color = (0, 255, 128, 255)
            # Subtle green glow
            glow = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
            g_draw = ImageDraw.Draw(glow)
            g_draw.text((base_x, base_y), text_str, font=font, fill=terminal_color, stroke_width=stroke_width + 6, stroke_fill=terminal_color)
            glow_blurred = glow.filter(ImageFilter.GaussianBlur(radius=8))
            final_img = Image.alpha_composite(final_img, glow_blurred)
            # Core terminal
            d = ImageDraw.Draw(final_img)
            d.text((base_x, base_y), text_str, font=font, fill=(220, 255, 230, 255), stroke_width=stroke_width, stroke_fill=(0, 40, 20, 255))

        # Style 7, 8, 9, 10: GRADIENTS (Fire, Chrome, Golden, Duotone)
        elif style in [WordArtPreset.GRADIENT_FIRE, WordArtPreset.METALLIC_CHROME, WordArtPreset.GOLDEN_LUXURY, WordArtPreset.DUOTONE_SPLIT]:
            # Generate gradient texture
            grad_img = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
            grad_draw = ImageDraw.Draw(grad_img)

            if style == WordArtPreset.GRADIENT_FIRE:
                c_top = (255, 60, 0, 255)      # Intense Crimson Red
                c_bot = (255, 230, 0, 255)     # Blazing Yellow
            elif style == WordArtPreset.METALLIC_CHROME:
                c_top = (240, 245, 255, 255)   # Specular Chrome White
                c_bot = (110, 130, 155, 255)   # Slate Steel
            elif style == WordArtPreset.GOLDEN_LUXURY:
                c_top = (255, 225, 120, 255)   # Light Gold
                c_bot = (180, 120, 20, 255)    # Deep Bronze Gold
            else: # DUOTONE_SPLIT
                c_top = primary_rgba
                c_bot = secondary_rgba

            # Render vertical gradient
            for y_step in range(base_y, min(canvas_h, base_y + text_h + 10)):
                ratio = max(0.0, min(1.0, (y_step - base_y) / max(1.0, float(text_h))))
                r = int(c_top[0] * (1.0 - ratio) + c_bot[0] * ratio)
                g = int(c_top[1] * (1.0 - ratio) + c_bot[1] * ratio)
                b = int(c_top[2] * (1.0 - ratio) + c_bot[2] * ratio)
                grad_draw.line([(base_x - 10, y_step), (base_x + text_w + 10, y_step)], fill=(r, g, b, 255), width=1)

            # Create text mask
            mask_img = Image.new("L", (canvas_w, canvas_h), 0)
            mask_draw = ImageDraw.Draw(mask_img)
            mask_draw.text((base_x, base_y), text_str, font=font, fill=255)

            # Create stroke behind
            stroke_img = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
            s_draw = ImageDraw.Draw(stroke_img)
            s_draw.text((base_x, base_y), text_str, font=font, fill=stroke_rgba, stroke_width=stroke_width, stroke_fill=stroke_rgba)

            # Composite: Stroke first, then gradient text masked on top
            final_img = Image.alpha_composite(final_img, stroke_img)
            final_img.paste(grad_img, (0, 0), mask_img)

        else:
            # Standard high contrast fallback
            draw = ImageDraw.Draw(final_img)
            draw.text((base_x, base_y), text_str, font=font, fill=primary_rgba, stroke_width=stroke_width, stroke_fill=stroke_rgba)

        return final_img

    @classmethod
    def render_animated_frame(
        cls,
        text: str,
        style: str,
        current_time_sec: float,
        start_time_sec: float = 0.0,
        duration_sec: float = 3.0,
        font_size: int = 64,
        primary_color: str = "#FFFFFF",
        secondary_color: str = "#FFE600",
        stroke_color: str = "#000000",
        stroke_width: int = 6,
        canvas_dimensions: Tuple[int, int] = (1080, 1920),
        y_position_percent: float = 22.0,
    ) -> Optional[Image.Image]:
        """Renders an animated WordArt overlay frame for a 1080x1920 canvas at timestamp t."""
        phase_info = compute_animation_phase(
            current_time_sec=current_time_sec,
            start_time_sec=start_time_sec,
            duration_sec=duration_sec,
            enter_duration_sec=0.35,
            exit_duration_sec=0.3,
            enter_easing="slam_in" if style == WordArtPreset.SLAM_IN else "ease_out_back",
            exit_easing="ease_in_cubic",
        )

        if not phase_info["is_visible"]:
            return None

        # Render crisp master badge
        badge = cls.render_wordart_badge(
            text=text,
            style=style,
            font_size=font_size,
            primary_color=primary_color,
            secondary_color=secondary_color,
            stroke_color=stroke_color,
            stroke_width=stroke_width,
        )

        scale = phase_info["scale"]
        opacity = phase_info["opacity"]
        translate_y = phase_info["translate_y"]

        # Apply scale transform
        if abs(scale - 1.0) > 0.01 and scale > 0.05:
            new_w = max(1, int(badge.width * scale))
            new_h = max(1, int(badge.height * scale))
            badge = badge.resize((new_w, new_h), Image.Resampling.BILINEAR)

        # Apply alpha opacity
        if opacity < 0.99:
            alpha_layer = badge.split()[3]
            alpha_layer = alpha_layer.point(lambda p: int(p * opacity))
            badge.putalpha(alpha_layer)

        # Place onto 1080x1920 transparent frame
        target_w, target_h = canvas_dimensions
        frame_canvas = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))

        pos_x = (target_w - badge.width) // 2
        base_pos_y = int(target_h * (y_position_percent / 100.0))
        pos_y = int(base_pos_y + translate_y - badge.height // 2)

        frame_canvas.paste(badge, (pos_x, pos_y), badge)
        return frame_canvas

    @classmethod
    def render_png_sequence(
        cls,
        text: str,
        style: str,
        duration_sec: float,
        fps: int = 30,
        output_dir: Optional[Path] = None,
        prefix: str = "frame",
        canvas_dimensions: Tuple[int, int] = (1080, 1920),
        y_position_percent: float = 22.0,
    ) -> List[Path]:
        """Renders an animated WordArt transparent PNG sequence into a directory for FFmpeg."""
        if output_dir is None:
            output_dir = Path("storage/temp/wordart_sequence")
        output_dir.mkdir(parents=True, exist_ok=True)

        total_frames = int(math.ceil(duration_sec * fps))
        saved_files: List[Path] = []

        for frame_idx in range(total_frames):
            t = frame_idx / float(fps)
            frame = cls.render_animated_frame(
                text=text,
                style=style,
                current_time_sec=t,
                start_time_sec=0.0,
                duration_sec=duration_sec,
                canvas_dimensions=canvas_dimensions,
                y_position_percent=y_position_percent,
            )
            if frame is None:
                # Transparent empty frame
                frame = Image.new("RGBA", canvas_dimensions, (0, 0, 0, 0))

            file_path = output_dir / f"{prefix}_{frame_idx:05d}.png"
            frame.save(str(file_path), format="PNG")
            saved_files.append(file_path)

        return saved_files
