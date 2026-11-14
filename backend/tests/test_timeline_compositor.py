import os
import json
import asyncio
from pathlib import Path
from backend.app.services.timeline_compositor import (
    MasterTimelineCompositor,
    ContentPackagerService,
)

TEST_VIDEO = "backend/storage/uploads/yt_c3a708fa.mp4"
OUTPUT_DIR = "backend/storage/clips/test_master_timeline_pytest"


def test_content_packager_role_06(tmp_path):
    """Tests Role 06 (Content Packager) title alternatives and YouTube metadata."""
    transcript = "Here is the number one strategy that gets people to watch your entire video."
    result = ContentPackagerService.package_content(
        clip_id="test_pack_01",
        transcript=transcript,
        central_idea="Improving audience retention through curiosity pacing",
        opening_hook="Stop making this mistake when editing your videos.",
        output_dir=str(tmp_path),
    )

    assert result is not None
    assert "titles" in result
    assert len(result["titles"]) >= 1
    assert "description" in result
    assert "tags" in result
    assert "hashtags" in result

    pack_file = tmp_path / "packaging_metadata.json"
    assert pack_file.exists()
    print("\n[Role 06 Content Packager] Generated Titles:")
    for t in result["titles"]:
        print(f"  - [{t.get('angle', 'title')}]: {t.get('text')}")


def test_master_timeline_end_to_end_render():
    """Tests complete end-to-end pipeline: WordAligner -> Hooks -> TTS -> Kinetic Subtitles -> Concat -> final.mp4."""
    assert os.path.exists(TEST_VIDEO), f"Reference video {TEST_VIDEO} not found"
    out_dir = Path(OUTPUT_DIR)

    async def _run():
        return await MasterTimelineCompositor.process_and_render_clip(
            source_video_path=TEST_VIDEO,
            start_sec=23.1,
            end_sec=33.1, # 10s slice
            clip_id="test_master_clip",
            output_dir=str(out_dir),
            enable_opening_hook=True,
            opening_hook_text="Stop scrolling if you want your videos to actually go viral.",
            headline_text="THE VIRAL RETENTION SECRET",
            tts_voice="en-US-ChristopherNeural",
            subtitle_preset="mrbeast",
        )

    report = asyncio.run(_run())

    assert report["status"] == "success"
    assert report["total_duration_sec"] > 10.0 # 10s clip + ~3s intro hook

    # Verify all required output files exist
    files = report["output_files"]
    assert Path(files["final_video"]).exists()
    assert Path(files["transcript"]).exists()
    assert Path(files["word_alignment"]).exists()
    assert Path(files["hooks"]).exists()
    assert Path(files["opening_voice"]).exists()
    assert Path(files["subtitles_ass"]).exists()
    assert Path(files["subtitle_qa_report"]).exists()
    assert Path(files["packaging_metadata"]).exists()
    assert Path(files["render_report"]).exists()

    print(f"\n[Master Render Success] final.mp4 generated: {files['final_video']}")
    print(f"Total Duration: {report['total_duration_sec']}s (Clip: {report['clip_duration_sec']}s + Intro: {report['hooks']['opening_hook_duration_sec']}s)")
    print(f"Subtitle Words Aligned: {report['subtitles']['word_count']}")
    print(f"QA Status: {report['subtitles']['qa_status']}")

    # Test fast re-rendering
    fast_res = MasterTimelineCompositor.re_render_subtitles_fast(
        clip_dir=str(out_dir),
        subtitle_preset="clean_minimal",
        custom_font_name="Arial",
        headline_text="UPDATED HEADLINE TEXT",
    )
    assert fast_res["success"] is True
    print("[Fast Re-render Success] Re-rendered in seconds with 'clean_minimal' preset.")


def test_split_screen_with_minecraft_background(tmp_path):
    """Tests split-screen rendering with Minecraft Parkour gameplay on the bottom and speaker on top."""
    assert os.path.exists(TEST_VIDEO), f"Reference video {TEST_VIDEO} not found"
    bg_video = "backend/storage/backgrounds/minecraft_parkour.mp4"
    assert os.path.exists(bg_video), f"Minecraft background {bg_video} not found"

    async def _run():
        return await MasterTimelineCompositor.process_and_render_clip(
            source_video_path=TEST_VIDEO,
            start_sec=20.0,
            end_sec=25.0,  # 5s test slice
            clip_id="test_minecraft_split",
            output_dir=str(tmp_path),
            layout_mode="split_screen",
            background_video_path=bg_video,
            video_scale_percent=48,
            enable_opening_hook=False,  # No hook prepended by default
            headline_text="MINECRAFT SPLIT SCREEN TEST",
            subtitle_preset="tiktok_yellow",
            custom_font_name="Arial Black",
        )

    report = asyncio.run(_run())
    assert report["status"] == "success"
    final_video = Path(report["output_files"]["final_video"])
    assert final_video.exists()
    assert final_video.stat().st_size > 100_000
    print(f"\n[Split Screen Test Passed] final.mp4 size: {final_video.stat().st_size} bytes, duration: {report['total_duration_sec']}s")


