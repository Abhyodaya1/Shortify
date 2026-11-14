"""Tests for Renderer Optimization, Legacy Fallback, and Perceptual QA (Task 6).
Verifies that legacy multipass remains the active production default, single-pass falls back safely,
and QualityAssuranceEngine executes black frame and audio silence detection.
"""

import asyncio
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from backend.app.services.quality_assurance import QualityAssuranceEngine
from backend.app.services.timeline_compositor import MasterTimelineCompositor


class TestQualityAssuranceEngine:
    """Verifies technical container & perceptual validation checks."""

    def test_missing_file_fails_qa(self):
        res = QualityAssuranceEngine.validate_short_mp4("non_existent_path.mp4", target_duration_sec=30.0)
        assert res["passed"] is False
        assert "Rendered video file does not exist" in res["issues"][0]

    def test_black_frame_detection_triggered(self):
        """Mock ffmpeg output containing black_start to verify detection flag."""
        fake_res = MagicMock()
        fake_res.stderr = "[blackdetect @ 000002] black_start:1.200 black_end:3.400 black_duration:2.200"
        with patch("subprocess.run", return_value=fake_res):
            assert QualityAssuranceEngine._detect_black_frames("dummy.mp4") is True

    def test_black_frame_detection_clean(self):
        fake_res = MagicMock()
        fake_res.stderr = "frame= 150 fps= 30 q=28.0 size= 512kB time=00:00:05.00 bitrate= 838.9kbits/s"
        with patch("subprocess.run", return_value=fake_res):
            assert QualityAssuranceEngine._detect_black_frames("dummy.mp4") is False

    def test_audio_silence_detection_triggered(self):
        """Mock ffmpeg output containing silence_start to verify detection flag."""
        fake_res = MagicMock()
        fake_res.stderr = "[silencedetect @ 000002] silence_start: 0.000 | silence_end: 4.500"
        with patch("subprocess.run", return_value=fake_res):
            assert QualityAssuranceEngine._detect_audio_silence("dummy.mp4", duration_threshold=2.0) is True

    def test_audio_silence_detection_clean(self):
        fake_res = MagicMock()
        fake_res.stderr = "size= 1024kB time=00:00:05.00"
        with patch("subprocess.run", return_value=fake_res):
            assert QualityAssuranceEngine._detect_audio_silence("dummy.mp4", duration_threshold=2.0) is False


class TestRendererSafeFallback:
    """Verifies that legacy multipass remains default and single-pass falls back safely."""

    def test_legacy_multipass_is_default(self, tmp_path):
        """When use_single_pass is False, _render_legacy_multipass must be invoked."""
        with patch.object(MasterTimelineCompositor, "_render_legacy_multipass") as mock_legacy, \
             patch.object(MasterTimelineCompositor, "_render_single_pass_filter_complex") as mock_single, \
             patch.object(MasterTimelineCompositor, "_measure_duration", return_value=5.0):

            # Create dummy media to pass initial checks
            dummy_src = tmp_path / "src.mp4"
            dummy_src.write_bytes(b"\x00" * 1024)

            fake_alignment = {
                "words": [{"word": "test", "start": 0.0, "end": 1.0}],
                "full_text": "test",
                "transcript": {"full_text": "test"},
            }
            fake_hooks = {
                "clip_id": "test",
                "recommended_selection": {"opening_hook": "test", "headline": "TEST", "ending_hook": ""},
            }

            from backend.app.services.word_aligner import WordAligner
            from backend.app.services.editorial_orchestrator import EditorialOrchestrator

            with patch.object(WordAligner, "align_clip", return_value=fake_alignment), \
                 patch.object(EditorialOrchestrator, "run_pipeline", return_value=fake_hooks):

                asyncio.run(MasterTimelineCompositor.process_and_render_clip(
                    source_video_path=str(dummy_src),
                    start_sec=0.0,
                    end_sec=5.0,
                    clip_id="test_clip",
                    output_dir=str(tmp_path / "out"),
                    use_single_pass=False,  # Explicit default
                ))

                assert mock_legacy.call_count == 1
                assert mock_single.call_count == 0

    def test_single_pass_falls_back_to_legacy_on_error(self, tmp_path):
        """If single-pass throws an exception, system must fall back to legacy multipass."""
        with patch.object(MasterTimelineCompositor, "_render_single_pass_filter_complex", side_effect=RuntimeError("FFmpeg NVENC crash")), \
             patch.object(MasterTimelineCompositor, "_render_legacy_multipass") as mock_legacy, \
             patch.object(MasterTimelineCompositor, "_measure_duration", return_value=5.0):

            dummy_src = tmp_path / "src.mp4"
            dummy_src.write_bytes(b"\x00" * 1024)

            fake_alignment = {
                "words": [{"word": "test", "start": 0.0, "end": 1.0}],
                "full_text": "test",
                "transcript": {"full_text": "test"},
            }
            fake_hooks = {
                "clip_id": "test",
                "recommended_selection": {"opening_hook": "test", "headline": "TEST", "ending_hook": ""},
            }

            from backend.app.services.word_aligner import WordAligner
            from backend.app.services.editorial_orchestrator import EditorialOrchestrator

            with patch.object(WordAligner, "align_clip", return_value=fake_alignment), \
                 patch.object(EditorialOrchestrator, "run_pipeline", return_value=fake_hooks):

                asyncio.run(MasterTimelineCompositor.process_and_render_clip(
                    source_video_path=str(dummy_src),
                    start_sec=0.0,
                    end_sec=5.0,
                    clip_id="test_clip_fallback",
                    output_dir=str(tmp_path / "out_fb"),
                    use_single_pass=True,
                ))

                # Legacy multipass must be called as safety net
                assert mock_legacy.call_count == 1
