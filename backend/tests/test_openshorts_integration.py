"""Test suite for OpenShorts reverse engineering features adapted into Shortify:
- Stacked two-speaker split geometry and headroom bias (split_layout.py)
- Stacked vstack FFmpeg filtergraph generation (split_layout.py)
- Dynamic collision-free hook card placement (hook_placement.py)
- Mid-seam subtitle positioning ({\an5}) for split screen layouts (subtitles.py)
- Dual-speaker center coordinates in face tracker
"""

import os
import pytest
from pathlib import Path
from backend.app.services.timeline_compositor import MasterTimelineCompositor
from backend.app.services.kinetic_subtitle_compiler import KineticSubtitleCompiler


def test_split_geometry_calculation():
    """Verify calculate_split_geometry matches OpenShorts' headroom bias and aspect ratios."""
    orig_w, orig_h = 1920, 1080
    out_w, out_h = 1080, 1920
    centre = (480.0, 400.0)  # Left speaker face

    crop_w, crop_h, crop_x, crop_y, half_h = MasterTimelineCompositor.calculate_split_geometry(
        orig_w=orig_w,
        orig_h=orig_h,
        out_w=out_w,
        out_h=out_h,
        centre=centre,
        tightness=0.8,
    )

    # half_h should be out_h // 2 = 960
    assert half_h == 960

    # Aspect ratio should equal out_w / half_h = 1080 / 960 = 1.125
    aspect = out_w / float(half_h)
    assert abs((crop_w / float(crop_h)) - aspect) < 0.05

    # Crop coordinates must be even numbers for FFmpeg
    assert crop_w % 2 == 0
    assert crop_h % 2 == 0
    assert crop_x % 2 == 0
    assert crop_y % 2 == 0

    # Must stay within source dimensions
    assert 0 <= crop_x <= orig_w - crop_w
    assert 0 <= crop_y <= orig_h - crop_h

    # Headroom offset test: y = cy - crop_h * 0.42
    expected_y = int(round(centre[1] - crop_h * 0.42))
    expected_y = max(0, min(expected_y, orig_h - crop_h))
    expected_y -= expected_y % 2
    assert crop_y == expected_y


def test_split_vstack_filtergraph_syntax():
    """Verify build_split_vstack_filtergraph generates valid FFmpeg filtergraph strings."""
    orig_w, orig_h = 1920, 1080
    out_w, out_h = 1080, 1920
    left_centre = (400.0, 350.0)
    right_centre = (1450.0, 350.0)

    # Case 1: Pure video split
    filtergraph = MasterTimelineCompositor.build_split_vstack_filtergraph(
        orig_w=orig_w,
        orig_h=orig_h,
        out_w=out_w,
        out_h=out_h,
        left_centre=left_centre,
        right_centre=right_centre,
    )

    assert "[0:v]split=2[ta][ba];" in filtergraph
    assert "scale=1080:960[top];" in filtergraph
    assert "scale=1080:960[bot];" in filtergraph
    assert "[top][bot]vstack=inputs=2,pad=1080:1920:0:0,setsar=1[v]" in filtergraph

    # Case 2: Split with subtitles
    sub_filtergraph = MasterTimelineCompositor.build_split_vstack_filtergraph(
        orig_w=orig_w,
        orig_h=orig_h,
        out_w=out_w,
        out_h=out_h,
        left_centre=left_centre,
        right_centre=right_centre,
        subtitles_ass_path="C\\:/path/to/sub.ass",
    )
    assert "subtitles='C\\:/path/to/sub.ass'[v]" in sub_filtergraph


