"""Tests for Long Video Ingestion & Targeted Range Clipping Engine.
Verifies that:
- Long videos (1h+, 10h+, 24h VODs) bypass full 20GB downloads using metadata & transcript-first ingestion.
- Targeted range downloads extract only requested 30-60s candidate windows via HTTP range requests.
- Missing audio transcripts on long media are segmented into 30-min chunks with cumulative timestamps.
- Render & face tracking pipelines consume targeted range clips cleanly without full source dependencies.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from backend.app.services.video_ingestion import IngestionService


def test_targeted_range_flag_for_long_videos():
    """Verify that videos longer than 15 minutes (e.g. 10 hours) bypass full video download."""
    mock_info = {
        "id": "qSyo5d-dVzA",
        "title": "GTA 6 Livestream 10 Hours",
        "duration": 36000.0,  # 10 hours
        "thumbnail": "https://img.youtube.com/vi/qSyo5d-dVzA/0.jpg",
        "width": 1920,
        "height": 1080,
        "fps": 60.0,
        "live_status": "post_live",
    }

    mock_transcript = [
        {"start": 100.0, "duration": 4.0, "text": "This mission is incredible."},
        {"start": 104.0, "duration": 5.0, "text": "Look at the graphics right here."},
    ]

    with patch("yt_dlp.YoutubeDL") as MockYDL, \
         patch("backend.app.services.url_security_validator.URLSecurityValidator.validate_url", return_value=("https://www.youtube.com/live/qSyo5d-dVzA", "qSyo5d-dVzA")), \
         patch("youtube_transcript_api.YouTubeTranscriptApi.list") as mock_list_transcripts:
        
        # Mock metadata-only extraction (download=False)
        mock_instance = MockYDL.return_value.__enter__.return_value
        mock_instance.extract_info.return_value = mock_info

        # Mock caption retrieval
        mock_trans_obj = MagicMock()
        mock_trans_obj.fetch.return_value = mock_transcript
        mock_transcript_list = MagicMock()
        mock_transcript_list.find_transcript.return_value = mock_trans_obj
        mock_list_transcripts.return_value = mock_transcript_list

        data = IngestionService.ingest_youtube_url("https://www.youtube.com/live/qSyo5d-dVzA")

        # Must flag targeted ranges and NOT attempt full download
        assert data["is_targeted_ranges"] is True
        assert data["filepath"] == ""
        assert data["duration_sec"] == 36000.0
        assert data["title"] == "GTA 6 Livestream 10 Hours"
        assert len(data["transcript_cues"]) == 2
        assert data["transcript_cues"][0]["text"] == "This mission is incredible."
        assert data["transcript_cues"][0]["start_sec"] == 100.0
        assert data["transcript_cues"][0]["end_sec"] == 104.0

        # Verify extract_info was called with download=False
        mock_instance.extract_info.assert_called_once()
        _, kwargs = mock_instance.extract_info.call_args
        assert kwargs.get("download") is False


def test_short_video_downloads_full_stream():
    """Verify that short videos (<= 15 minutes) proceed with standard full download."""
    mock_info = {
        "id": "dQw4w9WgXcQ",
        "title": "Short Video",
        "duration": 212.0,  # 3.5 minutes
        "thumbnail": "https://img.youtube.com/vi/dQw4w9WgXcQ/0.jpg",
        "width": 1920,
        "height": 1080,
        "fps": 30.0,
        "live_status": "not_live",
    }

    mock_transcript = [
        {"start": 0.0, "duration": 3.0, "text": "We're no strangers to love."},
    ]

    with patch("yt_dlp.YoutubeDL") as MockYDL, \
         patch("backend.app.services.url_security_validator.URLSecurityValidator.validate_url", return_value=("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ")), \
         patch("youtube_transcript_api.YouTubeTranscriptApi.list") as mock_list_transcripts, \
         patch.object(IngestionService, "get_video_dimensions", return_value=(1920, 1080, 30.0)):

        mock_instance = MockYDL.return_value.__enter__.return_value
        mock_instance.extract_info.return_value = mock_info
        mock_instance.download.return_value = 0

        mock_trans_obj = MagicMock()
        mock_trans_obj.fetch.return_value = mock_transcript
        mock_transcript_list = MagicMock()
        mock_transcript_list.find_transcript.return_value = mock_trans_obj
        mock_list_transcripts.return_value = mock_transcript_list

        data = IngestionService.ingest_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        assert data["is_targeted_ranges"] is False
        assert data["duration_sec"] == 212.0
        assert data["title"] == "Short Video"


def test_download_clip_section_range_math(tmp_path):
    """Verify that download_clip_section sets up accurate range padding and ffmpeg trim parameters."""
    clip_id = "test_range_math_clip"
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    start_sec = 120.0
    end_sec = 151.0

    # Mock yt_dlp and subprocess
    with patch("yt_dlp.YoutubeDL") as MockYDL, \
         patch("backend.app.services.url_security_validator.URLSecurityValidator.validate_url", return_value=(url, "dQw4w9WgXcQ")), \
         patch("subprocess.run") as mock_run:

        # Create a dummy downloaded raw range file
        dummy_raw = Path("backend/storage/uploads") / f"raw_range_{clip_id}.mp4"
        dummy_raw.parent.mkdir(parents=True, exist_ok=True)
        dummy_raw.write_bytes(b"dummy_video_bytes")

        target_file = Path("backend/storage/uploads") / f"clip_src_{clip_id}.mp4"

        # Simulate ffmpeg creating the final trimmed output
        def side_effect(cmd, **kwargs):
            target_file.write_bytes(b"trimmed_clip_bytes")
            return MagicMock(returncode=0)

        mock_run.side_effect = side_effect

        try:
            res_path = IngestionService.download_clip_section(
                url=url,
                start_sec=start_sec,
                end_sec=end_sec,
                clip_id=clip_id,
            )

            assert Path(res_path).exists()
            assert mock_run.called

            # Check that ffmpeg was called with relative trim:
            # start_sec (120) - pad_start (119) = 1.0s offset, duration = 31.0s
            ffmpeg_cmd = mock_run.call_args[0][0]
            assert "-ss" in ffmpeg_cmd
            ss_idx = ffmpeg_cmd.index("-ss")
            assert ffmpeg_cmd[ss_idx + 1] == "1.000"

            assert "-t" in ffmpeg_cmd
            t_idx = ffmpeg_cmd.index("-t")
            assert ffmpeg_cmd[t_idx + 1] == "31.000"

        finally:
            if dummy_raw.exists():
                dummy_raw.unlink()
            if target_file.exists():
                target_file.unlink()


def test_transcribe_long_media_audio_time_offset():
    """Verify that time_offset_sec shifts all speech cues accurately to global timeline coordinates."""
    mock_cues = [
        {"start_sec": 10.0, "end_sec": 14.5, "text": "First sentence of hour two."},
        {"start_sec": 20.0, "end_sec": 25.0, "text": "Second sentence of hour two."},
    ]

    with patch.object(IngestionService, "get_video_duration", return_value=1200.0), \
         patch.object(IngestionService, "transcribe_media_audio", return_value=mock_cues):
        
        offset = 3600.0  # Hour 2 starts at 3600s
        cues = IngestionService.transcribe_long_media_audio(
            audio_filepath="dummy_hour_2.m4a",
            chunk_duration_sec=1800,
            time_offset_sec=offset,
        )

        assert len(cues) == 2
        assert cues[0]["start_sec"] == 3610.0
        assert cues[0]["end_sec"] == 3614.5
        assert cues[1]["start_sec"] == 3620.0
        assert cues[1]["end_sec"] == 3625.0


@pytest.mark.anyio
async def test_progressive_batch_endpoint_flow():
    """Verify progressive batch endpoint partitions cues and produces candidate batches with total_batches tracking."""
    from backend.app.api.shorts_mvp_api import progressive_batch, ProgressiveBatchRequest, ingested_videos

    video_id = "test_vid_progressive"
    ingested_videos[video_id] = {
        "video_id": video_id,
        "title": "24-Hour Charity Marathon",
        "duration_sec": 86400.0,  # 24 hours
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "filepath": "",
        "is_targeted_ranges": True,
        "transcript_cues": [
            # Hour 1 cues
            {"start_sec": 120.0, "end_sec": 151.0, "text": "Welcome to the start of the 24 hour stream."},
            {"start_sec": 200.0, "end_sec": 231.0, "text": "We are raising money for a great cause."},
            # Hour 2 cues
            {"start_sec": 3700.0, "end_sec": 3731.0, "text": "Entering hour two now, thank you for donations."},
        ],
    }

    mock_discovered_batch0 = [
        {
            "clip_id": "clip_b0_1",
            "start_sec": 120.0,
            "end_sec": 151.0,
            "duration_sec": 31.0,
            "spoken_text": "Welcome to the start of the 24 hour stream.",
            "virality_score": 85,
        }
    ]

    mock_discovered_batch1 = [
        {
            "clip_id": "clip_b1_1",
            "start_sec": 3700.0,
            "end_sec": 3731.0,
            "duration_sec": 31.0,
            "spoken_text": "Entering hour two now, thank you for donations.",
            "virality_score": 92,
        }
    ]

    # Batch 0 (Hour 1: 0 - 3600s)
    req0 = ProgressiveBatchRequest(
        video_id=video_id,
        batch_index=0,
        batch_duration_sec=3600.0,
    )
    with patch("backend.app.api.shorts_mvp_api.SmartClipSelector.discover_clips", return_value=mock_discovered_batch0), \
         patch("backend.app.api.shorts_mvp_api.IngestionService.download_clip_section", return_value="dummy_clip.mp4"), \
         patch("backend.app.api.shorts_mvp_api.face_reframer.track_clip_faces", return_value=None):
        res0 = await progressive_batch(req0)

    assert res0["video_id"] == video_id
    assert res0["batch_index"] == 0
    assert res0["total_batches"] == 24
    assert res0["is_last_batch"] is False
    assert len(res0["new_clips"]) == 1
    assert res0["new_clips"][0]["clip_id"] == "clip_b0_1"

    # Batch 1 (Hour 2: 3600 - 7200s)
    req1 = ProgressiveBatchRequest(
        video_id=video_id,
        batch_index=1,
        batch_duration_sec=3600.0,
    )
    with patch("backend.app.api.shorts_mvp_api.SmartClipSelector.discover_clips", return_value=mock_discovered_batch1), \
         patch("backend.app.api.shorts_mvp_api.IngestionService.download_clip_section", return_value="dummy_clip.mp4"), \
         patch("backend.app.api.shorts_mvp_api.face_reframer.track_clip_faces", return_value=None):
        res1 = await progressive_batch(req1)

    assert res1["batch_index"] == 1
    assert res1["total_batches"] == 24
    assert res1["is_last_batch"] is False
    assert len(res1["new_clips"]) == 1
    assert res1["new_clips"][0]["clip_id"] == "clip_b1_1"
    assert res1["new_clips"][0]["start_sec"] >= 3600.0

