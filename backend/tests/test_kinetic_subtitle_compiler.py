import os
import json
from pathlib import Path
from backend.app.services.kinetic_subtitle_compiler import (
    KineticSubtitleCompiler,
    SubtitleQAService,
    format_ass_time,
)

SAMPLE_WORDS = [
    {"word": "You", "start": 0.42, "end": 0.68},
    {"word": "need", "start": 0.70, "end": 0.95},
    {"word": "to", "start": 0.98, "end": 1.10},
    {"word": "stop", "start": 1.12, "end": 1.55},
    {"word": "making", "start": 1.58, "end": 1.95},
    {"word": "this", "start": 1.98, "end": 2.20},
    {"word": "mistake.", "start": 2.22, "end": 2.80},
    # 0.6s silence gap
    {"word": "Because", "start": 3.40, "end": 3.75},
    {"word": "it", "start": 3.78, "end": 3.92},
    {"word": "destroys", "start": 3.95, "end": 4.45},
    {"word": "your", "start": 4.48, "end": 4.65},
    {"word": "audience", "start": 4.68, "end": 5.15},
    {"word": "retention.", "start": 5.18, "end": 5.80},
]


def test_format_ass_time():
    assert format_ass_time(0.0) == "0:00:00.00"
    assert format_ass_time(1.25) == "0:00:01.25"
    assert format_ass_time(65.50) == "0:01:05.50"
    assert format_ass_time(3661.05) == "1:01:01.05"


def test_compile_ass_kinetic_events(tmp_path):
    output_ass = tmp_path / "subtitles.ass"
    headline = "NEVER MAKE THIS MISTAKE"

    result_path = KineticSubtitleCompiler.compile_ass(
        words=SAMPLE_WORDS,
        output_path=str(output_ass),
        headline_text=headline,
        preset_name="mrbeast",
        custom_active_color="&H0000D7FF&",
        time_offset_sec=0.0,
    )

    assert Path(result_path).exists()
    content = output_ass.read_text(encoding="utf-8")

    # 1. Structure check
    assert "[Script Info]" in content
    assert "[V4+ Styles]" in content
    assert "Style: KineticSub" in content
    assert "Style: TopHeadline" in content
    assert "[Events]" in content

    # 2. Headline event
    assert headline in content

    # 3. Kinetic dialogue events check
    dialogue_lines = [line for line in content.splitlines() if line.startswith("Dialogue: 0,")]
    assert len(dialogue_lines) >= len(SAMPLE_WORDS)

    # 4. Active word tags check (Gold pop tag &H0000D7FF&)
    assert "{\\c&H0000D7FF&" in content
    assert "{\\r}" in content

    print(f"\n[Kinetic Subtitle Test] Successfully generated {len(dialogue_lines)} kinetic dialogue states.")
    print("Sample generated ASS events:")
    for l in dialogue_lines[:4]:
        print("  ", l)


def test_subtitle_qa_audit(tmp_path):
    ref_transcript = "You need to stop making this mistake. Because it destroys your audience retention."
    report = SubtitleQAService.audit_subtitles(
        clip_id="test_clip_qa",
        reference_transcript=ref_transcript,
        subtitles_words=SAMPLE_WORDS,
        output_dir=str(tmp_path),
    )

    assert report is not None
    assert "status" in report
    assert report["status"] in ["pass", "warning", "fail"]
    assert "summary" in report

    qa_report_file = tmp_path / "subtitle_qa_report.json"
    assert qa_report_file.exists()

    print(f"\n[Subtitle QA Report] Status: {report['status']}")
    print(f"Summary: {json.dumps(report.get('summary', {}))}")