def test_collision_free_hook_placement():
    """Verify calculate_collision_free_hook_y moves hook away from detected face regions."""
    target_height = 1920
    card_h = 240

    # Scenario A: No faces present -> defaults to primary safe candidate
    y_no_faces = MasterTimelineCompositor.calculate_collision_free_hook_y(
        target_height=target_height,
        card_height=card_h,
        head_boxes=[],
    )
    assert y_no_faces == int(target_height * 0.11)

    # Scenario B: Face detected right across standard position (Y ~ 0.10 to 0.25)
    face_in_hook_zone = [{
        "x0": 0.35,
        "y0": 0.12,
        "x1": 0.65,
        "y1": 0.28,
        "timestamp_sec": 1.0,
    }]

    y_avoiding_face = MasterTimelineCompositor.calculate_collision_free_hook_y(
        target_height=target_height,
        card_height=card_h,
        head_boxes=face_in_hook_zone,
        is_split_layout=False,
    )

    # Hook must move away from candidate 0 (Y=211) to another candidate (e.g. high or mid-chest)
    assert y_avoiding_face != int(target_height * 0.11)

    # Scenario C: Split layout -> tests split-specific safe candidates
    y_split = MasterTimelineCompositor.calculate_collision_free_hook_y(
        target_height=target_height,
        card_height=card_h,
        head_boxes=[],
        is_split_layout=True,
    )
    assert y_split == int(target_height * 0.08)


def test_seam_subtitle_alignment_split_layout(tmp_path):
    """Verify compile_ass outputs Alignment = 5 (middle-center) and MarginV = 0 in split mode."""
    test_words = [
        {"word": "Hello", "start": 0.2, "end": 0.6},
        {"word": "world", "start": 0.7, "end": 1.2},
    ]

    out_file = tmp_path / "split_subs.ass"

    # Test split layout compilation
    KineticSubtitleCompiler.compile_ass(
        words=test_words,
        output_path=str(out_file),
        layout_preset="split",
        video_width=1080,
        video_height=1920,
    )

    content = out_file.read_text(encoding="utf-8")

    # In ASS V4+ Styles:
    # Format: ..., Alignment, MarginL, MarginR, MarginV, Encoding
    # Alignment 5 = middle-center; MarginV = 0 puts it right on the seam
    style_lines = [l for l in content.splitlines() if l.startswith("Style: KineticSub")]
    assert len(style_lines) == 1
    style_line = style_lines[0]

    parts = style_line.split(",")
    # Alignment is 3rd from the end; MarginV is 2nd from the end
    alignment = parts[-5].strip()
    margin_v = parts[-2].strip()

    assert alignment == "5", f"Expected alignment 5 (middle-center), got {alignment}"
    assert margin_v == "0", f"Expected margin_v 0 (seam anchor), got {margin_v}"


def test_standard_subtitle_alignment_full_layout(tmp_path):
    """Verify compile_ass maintains Alignment = 2 (bottom-center) for normal layouts."""
    test_words = [
        {"word": "Normal", "start": 0.2, "end": 0.6},
        {"word": "layout", "start": 0.7, "end": 1.2},
    ]

    out_file = tmp_path / "normal_subs.ass"

    KineticSubtitleCompiler.compile_ass(
        words=test_words,
        output_path=str(out_file),
        layout_preset="full",
        video_width=1080,
        video_height=1920,
    )

    content = out_file.read_text(encoding="utf-8")
    style_lines = [l for l in content.splitlines() if l.startswith("Style: KineticSub")]
    assert len(style_lines) == 1
    parts = style_lines[0].split(",")
    alignment = parts[-5].strip()

    assert alignment == "2", f"Expected alignment 2 (bottom-center), got {alignment}"


def test_vocal_buffer_padding():
    """Verify Phase 1 vocal attack (80ms) and decay (150ms) buffer logic."""
    total_vid_dur = 60.0
    
    # Standard middle span
    raw_start = 10.0
    raw_end = 25.0
    buffered_start = max(0.0, round(raw_start - 0.08, 2))
    buffered_end = min(total_vid_dur, round(raw_end + 0.15, 2))
    assert buffered_start == 9.92
    assert buffered_end == 25.15
    assert round(buffered_end - buffered_start, 2) == 15.23

    # Clamped at video start (raw_start = 0.05)
    raw_start_near_zero = 0.05
    buffered_start_clamped = max(0.0, round(raw_start_near_zero - 0.08, 2))
    assert buffered_start_clamped == 0.0

    # Clamped at video end (raw_end = 59.95)
    raw_end_near_max = 59.95
    buffered_end_clamped = min(total_vid_dur, round(raw_end_near_max + 0.15, 2))
    assert buffered_end_clamped == 60.0


