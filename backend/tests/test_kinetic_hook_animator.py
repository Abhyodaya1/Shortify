"""Unit tests for Kinetic Hook & Supporting Caption Animator."""

import pytest
from pathlib import Path
from PIL import Image
from backend.app.services.kinetic_hook_animator import KineticHookAnimator
from backend.app.models.visual_config import OpeningHookIntroConfig
from backend.app.services.wordart_renderer import WordArtRenderer


def test_wrap_text_to_lines():
    font = WordArtRenderer.get_font("Arial", 40)
    text = "The secret habit that separates top creators from everyone else in the industry"
    lines = KineticHookAnimator.wrap_text_to_lines(text, font, max_width=400)
    assert len(lines) >= 2
    assert " ".join(lines) == text


def test_supporting_caption_rendering():
    cap = KineticHookAnimator.render_supporting_caption("Watch until the end", font_size=24)
    assert isinstance(cap, Image.Image)
    assert cap.mode == "RGBA"
    assert cap.width > 50
    assert cap.height > 15


def test_typewriter_and_lifecycle_frames():
    config = OpeningHookIntroConfig(
        enabled=True,
        hook_text="STOP MAKING THIS CRITICAL MISTAKE",
        supporting_text="3-minute breakdown",
        show_supporting_caption=True,
        animation_type="typewriter",
        wordart_style="neon_glow",
        duration_sec=3.0,
        enter_duration_sec=0.5,
        exit_duration_sec=0.4,
    )

    # Before start
    f_before = KineticHookAnimator.render_composite_frame(-0.1, config, (540, 960))
    assert f_before is None

    # Early enter (typewriter in progress)
    f_early = KineticHookAnimator.render_composite_frame(0.2, config, (540, 960))
    assert f_early is not None
    assert f_early.size == (540, 960)

    # Hold phase
    f_hold = KineticHookAnimator.render_composite_frame(1.5, config, (540, 960))
    assert f_hold is not None

    # After end
    f_after = KineticHookAnimator.render_composite_frame(3.5, config, (540, 960))
    assert f_after is None


def test_export_hook_sequence(tmp_path: Path):
    config = OpeningHookIntroConfig(
        enabled=True,
        hook_text="VIRAL REVEAL",
        supporting_text="Explained Simply",
        show_supporting_caption=True,
        animation_type="slam_in",
        wordart_style="slam_in",
        duration_sec=0.5,
    )

    fps = 10
    expected_frames = 5  # ceil(0.5 * 10) = 5
    seq_dir = tmp_path / "hook_seq_test"

    paths = KineticHookAnimator.export_hook_sequence(
        config=config,
        output_dir=seq_dir,
        fps=fps,
        canvas_dimensions=(270, 480),
    )

    assert len(paths) == expected_frames
    for p in paths:
        assert p.exists()
        with Image.open(p) as img:
            assert img.size == (270, 480)
            assert img.mode == "RGBA"
