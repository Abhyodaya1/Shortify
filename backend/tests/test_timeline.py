"""Unit tests for Universal Timeline and Serializers."""

import pytest
from uuid import uuid4
from backend.app.models.timeline import Timeline, Track, Clip, TrackType, ClipTransform
from backend.app.serializers.remotion_serializer import RemotionSerializer
from backend.app.serializers.fcpxml_serializer import FCPXMLSerializer


def test_timeline_creation_and_durations():
    timeline = Timeline(title="Test Multicam Cut", width=1920, height=1080, fps=30)
    video_track = timeline.add_track(name="Camera A - Wide", track_type=TrackType.VIDEO)
    audio_track = timeline.add_track(name="Master Audio", track_type=TrackType.AUDIO)

    clip1 = Clip(
        asset_id="wide_cam.mp4",
        start_time_ms=0,
        duration_ms=5000,
        source_in_ms=1000,
        source_out_ms=6000,
    )
    clip2 = Clip(
        asset_id="close_up.mp4",
        start_time_ms=5000,
        duration_ms=4000,
        source_in_ms=0,
        source_out_ms=4000,
    )
    timeline.add_clip(video_track.track_id, clip1)
    timeline.add_clip(video_track.track_id, clip2)

    audio_clip = Clip(
        asset_id="voice_stem.wav",
        start_time_ms=0,
        duration_ms=9000,
        volume=1.0,
    )
    timeline.add_clip(audio_track.track_id, audio_clip)

    assert timeline.duration_ms == 9000
    assert timeline.total_frames == 270  # (9000 / 1000) * 30
    assert timeline.aspect_ratio == "16:9"


def test_clip_collision_detection_raises_error():
    timeline = Timeline(fps=30)
    track = timeline.add_track(name="Colliding Track", track_type=TrackType.VIDEO)

    clip1 = Clip(start_time_ms=0, duration_ms=5000)
    # Clip 2 starts at 3000ms while clip 1 ends at 5000ms
    clip2 = Clip(start_time_ms=3000, duration_ms=4000)

    timeline.add_clip(track.track_id, clip1)
    with pytest.raises(ValueError, match="Clip collision on track"):
        timeline.add_clip(track.track_id, clip2)


def test_clip_invalid_source_boundaries_raises_error():
    with pytest.raises(ValueError, match="source_out_ms"):
        Clip(
            start_time_ms=0,
            duration_ms=2000,
            source_in_ms=5000,
            source_out_ms=4000,  # Invalid: out <= in
        )


def test_remotion_serializer_output():
    timeline = Timeline(title="Remotion Export Test", width=1080, height=1920, fps=30)
    video_track = timeline.add_track(name="Vertical Video", track_type=TrackType.VIDEO)
    caption_track = timeline.add_track(name="Captions", track_type=TrackType.CAPTION)

    clip = Clip(asset_id="talksport_speaker.mp4", start_time_ms=0, duration_ms=3000)
    caption = Clip(
        text_content="Autonomous Video Agent in Motion",
        start_time_ms=1000,
        duration_ms=2000,
        style_props={"color": "#FFCC00", "font_size": "56px"},
    )

    timeline.add_clip(video_track.track_id, clip)
    timeline.add_clip(caption_track.track_id, caption)

    tsx = RemotionSerializer.serialize_to_tsx(timeline)

    assert "import { Composition, Sequence, Video, Audio, staticFile, AbsoluteFill } from 'remotion';" in tsx
    assert "<Composition" in tsx
    assert 'width={1080}' in tsx
    assert 'height={1920}' in tsx
    assert 'fps={30}' in tsx
    assert "Autonomous Video Agent in Motion" in tsx
    assert "#FFCC00" in tsx


def test_fcpxml_serializer_output():
    timeline = Timeline(title="FCPXML Export Test", width=1920, height=1080, fps=30)
    video_track = timeline.add_track(name="Main Track", track_type=TrackType.VIDEO)

    clip = Clip(
        asset_id="founder_clip.mp4",
        start_time_ms=0,
        duration_ms=6000,
        source_in_ms=1000,
        source_out_ms=7000,
    )
    timeline.add_clip(video_track.track_id, clip)

    xml_content = FCPXMLSerializer.serialize_to_fcpxml(timeline)

    assert '<?xml version="1.0" ?>' in xml_content
    assert '<fcpxml version="1.9">' in xml_content
    assert '<sequence' in xml_content
    assert 'founder_clip.mp4' in xml_content
    assert '<asset-clip' in xml_content