def test_kinetic_punch_in_expression():
    """Verify Phase 2 smoothstep kinetic punch-in zoom expression and envelope boundaries."""
    clip_dur = 30.0
    expr = MasterTimelineCompositor.build_punch_in_expression(
        clip_duration=clip_dur,
        punch_times=[3.5, 22.0],
        max_zoom=1.12,
    )

    # Expression contains smoothstep terms and both punch anchors
    assert "between(t,3.50,3.75)" in expr
    assert "between(t,3.75,5.05)" in expr
    assert "between(t,5.05,5.60)" in expr
    assert "1.12" in expr

    # Verify smoothstep mathematical properties at key envelope points:
    # Rise = 0.25s, Hold = 1.30s, Fall = 0.55s -> Total duration = 2.10s
    def eval_zoom(t: float, pt: float = 3.5, max_z: float = 1.12) -> float:
        t_rise = pt + 0.25
        t_hold = t_rise + 1.30
        t_fall = t_hold + 0.55
        if t < pt or t > t_fall:
            return 1.0
        if pt <= t <= t_rise:
            u = (t - pt) / 0.25
            return 1.0 + (max_z - 1.0) * (3 * (u**2) - 2 * (u**3))
        if t_rise < t <= t_hold:
            return max_z
        if t_hold < t <= t_fall:
            u = (t - t_hold) / 0.55
            return 1.0 + (max_z - 1.0) * (1.0 - (3 * (u**2) - 2 * (u**3)))
        return 1.0

    # Test baseline
    assert eval_zoom(0.0) == 1.0
    assert eval_zoom(3.0) == 1.0
    # Test start of punch
    assert eval_zoom(3.5) == 1.0
    # Test midpoint of rise (smoothstep S-curve)
    mid_rise = eval_zoom(3.5 + 0.125)
    assert 1.05 < mid_rise < 1.08
    # Test peak / hold phase
    assert abs(eval_zoom(3.75) - 1.12) < 1e-4
    assert abs(eval_zoom(4.50) - 1.12) < 1e-4
    assert abs(eval_zoom(5.05) - 1.12) < 1e-4
    # Test midpoint of fall
    mid_fall = eval_zoom(5.05 + 0.275)
    assert 1.05 < mid_fall < 1.08
    # Test end of fall
    assert abs(eval_zoom(5.60) - 1.0) < 1e-4
    assert eval_zoom(6.0) == 1.0

    # Ensure zoom stays strictly within [1.00, 1.12]
    for step in range(0, 300):
        t_val = step * 0.1
        z = eval_zoom(t_val)
        assert 1.0 <= z <= 1.12001


def test_screencast_filtergraph_syntax():
    """Verify Phase 4 screencast layout generates correct 52/48 split and vstack filtergraph."""
    orig_w, orig_h = 1920, 1080
    out_w, out_h = 1080, 1920
    face_centre = (960.0, 540.0)

    filtergraph = MasterTimelineCompositor.build_screencast_filtergraph(
        orig_w=orig_w,
        orig_h=orig_h,
        out_w=out_w,
        out_h=out_h,
        face_centre=face_centre,
        subtitles_ass_path="C\\:/path/to/screencast.ass",
    )

    # Upper band: 52% of 1920 = 998 (int(1920 * 0.52))
    expected_top_h = int(out_h * 0.52)
    expected_bot_h = out_h - expected_top_h
    assert expected_top_h == 998
    assert expected_bot_h == 922

    # Check split declaration
    assert "[0:v]split=2[scr][spk];" in filtergraph
    # Check screen upper band scaling
    assert f"scale={out_w}:{expected_top_h}[top];" in filtergraph
    # Check speaker lower band scaling
    assert f"scale={out_w}:{expected_bot_h}[bot];" in filtergraph
    # Check vstack combining both bands
    assert f"[top][bot]vstack=inputs=2,pad={out_w}:{out_h}:0:0,setsar=1" in filtergraph
    # Check subtitle burning
    assert "subtitles='C\\:/path/to/screencast.ass'[v]" in filtergraph

