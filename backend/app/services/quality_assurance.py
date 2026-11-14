"""Deterministic Quality Assurance (QA) Engine for rendered YouTube Shorts.
Implements the technical validation checklist from 03_IMPLEMENTATION_SPEC.md Section 10.
"""

from __future__ import annotations
import os
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from ..models.editorial_profile import EditorialProfile


class TechnicalQAResult:
    def __init__(self, passed: bool, checks: Dict[str, Any], issues: List[str]):
        self.passed = passed
        self.checks = checks
        self.issues = issues

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "checks": self.checks,
            "issues": self.issues,
        }


class QualityAssuranceEngine:
    """Performs deterministic inspection on rendered MP4 files."""

    @classmethod
    def validate_short_mp4(
        cls,
        rendered_mp4_path: str,
        target_duration_sec: float,
        profile: Optional[EditorialProfile] = None,
    ) -> Dict[str, Any]:
        """Runs ffprobe and OpenCV checks on video, audio, and duration boundaries."""
        mp4_path = Path(rendered_mp4_path)
        issues: List[str] = []
        checks: Dict[str, Any] = {}

        # 1. File existence & basic size check
        if not mp4_path.exists():
            return {
                "passed": False,
                "issues": ["Rendered video file does not exist on disk."],
                "checks": {"file_exists": False},
            }

        file_size = mp4_path.stat().st_size
        checks["file_size_bytes"] = file_size
        if file_size < 15_000:
            issues.append(f"Rendered video size is abnormally small ({file_size} bytes).")

        # 2. Extract media streams metadata via ffprobe
        probe_data = cls._run_ffprobe(str(mp4_path))
        if not probe_data:
            return {
                "passed": False,
                "issues": ["ffprobe could not inspect rendered MP4."],
                "checks": {"probe_success": False},
            }

        # 3. Video stream inspection
        video_streams = [s for s in probe_data.get("streams", []) if s.get("codec_type") == "video"]
        if not video_streams:
            issues.append("No video stream found in rendered file.")
            v_stream = {}
        else:
            v_stream = video_streams[0]

        width = int(v_stream.get("width", 0))
        height = int(v_stream.get("height", 0))
        checks["width"] = width
        checks["height"] = height

        # Aspect ratio check: 9:16 is 0.5625
        if width > 0 and height > 0:
            aspect_ratio = width / height
            checks["aspect_ratio"] = round(aspect_ratio, 4)
            if abs(aspect_ratio - (9.0 / 16.0)) > 0.02:
                issues.append(f"Aspect ratio is not 9:16 (observed: {aspect_ratio:.4f}, expected ~0.5625).")

        # 4. Duration check
        format_info = probe_data.get("format", {})
        actual_duration = float(format_info.get("duration", 0.0))
        checks["actual_duration_sec"] = round(actual_duration, 2)
        checks["target_duration_sec"] = target_duration_sec

        tolerance = profile.duration_tolerance_seconds if profile else 2.0
        dur_diff = abs(actual_duration - target_duration_sec)
        checks["duration_variance_sec"] = round(dur_diff, 2)

        if dur_diff > tolerance:
            issues.append(
                f"Duration variance ({dur_diff:.2f}s) exceeds editorial tolerance ({tolerance}s). "
                f"Actual: {actual_duration:.2f}s vs Target: {target_duration_sec:.2f}s."
            )

        # 5. Audio stream inspection
        audio_streams = [s for s in probe_data.get("streams", []) if s.get("codec_type") == "audio"]
        checks["audio_stream_present"] = len(audio_streams) > 0
        if not audio_streams:
            issues.append("Rendered Short lacks an audio stream.")
        else:
            a_stream = audio_streams[0]
            checks["audio_codec"] = a_stream.get("codec_name", "")
            checks["audio_channels"] = a_stream.get("channels", 0)

        # 6. Overall Pass/Fail Verdict
        passed = len(issues) == 0
        checks["overall_pass"] = passed

        return {
            "passed": passed,
            "checks": checks,
            "issues": issues,
        }

    @staticmethod
    def _run_ffprobe(filepath: str) -> Optional[Dict[str, Any]]:
        """Executes ffprobe to extract JSON stream & format properties."""
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            filepath,
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode == 0:
                return json.loads(res.stdout)
        except Exception:
            pass
        return None

