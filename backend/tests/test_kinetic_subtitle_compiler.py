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


def test_neon_glow_sharpness_and_contrast(tmp_path):
    """Verifies Neon subtitles have sharp, crisp outlines and controlled aura without blurry washed-out text."""
    output_ass = tmp_path / "neon.ass"
    words = [
        {"word": "UNREAL", "start": 0.5, "end": 0.9},
        {"word": "CLUTCH", "start": 0.95, "end": 1.4},
    ]
    KineticSubtitleCompiler.compile_ass(
        words=words,
        output_path=str(output_ass),
        preset_name="neon_glow",
        custom_animation="glow_pulse",
    )
    content = output_ass.read_text(encoding="utf-8")

    # 1. Style line must have crisp white primary color and pitch-black outline with thick stroke
    assert "Style: KineticSub" in content
    # PrimaryColour=&H00FFFFFF&, OutlineColour=&H00000000&, Outline>=4.5
    assert "&H00FFFFFF&" in content
    assert "&H00000000&" in content

    # 2. In dialogue event, neon aura must NOT blur out the border with \blur6
    assert "\\blur6" not in content
    # Must preserve crisp black outline (\3c&H00000000&) while casting aura (\4c)
    assert "\\3c&H00000000&" in content


def test_blue_and_coloured_contrast_elevation():
    """Verifies that dark or low-contrast blue colors are elevated to vivid electric azure for high contrast."""
    from backend.app.services.kinetic_subtitle_compiler import hex_to_ass_color

    # Pure dark blue (#0000FF) has low luminance (~29), should be boosted to electric azure
    ass_blue = hex_to_ass_color("#0000FF")
    assert ass_blue.startswith("&H00") and ass_blue.endswith("&")
    # Verify green/blue components ensure high luminance
    # Hex in ASS is &H00BBGGRR&
    b_hex = ass_blue[4:6] # BB
    g_hex = ass_blue[6:8] # GG
    assert int(b_hex, 16) >= 200
    assert int(g_hex, 16) >= 150 # elevated green gives azure brightness


def test_genuine_typewriter_character_by_character(tmp_path):
    """Verifies that Typewriter animation reveals characters sequentially (T -> TA -> TAP)
    while keeping completed words visible and matching actual speech timing.
    """
    output_ass = tmp_path / "typewriter.ass"
    words = [
        {"word": "TAP", "start": 1.0, "end": 1.3},
        {"word": "HERE", "start": 1.35, "end": 1.75},
    ]

    KineticSubtitleCompiler.compile_ass(
        words=words,
        output_path=str(output_ass),
        preset_name="typewriter",
        custom_animation="typewriter",
    )
    content = output_ass.read_text(encoding="utf-8")

    dialogue_lines = [l for l in content.splitlines() if l.startswith("Dialogue: 0,")]
    # Word 1 (TAP: 3 chars) + Word 2 (HERE: 4 chars) = at least 7 incremental events
    assert len(dialogue_lines) >= 7

    # Check incremental typing of "TAP"
    texts = [l.split(",,", 1)[1] for l in dialogue_lines]
    # Letter 1: "T"
    assert any("T{\\r}" in t for t in texts)
    # Letter 2: "TA"
    assert any("TA{\\r}" in t for t in texts)
    # Letter 3: "TAP"
    assert any("TAP{\\r}" in t for t in texts)

    # When typing "HERE", the completed prior word "TAP" MUST remain visible!
    assert any("TAP {\\c" in t and "H" in t for t in texts)
    assert any("TAP {\\c" in t and "HE" in t for t in texts)
    assert any("TAP {\\c" in t and "HER" in t for t in texts)
    assert any("TAP {\\c" in t and "HERE" in t for t in texts)


def test_all_presets_have_sufficient_contrast_and_outline():
    """Verifies that every preset in SubtitlePreset has an outline width >= 4.0
    and pure black outline for consistent legibility across all backgrounds.
    """
    from backend.app.services.kinetic_subtitle_compiler import SubtitlePreset

    for name, preset in SubtitlePreset.PRESETS.items():
        assert preset["outline_width"] >= 4.0, f"Preset '{name}' outline too thin ({preset['outline_width']})"
        assert preset["outline_color"] == "&H00000000&", f"Preset '{name}' must have pure black outline"
        assert preset["margin_v_ratio"] >= 0.18, f"Preset '{name}' margin too close to screen edge"

