"""Benchmark Harness: Single-Pass filter_complex vs Legacy Multi-Pass Renderer.
Measures wall-clock render latency, disk writes, and perceptual QA parity on RTX 3050 NVENC / CPU.
"""

from __future__ import annotations
import os
import sys
import time
import shutil
import asyncio
import subprocess
from pathlib import Path

# Ensure backend is on PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from unittest.mock import patch
from backend.app.services.timeline_compositor import MasterTimelineCompositor
from backend.app.services.quality_assurance import QualityAssuranceEngine
from backend.app.services.word_aligner import WordAligner
from backend.app.services.editorial_orchestrator import EditorialOrchestrator


def create_synthetic_test_video(output_path: Path, duration_sec: int = 5) -> Path:
    """Generates a synthetic 1920x1080 30fps MP4 with SMPTE test patterns and sine wave audio."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"smptebars=size=1920x1080:rate=30",
        "-f", "lavfi", "-i", "sine=frequency=1000:sample_rate=48000",
        "-t", str(duration_sec),
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        str(output_path.resolve()),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_path


def create_synthetic_background_video(output_path: Path, duration_sec: int = 10) -> Path:
    """Generates a synthetic 1080x1920 30fps vertical MP4 for background split."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"testsrc=size=1080x1920:rate=30",
        "-t", str(duration_sec),
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
        "-an",
        str(output_path.resolve()),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_path


