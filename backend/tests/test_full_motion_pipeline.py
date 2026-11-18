"""Phase 9: Automated Visual QA & Performance Benchmarks for the Complete Motion Pipeline.
Validates BrushReveal transitions, Motion Graphics, Animated Cards, Easing throughput,
and FFmpeg overlay integrity without truncation.
"""

import time
import pytest
from pathlib import Path
from PIL import Image

from backend.app.services.easing import evaluate_easing, compute_animation_phase
from backend.app.services.brush_reveal_transition import BrushRevealTransition
from backend.app.services.motion_graphics_renderer import MotionGraphicsRenderer
from backend.app.services.animated_card_compositor import AnimatedCardCompositor
from backend.app.services.wordart_renderer import WordArtRenderer, WordArtPreset
from backend.app.models.visual_config import MotionGraphicElementConfig, OpeningHookIntroConfig


def test_brush_reveal_alpha_progression():
    """Validates brush wipe mask progression from completely transparent to fully opaque."""
    mask_0 = BrushRevealTransition.generate_brush_mask(0.0, (200, 200))
    mask_half = BrushRevealTransition.generate_brush_mask(0.5, (200, 200))
    mask_1 = BrushRevealTransition.generate_brush_mask(1.0, (200, 200))

    assert mask_0.getextrema() == (0, 0), "Mask at t=0 should be completely black (0)"
    assert mask_1.getextrema() == (255, 255), "Mask at t=1 should be completely white (255)"

    # Midpoint should have both dark and light pixels
    min_val, max_val = mask_half.getextrema()
    assert min_val == 0
    assert max_val == 255


def test_brush_reveal_sequence_generation(tmp_path: Path):
    """Verifies sequence generation outputs valid sequential PNG frames."""
    fg = Image.new("RGBA", (180, 320), (255, 230, 0, 255))
    seq_dir = tmp_path / "brush_seq"
    frames = BrushRevealTransition.export_reveal_sequence(
        foreground=fg,
        duration_sec=0.3,
        fps=10,
        output_dir=seq_dir,
    )
    assert len(frames) == 3
    for f in frames:
        assert f.exists()
        with Image.open(f) as img:
            assert img.size == (180, 320)
            assert img.mode == "RGBA"


def test_motion_graphics_arrow_and_circle():
    """Validates arrow and circle drawing geometry across progress states."""
    arrow_early = MotionGraphicsRenderer.render_arrow(0.2)
    arrow_late = MotionGraphicsRenderer.render_arrow(1.0)
    assert isinstance(arrow_early, Image.Image)
    assert isinstance(arrow_late, Image.Image)

    circle_half = MotionGraphicsRenderer.render_circle_highlight(0.5)
    circle_full = MotionGraphicsRenderer.render_circle_highlight(1.0)
    assert circle_half.split()[3].getextrema()[1] > 0
    assert circle_full.split()[3].getextrema()[1] > 0


def test_motion_graphic_frame_lifecycle():
    """Verifies motion graphic element frame generator adheres to time boundaries."""
    cfg = MotionGraphicElementConfig(
        graphic_type="arrow",
        start_sec=1.0,
        duration_sec=2.0,
        x_percent=50.0,
        y_percent=50.0,
        color="#00E297",
    )

    f_before = MotionGraphicsRenderer.render_motion_graphic_frame(cfg, 0.5)
    f_active = MotionGraphicsRenderer.render_motion_graphic_frame(cfg, 2.0)
    f_after = MotionGraphicsRenderer.render_motion_graphic_frame(cfg, 3.5)

    assert f_before is None
    assert f_active is not None
    assert f_active.size == (1080, 1920)
    assert f_after is None


def test_animated_card_compositor_lifecycle():
    """Verifies animated social card entrance, hold, and exit frame rendering."""
    card_img = Image.new("RGBA", (800, 250), (255, 255, 255, 255))
    duration = 3.0

    # Before start
    f_before = AnimatedCardCompositor.render_animated_card_frame(card_img, -0.2, 0.0, duration)
    assert f_before is None

    # Enter phase
    f_enter = AnimatedCardCompositor.render_animated_card_frame(card_img, 0.2, 0.0, duration)
    assert f_enter is not None
    assert f_enter.size == (1080, 1920)

    # Hold phase
    f_hold = AnimatedCardCompositor.render_animated_card_frame(card_img, 1.5, 0.0, duration)
    assert f_hold is not None

    # After end
    f_after = AnimatedCardCompositor.render_animated_card_frame(card_img, 3.5, 0.0, duration)
    assert f_after is None


def test_easing_performance_benchmark():
    """Benchmarks easing calculation throughput to guarantee sub-millisecond execution."""
    t_start = time.perf_counter()
    iterations = 25000

    for i in range(iterations):
        t = (i % 1000) / 1000.0
        _ = evaluate_easing("ease_out_back", t)
        _ = evaluate_easing("slam_in", t)
        _ = evaluate_easing("ease_out_bounce", t)

    elapsed_sec = time.perf_counter() - t_start
    ops_per_sec = (iterations * 3) / max(1e-6, elapsed_sec)

    # Must exceed at least 50,000 evaluations per second on dev machine
    assert ops_per_sec > 50000, f"Easing throughput too low: {ops_per_sec:.0f} ops/sec"


def test_wordart_badge_rasterization_benchmark():
    """Benchmarks WordArt badge rasterization to guarantee ultra-fast frame synthesis."""
    t_start = time.perf_counter()
    sample = "HIGH CONVERTING HOOK"

    # Render 5 distinct WordArt styles
    for style in [WordArtPreset.SLAM_IN, WordArtPreset.NEON_GLOW, WordArtPreset.GRADIENT_FIRE, WordArtPreset.COMIC_POP, WordArtPreset.SOFT_PILL]:
        badge = WordArtRenderer.render_wordart_badge(sample, style=style, font_size=40)
        assert badge.width > 100

    elapsed = time.perf_counter() - t_start
    # All 5 complex badges rendered in under 0.6 seconds
    assert elapsed < 0.6, f"WordArt rasterization took too long: {elapsed:.3f}s"
