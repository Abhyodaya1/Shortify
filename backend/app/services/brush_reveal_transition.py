"""BrushReveal and Intro Transition Generator.
Creates dynamic alpha wipe masks and transition frames using Pillow and OpenCV,
supporting clean-edge ink/brush reveals without external browser runtimes.
"""

from __future__ import annotations
import math
from pathlib import Path
from typing import Tuple, Optional, List
from PIL import Image, ImageDraw, ImageFilter

from backend.app.services.easing import evaluate_easing


class BrushRevealTransition:
    """Generates animated brush and ink wipe alpha masks."""

    @classmethod
    def generate_brush_mask(
        cls,
        progress: float,
        canvas_dimensions: Tuple[int, int] = (1080, 1920),
        angle_deg: float = 45.0,
        edge_softness: int = 40,
    ) -> Image.Image:
        """Generates a grayscale alpha mask (0=transparent, 255=opaque) for progress in [0.0, 1.0]."""
        w, h = canvas_dimensions
        clamped_p = max(0.0, min(1.0, float(progress)))

        if clamped_p <= 0.0:
            return Image.new("L", (w, h), 0)
        if clamped_p >= 1.0:
            return Image.new("L", (w, h), 255)

        # Create oversized canvas for angled wipe
        diag = int(math.hypot(w, h)) + 100
        mask_canvas = Image.new("L", (diag, diag), 0)
        draw = ImageDraw.Draw(mask_canvas)

        # Calculate wipe distance
        wipe_pos = int(diag * clamped_p)
        draw.rectangle([(0, 0), (diag, wipe_pos)], fill=255)

        # Soft edge blur
        if edge_softness > 0:
            mask_canvas = mask_canvas.filter(ImageFilter.GaussianBlur(radius=edge_softness // 2))

        # Rotate by angle and crop to target canvas
        rotated = mask_canvas.rotate(angle_deg, resample=Image.Resampling.BILINEAR)
        offset_x = (diag - w) // 2
        offset_y = (diag - h) // 2
        final_mask = rotated.crop((offset_x, offset_y, offset_x + w, offset_y + h))

        return final_mask

    @classmethod
    def apply_reveal_to_image(
        cls,
        foreground: Image.Image,
        progress: float,
        angle_deg: float = 45.0,
    ) -> Image.Image:
        """Applies brush reveal mask to a foreground RGBA image."""
        if foreground.mode != "RGBA":
            foreground = foreground.convert("RGBA")

        mask = cls.generate_brush_mask(
            progress=progress,
            canvas_dimensions=foreground.size,
            angle_deg=angle_deg,
        )

        r, g, b, orig_a = foreground.split()
        combined_a = Image.new("L", foreground.size)
        # Multiply original alpha with reveal mask
        mask_data = mask.load()
        orig_data = orig_a.load()
        comb_draw = ImageDraw.Draw(combined_a)

        # Faster alpha composite using point operation
        alpha_mask = orig_a.point(lambda p: p / 255.0)
        # Composite mask
        final_alpha = Image.composite(orig_a, Image.new("L", foreground.size, 0), mask)

        output = Image.merge("RGBA", (r, g, b, final_alpha))
        return output

    @classmethod
    def export_reveal_sequence(
        cls,
        foreground: Image.Image,
        duration_sec: float = 1.0,
        fps: int = 30,
        output_dir: Optional[Path] = None,
        prefix: str = "brush_frame",
        easing: str = "ease_out_cubic",
    ) -> List[Path]:
        """Renders sequential transparent PNG frames of the reveal."""
        if output_dir is None:
            output_dir = Path("storage/temp/brush_reveal_seq")
        output_dir.mkdir(parents=True, exist_ok=True)

        total_frames = max(1, int(math.ceil(duration_sec * fps)))
        saved_paths: List[Path] = []

        for i in range(total_frames):
            raw_t = i / float(total_frames - 1) if total_frames > 1 else 1.0
            eased_t = evaluate_easing(easing, raw_t)

            frame = cls.apply_reveal_to_image(foreground, eased_t)
            out_file = output_dir / f"{prefix}_{i:05d}.png"
            frame.save(str(out_file), format="PNG")
            saved_paths.append(out_file)

        return saved_paths