def run_benchmark():
    work_dir = Path("backend/storage/benchmark_temp").resolve()
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("SHORTIFY MVP — RENDERING PIPELINE BENCHMARK HARNESS")
    print("=" * 70)

    # 1. Setup Test Assets
    print("[1/5] Generating synthetic test video (1920x1080, 5.0s, stereo audio)...")
    src_video = work_dir / "src_video.mp4"
    create_synthetic_test_video(src_video, duration_sec=5)

    bg_video = work_dir / "bg_video.mp4"
    create_synthetic_background_video(bg_video, duration_sec=10)

    fake_alignment = {
        "words": [
            {"word": "Shortify", "start": 0.5, "end": 1.2, "score": 0.98},
            {"word": "rendering", "start": 1.3, "end": 2.1, "score": 0.99},
            {"word": "benchmark", "start": 2.2, "end": 3.4, "score": 0.95},
            {"word": "validation", "start": 3.5, "end": 4.5, "score": 0.97},
        ],
        "full_text": "Shortify rendering benchmark validation",
        "transcript": {"full_text": "Shortify rendering benchmark validation"},
    }

    fake_hooks = {
        "clip_id": "bench",
        "recommended_selection": {
            "opening_hook": "Shortify Benchmark",
            "headline": "RENDER TEST",
            "ending_hook": "",
        },
    }

    with patch.object(WordAligner, "align_clip", return_value=fake_alignment), \
         patch.object(EditorialOrchestrator, "run_pipeline", return_value=fake_hooks):

        # 2. Benchmark Legacy Multi-Pass Renderer
        print("[2/5] Benchmarking Legacy Multi-Pass Renderer...")
        legacy_dir = work_dir / "legacy_out"
        legacy_dir.mkdir(parents=True, exist_ok=True)

        t0_legacy = time.perf_counter()
        res_legacy = asyncio.run(MasterTimelineCompositor.process_and_render_clip(
            clip_id="bench_legacy",
            source_video_path=str(src_video),
            start_sec=0.0,
            end_sec=5.0,
            output_dir=str(legacy_dir),
            layout_mode="split_screen",
            card_type="none",
            background_video_path=str(bg_video),
            video_scale_percent=50,
            enable_opening_hook=False,
            use_single_pass=False,
        ))
        t1_legacy = time.perf_counter()
        legacy_duration = t1_legacy - t0_legacy

        # Measure total bytes written in legacy dir
        legacy_bytes = sum(f.stat().st_size for f in legacy_dir.glob("*.*") if f.is_file())
        legacy_mp4s = list(legacy_dir.glob("*.mp4"))

        # 3. Benchmark Single-Pass Filter Complex Renderer
        print("[3/5] Benchmarking Single-Pass filter_complex Renderer...")
        single_dir = work_dir / "single_out"
        single_dir.mkdir(parents=True, exist_ok=True)

        t0_single = time.perf_counter()
        res_single = asyncio.run(MasterTimelineCompositor.process_and_render_clip(
            clip_id="bench_single",
            source_video_path=str(src_video),
            start_sec=0.0,
            end_sec=5.0,
            output_dir=str(single_dir),
            layout_mode="split_screen",
            card_type="none",
            background_video_path=str(bg_video),
            video_scale_percent=50,
            enable_opening_hook=False,
            use_single_pass=True,
        ))
        t1_single = time.perf_counter()
        single_duration = t1_single - t0_single

        single_bytes = sum(f.stat().st_size for f in single_dir.glob("*.*") if f.is_file())
        single_mp4s = list(single_dir.glob("*.mp4"))

    # 4. QA Validation & Perceptual Check on Outputs
    print("[4/5] Executing Perceptual QA & Container Validation on both outputs...")
    legacy_final = legacy_dir / "final.mp4"
    single_final = single_dir / "final.mp4"

    qa_legacy = QualityAssuranceEngine.validate_short_mp4(str(legacy_final), target_duration_sec=5.0)
    qa_single = QualityAssuranceEngine.validate_short_mp4(str(single_final), target_duration_sec=5.0)

    # 5. Output Results Table
    speedup_pct = ((legacy_duration - single_duration) / legacy_duration) * 100.0 if legacy_duration > 0 else 0.0
    disk_reduction_pct = ((legacy_bytes - single_bytes) / legacy_bytes) * 100.0 if legacy_bytes > 0 else 0.0

    print("\n" + "=" * 70)
    print("EMPIRICAL BENCHMARK RESULTS")
    print("=" * 70)
    print(f"{'Metric':<35} | {'Legacy Multi-Pass':<18} | {'Single-Pass':<18}")
    print("-" * 75)
    print(f"{'Wall-Clock Render Time (s)':<35} | {legacy_duration:<18.2f} | {single_duration:<18.2f}")
    print(f"{'Intermediate MP4 Count':<35} | {len(legacy_mp4s):<18} | {len(single_mp4s):<18}")
    print(f"{'Total Disk Writes (MB)':<35} | {legacy_bytes / (1024*1024):<18.2f} | {single_bytes / (1024*1024):<18.2f}")
    print(f"{'QA Container Validation':<35} | {str(qa_legacy['passed']):<18} | {str(qa_single['passed']):<18}")
    print(f"{'Black Frames Detected':<35} | {str(qa_legacy['checks'].get('black_frames_detected', False)):<18} | {str(qa_single['checks'].get('black_frames_detected', False)):<18}")
    print(f"{'Extended Silence Detected':<35} | {str(qa_legacy['checks'].get('extended_silence_detected', False)):<18} | {str(qa_single['checks'].get('extended_silence_detected', False)):<18}")
    print("-" * 75)
    print(f"Latency Delta: {speedup_pct:+.1f}% ({'FASTER' if speedup_pct > 0 else 'SLOWER'})")
    print(f"Disk Write Reduction: {disk_reduction_pct:+.1f}%")
    print("=" * 70)

    # Cleanup benchmark files
    try:
        shutil.rmtree(work_dir)
    except Exception:
        pass

    return {
        "legacy_duration_sec": legacy_duration,
        "single_duration_sec": single_duration,
        "speedup_pct": speedup_pct,
        "legacy_bytes_mb": legacy_bytes / (1024 * 1024),
        "single_bytes_mb": single_bytes / (1024 * 1024),
        "disk_reduction_pct": disk_reduction_pct,
        "qa_legacy_passed": qa_legacy["passed"],
        "qa_single_passed": qa_single["passed"],
    }


if __name__ == "__main__":
    run_benchmark()
