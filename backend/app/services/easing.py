"""Shared Deterministic Easing & Animation Timing Engine (Python).
Provides 1:1 mathematical parity with frontend/components/visual-style-studio/easing.ts
"""

from __future__ import annotations
import math
from typing import Dict, Any, Literal

EasingType = Literal[
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


def evaluate_easing(easing_type: str, t: float) -> float:
    """Evaluates an easing curve at parameter t in [0.0, 1.0]."""
    clamped_t = max(0.0, min(1.0, float(t)))

    if easing_type == "linear":
        return clamped_t

    elif easing_type == "ease_in_quad":
        return clamped_t * clamped_t

    elif easing_type == "ease_out_quad":
        return clamped_t * (2.0 - clamped_t)

    elif easing_type == "ease_in_out_quad":
        if clamped_t < 0.5:
            return 2.0 * clamped_t * clamped_t
        else:
            return -1.0 + (4.0 - 2.0 * clamped_t) * clamped_t

    elif easing_type == "ease_in_cubic":
        return clamped_t * clamped_t * clamped_t

    elif easing_type == "ease_out_cubic":
        f = clamped_t - 1.0
        return f * f * f + 1.0

    elif easing_type == "ease_in_out_cubic":
        if clamped_t < 0.5:
            return 4.0 * clamped_t * clamped_t * clamped_t
        else:
            return (clamped_t - 1.0) * (2.0 * clamped_t - 2.0) * (2.0 * clamped_t - 2.0) + 1.0

    elif easing_type == "ease_out_back":
        c1 = 1.70158
        c3 = c1 + 1.0
        f = clamped_t - 1.0
        return 1.0 + c3 * (f * f * f) + c1 * (f * f)

    elif easing_type == "ease_out_elastic":
        if clamped_t == 0.0:
            return 0.0
        if clamped_t == 1.0:
            return 1.0
        p = 0.3
        s = p / 4.0
        return (2.0 ** (-10.0 * clamped_t)) * math.sin(((clamped_t - s) * (2.0 * math.pi)) / p) + 1.0

    elif easing_type == "ease_out_bounce":
        x = clamped_t
        n1 = 7.5625
        d1 = 2.75
        if x < 1.0 / d1:
            return n1 * x * x
        elif x < 2.0 / d1:
            x -= 1.5 / d1
            return n1 * x * x + 0.75
        elif x < 2.5 / d1:
            x -= 2.25 / d1
            return n1 * x * x + 0.9375
        else:
            x -= 2.625 / d1
            return n1 * x * x + 0.984375

    elif easing_type == "smoothstep":
        return clamped_t * clamped_t * (3.0 - 2.0 * clamped_t)

    elif easing_type == "slam_in":
        if clamped_t < 0.7:
            sub = clamped_t / 0.7
            return sub * sub * 1.15
        else:
            sub = (clamped_t - 0.7) / 0.3
            return 1.15 - 0.15 * math.sin((sub * math.pi) / 2.0)

    else:
        return clamped_t


def compute_animation_phase(
    current_time_sec: float,
    start_time_sec: float,
    duration_sec: float,
    enter_duration_sec: float = 0.35,
    exit_duration_sec: float = 0.3,
    enter_easing: str = "ease_out_back",
    exit_easing: str = "ease_in_cubic",
) -> Dict[str, Any]:
    """Three-phase animation calculator: Enter -> Hold -> Exit."""
    end_time_sec = start_time_sec + duration_sec

    if current_time_sec < start_time_sec:
        return {
            "phase": "before",
            "progress": 0.0,
            "eased_progress": 0.0,
            "opacity": 0.0,
            "scale": 0.0,
            "translate_y": 0.0,
            "is_visible": False,
        }

    if current_time_sec >= end_time_sec:
        return {
            "phase": "after",
            "progress": 1.0,
            "eased_progress": 1.0,
            "opacity": 0.0,
            "scale": 1.0,
            "translate_y": 0.0,
            "is_visible": False,
        }

    elapsed = current_time_sec - start_time_sec
    clamped_enter_dur = max(0.01, min(enter_duration_sec, duration_sec * 0.45))
    clamped_exit_dur = max(0.01, min(exit_duration_sec, duration_sec * 0.45))
    hold_start_sec = clamped_enter_dur
    exit_start_sec = duration_sec - clamped_exit_dur

    # Phase 1: Enter
    if elapsed < hold_start_sec:
        raw_progress = elapsed / clamped_enter_dur
        eased = evaluate_easing(enter_easing, raw_progress)
        return {
            "phase": "enter",
            "progress": raw_progress,
            "eased_progress": eased,
            "opacity": min(1.0, raw_progress * 2.0),
            "scale": 0.7 + 0.3 * eased,
            "translate_y": (1.0 - eased) * 40.0,
            "is_visible": True,
        }

    # Phase 3: Exit
    if elapsed >= exit_start_sec:
        exit_elapsed = elapsed - exit_start_sec
        raw_progress = exit_elapsed / clamped_exit_dur
        eased = evaluate_easing(exit_easing, raw_progress)
        return {
            "phase": "exit",
            "progress": raw_progress,
            "eased_progress": eased,
            "opacity": max(0.0, 1.0 - eased),
            "scale": 1.0 - 0.15 * eased,
            "translate_y": -eased * 30.0,
            "is_visible": True,
        }

    # Phase 2: Hold
    hold_duration = exit_start_sec - hold_start_sec
    hold_elapsed = elapsed - hold_start_sec
    raw_progress = hold_elapsed / hold_duration if hold_duration > 0 else 1.0

    return {
        "phase": "hold",
        "progress": raw_progress,
        "eased_progress": 1.0,
        "opacity": 1.0,
        "scale": 1.0,
        "translate_y": 0.0,
        "is_visible": True,
    }
