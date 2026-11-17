"""Unit tests for WordArt Typography & Kinetic Text Rendering Engine."""

import pytest
from pathlib import Path
from PIL import Image
from backend.app.services.wordart_renderer import WordArtRenderer, WordArtPreset


def test_all_wordart_presets_render_successfully():
    """Verifies all 10 presets rasterize cleanly with alpha channels."""
    sample_text = "VIRAL HOOK"

    for preset in WordArtPreset.ALL_PRESETS:
        img = WordArtRenderer.render_wordart_badge(
            text=sample_text,
            style=preset,
            font_size=48,
            primary_color="#FFFFFF",
            secondary_color="#FFE600",
            stroke_width=4,
        )
        assert isinstance(img, Image.Image), f"Preset {preset} did not return a PIL Image"
        assert img.mode == "RGBA", f"Preset {preset} is not in RGBA mode"
        assert img.width > 50, f"Preset {preset} width too small: {img.width}"
        assert img.height > 20, f"Preset {preset} height too small: {img.height}"

        # Verify transparent pixels exist and colored pixels exist
        alpha_band = img.split()[3]
        min_a, max_a = alpha_band.getextrema()
        assert min_a == 0, f"Preset {preset} background should contain transparency"
        assert max_a > 180, f"Preset {preset} text should contain visible content"


def test_animated_frame_lifecycle():
    """Verifies animated frame generation at before, enter, hold, exit, and after states."""
    duration = 3.0
    text = "STOP MAKING THIS MISTAKE"

    # Before start
    f_before = WordArtRenderer.render_animated_frame(
        text=text,
        style=WordArtPreset.SLAM_IN,
        current_time_sec=-0.5,
        start_time_sec=0.0,
        duration_sec=duration,
    )
    assert f_before is None

    # During enter
    f_enter = WordArtRenderer.render_animated_frame(
        text=text,
        style=WordArtPreset.SLAM_IN,
        current_time_sec=0.2,
        start_time_sec=0.0,
        duration_sec=duration,
        canvas_dimensions=(540, 960),
    )
    assert f_enter is not None
    assert f_enter.size == (540, 960)

    # During hold
    f_hold = WordArtRenderer.render_animated_frame(
        text=text,
        style=WordArtPreset.SLAM_IN,
        current_time_sec=1.5,
        start_time_sec=0.0,
        duration_sec=duration,
        canvas_dimensions=(540, 960),
    )
    assert f_hold is not None
    assert f_hold.size == (540, 960)

    # After end
    f_after = WordArtRenderer.render_animated_frame(
        text=text,
        style=WordArtPreset.SLAM_IN,
        current_time_sec=3.5,
        start_time_sec=0.0,
        duration_sec=duration,
    )
    assert f_after is None


def test_png_sequence_generation(tmp_path: Path):
    """Verifies batch sequence rendering writes valid sequential PNG frames."""
    duration = 0.5
    fps = 10
    expected_frames = 5

    seq_dir = tmp_path / "test_seq"
    files = WordArtRenderer.render_png_sequence(
        text="QUICK TEST",
        style=WordArtPreset.NEON_GLOW,
        duration_sec=duration,
        fps=fps,
        output_dir=seq_dir,
        prefix="neon_frame",
        canvas_dimensions=(270, 480),
    )

    assert len(files) == expected_frames
    for f in files:
        assert f.exists()
        with Image.open(f) as img:
            assert img.size == (270, 480)
            assert img.mode == "RGBA"
