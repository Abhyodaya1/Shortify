"""Face Tracking & Dynamic 9:16 Re-framing Engine using OpenCV YuNet & Haar Cascade.
Computes butter-smooth speaker panning with Exponential Moving Average (EMA) smoothing.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import cv2
import numpy as np

MODEL_PATH = Path("backend/models/face_detection_yunet_2023mar.onnx")


class FaceTrackingReframer:
    """Detects speaker faces across video segments and computes smooth 9:16 vertical crop windows."""

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = Path(model_path) if model_path else MODEL_PATH
        self.detector = None
        self.haar_cascade = None

        # 1. Primary: YuNet ONNX Deep Neural Network
        if self.model_path.exists():
            try:
                self.detector = cv2.FaceDetectorYN_create(str(self.model_path), "", (320, 320))
            except Exception as e:
                print(f"Warning: Could not initialize YuNet ({e})")

        # 2. Secondary fallback: Haar Cascade
        try:
            haar_path = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
            if os.path.exists(haar_path):
                self.haar_cascade = cv2.CascadeClassifier(haar_path)
        except Exception:
            pass

    def _detect_face_x(self, frame: np.ndarray, src_w: int, src_h: int) -> Optional[float]:
        """Detects the primary speaker's center X coordinate using the 2-tier vision chain."""
        detect_w, detect_h = 480, 270

        # Tier 1: YuNet
        if self.detector is not None:
            try:
                self.detector.setInputSize((detect_w, detect_h))
                small = cv2.resize(frame, (detect_w, detect_h))
                retval, faces = self.detector.detect(small)
                if faces is not None and len(faces) > 0:
                    best_face = max(faces, key=lambda f: f[2] * f[3])
                    scale_x = src_w / detect_w
                    fx, fw = best_face[0] * scale_x, best_face[2] * scale_x
                    return float(fx + (fw / 2.0))
            except Exception:
                pass

        # Tier 2: Haar Cascade fallback
        if self.haar_cascade is not None:
            try:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                small_gray = cv2.resize(gray, (detect_w, detect_h))
                faces = self.haar_cascade.detectMultiScale(small_gray, scaleFactor=1.2, minNeighbors=4)
                if len(faces) > 0:
                    best_face = max(faces, key=lambda f: f[2] * f[3])
                    scale_x = src_w / detect_w
                    fx, fw = best_face[0] * scale_x, best_face[2] * scale_x
                    return float(fx + (fw / 2.0))
            except Exception:
                pass

        return None

    def track_clip_faces(
        self,
        video_filepath: str,
        start_sec: float,
        end_sec: float,
        sample_fps: float = 3.0,
    ) -> Dict[str, Any]:
        """Analyzes video frames across [start_sec, end_sec] and computes smooth 9:16 crop trajectory."""
        cap = cv2.VideoCapture(video_filepath)
        if not cap.isOpened():
            return self._default_center_crop(1920, 1080)

        src_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1920
        src_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 1080

        # Calculate 9:16 crop width
        crop_h = src_h
        crop_w = int(src_h * 9 / 16)
        if crop_w > src_w:
            crop_w = src_w
            crop_h = int(src_w * 16 / 9)

        max_x = max(0, src_w - crop_w)
        center_x = max_x // 2

        duration = max(1.0, end_sec - start_sec)
        # Sample 5 to 10 keyframe anchors evenly across the clip for smooth panning
        target_samples = max(5, min(10, int(duration / 3.5)))
        step_sec = duration / max(1, target_samples)

        raw_centers = []
        timestamps = []
        face_count = 0
        total_samples = 0

        for i in range(target_samples):
            t_sec = start_sec + (i * step_sec)
            cap.set(cv2.CAP_PROP_POS_MSEC, t_sec * 1000.0)
            ret, frame = cap.read()
            if not ret:
                continue

            total_samples += 1
            rel_t = round(t_sec - start_sec, 2)
            timestamps.append(rel_t)

            detected_x = self._detect_face_x(frame, src_w, src_h)
            if detected_x is not None:
                face_count += 1
            raw_centers.append(detected_x)

        cap.release()

        # Compute smoothed crop trajectory using Exponential Moving Average (EMA)
        smooth_crops: List[Dict[str, Any]] = []
        prev_crop_x = float(center_x)
        alpha = 0.22  # EMA smoothing factor for cinematic panning

        for rel_t, raw_x in zip(timestamps, raw_centers):
            if raw_x is not None:
                target_crop_x = raw_x - (crop_w / 2.0)
            else:
                target_crop_x = prev_crop_x

            # Clamp within frame boundaries
            target_crop_x = max(0.0, min(float(max_x), target_crop_x))
            smooth_x = alpha * target_crop_x + (1.0 - alpha) * prev_crop_x
            prev_crop_x = smooth_x

            smooth_crops.append({
                "timestamp_sec": rel_t,
                "crop_x": int(round(smooth_x)),
            })

        crop_xs = [c["crop_x"] for c in smooth_crops]
        avg_crop_x = int(np.mean(crop_xs)) if crop_xs else center_x
        detection_ratio = round(face_count / max(1, total_samples), 2)
        has_face = detection_ratio >= 0.25

        # Check motion amplitude across keyframes
        x_spread = (max(crop_xs) - min(crop_xs)) if crop_xs else 0
        crop_expr = self.build_crop_expression(smooth_crops, max_x, default_x=avg_crop_x)

        return {
            "source_width": src_w,
            "source_height": src_h,
            "crop_width": crop_w,
            "crop_height": crop_h,
            "optimal_crop_x": avg_crop_x,
            "optimal_crop_y": 0,
            "crop_expr": crop_expr,
            "has_motion": x_spread >= 25,
            "face_detection_ratio": detection_ratio,
            "face_locked": has_face,
            "keyframes": smooth_crops,
        }

    @staticmethod
    def build_crop_expression(keyframes: List[Dict[str, Any]], max_x: int, default_x: int) -> str:
        """Constructs a smooth piecewise linear FFmpeg crop expression for buttery camera panning."""
        if not keyframes or len(keyframes) < 2:
            return str(default_x)

        # If motion across the whole segment is minimal (< 25px), use static crop to prevent micro-jitter
        xs = [k["crop_x"] for k in keyframes]
        if max(xs) - min(xs) < 25:
            return str(default_x)

        # Build nested if(lt(t, t_next), x_prev + (x_next-x_prev)*(t-t_prev)/(t_next-t_prev), ...)
        expr = str(keyframes[-1]["crop_x"])
        for i in range(len(keyframes) - 2, -1, -1):
            t0 = keyframes[i]["timestamp_sec"]
            x0 = keyframes[i]["crop_x"]
            t1 = keyframes[i + 1]["timestamp_sec"]
            x1 = keyframes[i + 1]["crop_x"]
            dt = max(0.1, t1 - t0)
            dx = x1 - x0

            # Linear interpolation clamped within bounds
            lerp = f"({x0} + ({dx}) * (t - {t0}) / {dt:.2f})"
            expr = f"if(lt(t,{t1}), {lerp}, {expr})"

        return f"max(0,min({max_x},{expr}))"

    @staticmethod
    def _default_center_crop(src_w: int, src_h: int) -> Dict[str, Any]:
        crop_h = src_h
        crop_w = int(src_h * 9 / 16)
        crop_x = max(0, (src_w - crop_w) // 2)
        return {
            "source_width": src_w,
            "source_height": src_h,
            "crop_width": crop_w,
            "crop_height": crop_h,
            "optimal_crop_x": crop_x,
            "optimal_crop_y": 0,
            "crop_expr": str(crop_x),
            "has_motion": False,
            "face_detection_ratio": 0.0,
            "face_locked": False,
            "keyframes": [],
        }
