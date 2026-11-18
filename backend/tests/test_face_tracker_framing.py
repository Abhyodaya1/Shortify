"""Unit tests for Face Tracking & 2-Person Conversational Framing."""

import pytest
from backend.app.services.face_tracker import FaceTrackingReframer


def test_single_person_framing():
    reframer = FaceTrackingReframer()
    # 1 face at x=500, w=120
    faces = [(500.0, 100.0, 120.0, 120.0)]
    target = reframer._calculate_framing_target(faces, crop_w=607, src_w=1920, prev_center_x=960.0)
    # Target center should be 500 + 60 = 560
    assert target == pytest.approx(560.0)


def test_two_person_conversation_fitting_in_frame():
    reframer = FaceTrackingReframer()
    crop_w = 607  # 1080 * 9 / 16 on 1920x1080
    # Two people sitting side-by-side: Face 1 at 700 (w=100), Face 2 at 1050 (w=100)
    # Span is 1150 - 700 = 450px <= 607 * 0.88 (534px)
    faces = [(700.0, 150.0, 100.0, 100.0), (1050.0, 150.0, 100.0, 100.0)]
    target = reframer._calculate_framing_target(faces, crop_w=crop_w, src_w=1920, prev_center_x=960.0)
    # Midpoint should keep BOTH faces in frame: (700 + 1150) / 2 = 925
    assert target == pytest.approx(925.0)


def test_two_person_wide_shot_hysteresis():
    reframer = FaceTrackingReframer()
    crop_w = 607
    # Two people far apart: Face 1 at 300, Face 2 at 1500 -> Span = 1300 > crop_w
    faces = [
        (300.0, 150.0, 120.0, 120.0),
        (1500.0, 150.0, 130.0, 130.0),
    ]
    # If camera was previously focused near Person 1 (x=360), hysteresis keeps focus on Person 1
    target = reframer._calculate_framing_target(faces, crop_w=crop_w, src_w=1920, prev_center_x=380.0)
    assert target == pytest.approx(360.0)


def test_empty_faces_returns_none():
    reframer = FaceTrackingReframer()
    target = reframer._calculate_framing_target([], crop_w=607, src_w=1920, prev_center_x=960.0)
    assert target is None
