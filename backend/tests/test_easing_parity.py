"""Unit tests verifying easing mathematical bounds and animation phase continuity."""

import pytest
from backend.app.services.easing import evaluate_easing, compute_animation_phase


def test_easing_boundaries():
    curves = [
        "linear",
        "ease_in_quad",
        "ease_out_quad",
        "ease_in_out_quad",
        "ease_in_cubic",
        "ease_out_cubic",
        "ease_in_out_cubic",
        "ease_out_back",
        "ease_out_elastic",
        "ease_out_bounce",
        "smoothstep",
        "slam_in",
    ]
    for curve in curves:
        val_0 = evaluate_easing(curve, 0.0)
        val_1 = evaluate_easing(curve, 1.0)
        assert abs(val_0 - 0.0) < 1e-4, f"Curve {curve} failed at t=0: got {val_0}"
        assert abs(val_1 - 1.0) < 1e-4, f"Curve {curve} failed at t=1: got {val_1}"


def test_easing_clamping():
    assert evaluate_easing("linear", -0.5) == 0.0
    assert evaluate_easing("linear", 1.5) == 1.0


def test_animation_phase_lifecycle():
    # 3 second element from t=1.0 to t=4.0
    start = 1.0
    duration = 3.0
    enter_dur = 0.5
    exit_dur = 0.5

    # Before start
    res_before = compute_animation_phase(0.5, start, duration, enter_dur, exit_dur)
    assert res_before["phase"] == "before"
    assert res_before["is_visible"] is False
    assert res_before["opacity"] == 0.0

    # Entering
    res_enter = compute_animation_phase(1.25, start, duration, enter_dur, exit_dur)
    assert res_enter["phase"] == "enter"
    assert res_enter["is_visible"] is True
    assert 0.0 <= res_enter["progress"] <= 1.0
    assert res_enter["opacity"] > 0.0

    # Holding
    res_hold = compute_animation_phase(2.5, start, duration, enter_dur, exit_dur)
    assert res_hold["phase"] == "hold"
    assert res_hold["is_visible"] is True
    assert res_hold["opacity"] == 1.0
    assert res_hold["scale"] == 1.0

    # Exiting
    res_exit = compute_animation_phase(3.8, start, duration, enter_dur, exit_dur)
    assert res_exit["phase"] == "exit"
    assert res_exit["is_visible"] is True
    assert 0.0 <= res_exit["progress"] <= 1.0

    # After end
    res_after = compute_animation_phase(4.5, start, duration, enter_dur, exit_dur)
    assert res_after["phase"] == "after"
    assert res_after["is_visible"] is False
