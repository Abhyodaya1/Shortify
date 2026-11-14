"""Unit tests for WordAligner acoustic word alignment."""

import os
from pathlib import Path
import pytest
from backend.app.services.word_aligner import WordAligner

TEST_VIDEO = "backend/storage/uploads/yt_c3a708fa.mp4"
OUTPUT_DIR = "backend/storage/clips/test_word_align_pytest"


def test_word_aligner_extract_and_align():
    assert os.path.exists(TEST_VIDEO), f"Reference video {TEST_VIDEO} not found"
    
    out_dir = Path(OUTPUT_DIR)
    
    res = WordAligner.align_clip(
        source_media_path=TEST_VIDEO,
        start_sec=23.1,
        end_sec=35.1, # 12s test slice
        output_dir=str(out_dir),
        clip_id="test_align",
    )

    # 1. Output files exist
    assert os.path.exists(res["audio_path"])
    assert os.path.exists(res["transcript_path"])
    assert os.path.exists(res["word_alignment_path"])

    # 2. Audio file has content
    assert os.path.getsize(res["audio_path"]) > 10000

    # 3. Words extracted
    words = res["words"]
    assert len(words) >= 5, f"Expected at least 5 words, got {len(words)}"
    assert len(res["full_text"]) > 10

    # 4. Strict timing and monotonicity validation
    for i in range(len(words)):
        w = words[i]
        assert w["start"] >= 0.0
        assert w["end"] > w["start"]
        assert len(w["word"]) > 0
        if i > 0:
            assert w["start"] >= words[i-1]["start"], f"Timestamp inversion at {i}: {w} vs {words[i-1]}"

    print(f"\nExtracted {len(words)} aligned words:")
    for w in words[:6]:
        print(f"   [{w['start']}s -> {w['end']}s] {w['word']}")

