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
                resolved_str = str(self.model_path.resolve())
                if hasattr(cv2, "FaceDetectorYN") and hasattr(cv2.FaceDetectorYN, "create"):
                    self.detector = cv2.FaceDetectorYN.create(resolved_str, "", (320, 320))
                elif hasattr(cv2, "FaceDetectorYN_create"):
                    self.detector = cv2.FaceDetectorYN_create(resolved_str, "", (320, 320))
            except Exception as e:
                print(f"Warning: Could not initialize YuNet ({e})")

        # 2. Secondary fallback: Haar Cascade
        try:
            haar_path = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
            if os.path.exists(haar_path):
                self.haar_cascade = cv2.CascadeClassifier(haar_path)
        except Exception:
            pass

    def _detect_faces(self, frame: np.ndarray, src_w: int, src_h: int) -> List[Tuple[float, float, float, float]]:
        """Detects all visible faces in the frame using the 2-tier vision chain.
        Returns a list of (x, y, w, h) bounding boxes scaled to (src_w, src_h).
        """
        detect_w, detect_h = 480, 270
        detected_faces: List[Tuple[float, float, float, float]] = []

        # Tier 1: YuNet ONNX Deep Neural Network
        if self.detector is not None:
            try:
                self.detector.setInputSize((detect_w, detect_h))
                small = cv2.resize(frame, (detect_w, detect_h))
                retval, faces = self.detector.detect(small)
                if faces is not None and len(faces) > 0:
                    scale_x = src_w / detect_w
                    scale_y = src_h / detect_h
                    for f in faces:
                        fx = float(f[0] * scale_x)
                        fy = float(f[1] * scale_y)
                        fw = float(f[2] * scale_x)
                        fh = float(f[3] * scale_y)
                        # Filter out tiny noise artifacts
                        if fw > (src_w * 0.04) and fh > (src_h * 0.04):
                            detected_faces.append((fx, fy, fw, fh))
                    if detected_faces:
                        return detected_faces
            except Exception:
                pass

        # Tier 2: Haar Cascade fallback
        if self.haar_cascade is not None:
            try:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                small_gray = cv2.resize(gray, (detect_w, detect_h))
                faces = self.haar_cascade.detectMultiScale(small_gray, scaleFactor=1.2, minNeighbors=4)
                if len(faces) > 0:
                    scale_x = src_w / detect_w
                    scale_y = src_h / detect_h
                    for f in faces:
                        fx = float(f[0] * scale_x)
                        fy = float(f[1] * scale_y)
                        fw = float(f[2] * scale_x)
                        fh = float(f[3] * scale_y)
                        if fw > (src_w * 0.04) and fh > (src_h * 0.04):
                            detected_faces.append((fx, fy, fw, fh))
            except Exception:
                pass

        return detected_faces

    def _calculate_framing_target(
        self,
        faces: List[Tuple[float, float, float, float]],
        crop_w: int,
        src_w: int,
        prev_center_x: float,
    ) -> Optional[float]:
        """Calculates optimal horizontal framing target taking 1-person, 2-person conversation,
        or multi-person dynamics into account.
        """
        if not faces:
            return None

        # Case 1: Exactly 1 face - center directly on speaker's face
        if len(faces) == 1:
            f = faces[0]
            return float(f[0] + (f[2] / 2.0))

        # Case 2: 2 or more faces (Conversational Framing)
        # Calculate bounding span of all detected faces
        min_x = min(f[0] for f in faces)
        max_x = max(f[0] + f[2] for f in faces)
        span_w = max_x - min_x

        # If both faces fit comfortably inside 9:16 crop window (with 10% safety margin),
        # frame their midpoint so BOTH speaker and listener remain visible simultaneously!
        if span_w <= (crop_w * 0.88):
            midpoint = (min_x + max_x) / 2.0
            return float(midpoint)

        # Case 3: Faces are wider than 9:16 crop (split dialogue / wide shot).
        # We track the dominant speaker, using hysteresis to avoid jitter back-and-forth.
        # Find face closest to previous focus or largest face
        sorted_by_size = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
        primary = sorted_by_size[0]

        # Check if another face is closer to current camera position to prevent abrupt jumps
        for candidate in sorted_by_size[:2]:
            cand_cx = candidate[0] + (candidate[2] / 2.0)
            if abs(cand_cx - prev_center_x) < (crop_w * 0.35):
                primary = candidate
                break

        return float(primary[0] + (primary[2] / 2.0))

    def _detect_face_x(self, frame: np.ndarray, src_w: int, src_h: int) -> Optional[float]:
        """Backward-compatible helper returning single primary face center."""
        faces = self._detect_faces(frame, src_w, src_h)
        if faces:
            best_face = max(faces, key=lambda f: f[2] * f[3])
            return float(best_face[0] + (best_face[2] / 2.0))
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
        multi_speaker_frames = 0

        current_focus_x = float(center_x + (crop_w / 2.0))
        last_reliable_target_x = current_focus_x
        last_face_time = -999.0

        left_face_samples: List[Tuple[float, float]] = []
        right_face_samples: List[Tuple[float, float]] = []
        detected_head_boxes: List[Dict[str, float]] = []

        for i in range(target_samples):
            t_sec = start_sec + (i * step_sec)
            cap.set(cv2.CAP_PROP_POS_MSEC, t_sec * 1000.0)
            ret, frame = cap.read()
            if not ret:
                continue

            total_samples += 1
            rel_t = round(t_sec - start_sec, 2)
            timestamps.append(rel_t)

            detected_faces = self._detect_faces(frame, src_w, src_h)
            if detected_faces:
                face_count += 1
                last_face_time = rel_t
                if len(detected_faces) >= 2:
                    multi_speaker_frames += 1
                    top_two = sorted(detected_faces, key=lambda f: f[2] * f[3], reverse=True)[:2]
                    top_two.sort(key=lambda f: f[0])
                    f_left, f_right = top_two[0], top_two[1]
                    left_face_samples.append((f_left[0] + f_left[2] / 2.0, f_left[1] + f_left[3] / 2.0))
                    right_face_samples.append((f_right[0] + f_right[2] / 2.0, f_right[1] + f_right[3] / 2.0))
                elif len(detected_faces) == 1:
                    f = detected_faces[0]
                    cx = f[0] + f[2] / 2.0
                    cy = f[1] + f[3] / 2.0
                    if cx < (src_w / 2.0):
                        left_face_samples.append((cx, cy))
                    else:
                        right_face_samples.append((cx, cy))

                for fx, fy, fw, fh in detected_faces:
                    detected_head_boxes.append({
                        "x0": fx / float(src_w),
                        "y0": fy / float(src_h),
                        "x1": (fx + fw) / float(src_w),
                        "y1": (fy + fh) / float(src_h),
                        "timestamp_sec": rel_t,
                    })

                target_cx = self._calculate_framing_target(
                    faces=detected_faces,
                    crop_w=crop_w,
                    src_w=src_w,
                    prev_center_x=current_focus_x,
                )
                if target_cx is not None:
                    last_reliable_target_x = target_cx
                    current_focus_x = target_cx
                raw_centers.append(target_cx)
            else:
                # Occlusion / temporary disappearance holding window (2.5 seconds)
                if (rel_t - last_face_time) <= 2.5:
                    # Hold last reliable position securely
                    raw_centers.append(last_reliable_target_x)
                else:
                    # After holding window expires without any face, gracefully drift toward center
                    raw_centers.append(float(center_x + (crop_w / 2.0)))

        cap.release()

        # Compute smoothed crop trajectory using Exponential Moving Average (EMA)
        smooth_crops: List[Dict[str, Any]] = []
        prev_crop_x = float(center_x)
        alpha = 0.24  # EMA smoothing factor for cinematic panning

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
        has_face = detection_ratio >= 0.20

        # Check motion amplitude across keyframes
        x_spread = (max(crop_xs) - min(crop_xs)) if crop_xs else 0
        crop_expr = self.build_crop_expression(smooth_crops, max_x, default_x=avg_crop_x)

        framing_mode = "center_fallback"
        if has_face:
            framing_mode = "conversation_midpoint" if multi_speaker_frames >= 2 else "single_speaker"

        default_left_cx = src_w * 0.30
        default_right_cx = src_w * 0.70
        default_cy = src_h * 0.40

        left_speaker_center = (
            float(np.mean([s[0] for s in left_face_samples])) if left_face_samples else default_left_cx,
            float(np.mean([s[1] for s in left_face_samples])) if left_face_samples else default_cy,
        )
        right_speaker_center = (
            float(np.mean([s[0] for s in right_face_samples])) if right_face_samples else default_right_cx,
            float(np.mean([s[1] for s in right_face_samples])) if right_face_samples else default_cy,
        )

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
            "multi_speaker_detected": multi_speaker_frames >= 2,
            "left_speaker_center": left_speaker_center,
            "right_speaker_center": right_speaker_center,
            "detected_head_boxes": detected_head_boxes,
            "framing_mode": framing_mode,
            "audio_diarization_available": False,
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
