"""Remotion React (.tsx) compilation serializer."""

from __future__ import annotations
import json
from ..models.timeline import Timeline, TrackType, Clip


class RemotionSerializer:
    """Serializes an internal Timeline model into a functional Remotion React (.tsx) composition."""

    @classmethod
    def serialize_to_tsx(cls, timeline: Timeline, component_name: str = "VideoComposition") -> str:
        fps = timeline.fps
        duration_in_frames = max(1, timeline.total_frames)
        width = timeline.width
        height = timeline.height

        lines = [
            "// Auto-generated Remotion Composition by Video Agent Engine",
            "import React from 'react';",
            "import { Composition, Sequence, Video, Audio, staticFile, AbsoluteFill } from 'remotion';",
            "",
            f"export const {component_name}: React.FC = () => {{",
            "  return (",
            "    <AbsoluteFill style={{ backgroundColor: '#000000' }}>",
        ]

        # Order tracks by z-order
        sorted_tracks = sorted(timeline.tracks, key=lambda t: t.order)

        for track in sorted_tracks:
            lines.append(f"      {cls._generate_track_comment(track)}")
            for clip in track.clips:
                from_frame = int((clip.start_time_ms / 1000.0) * fps)
                duration_frames = max(1, int((clip.duration_ms / 1000.0) * fps))

                lines.append(f"      <Sequence from={{{from_frame}}} durationInFrames={{{duration_frames}}}>")
                lines.append(cls._generate_clip_element(clip, track.track_type, indent="        "))
                lines.append("      </Sequence>")

        lines.extend([
            "    </AbsoluteFill>",
            "  );",
            "};",
            "",
            f"export const RemotionRoot: React.FC = () => {{",
            "  return (",
            f"    <Composition",
            f"      id=\"{component_name}\"",
            f"      component={{{component_name}}}",
            f"      durationInFrames={{{duration_in_frames}}}",
            f"      fps={{{fps}}}",
            f"      width={{{width}}}",
            f"      height={{{height}}}",
            "    />",
            "  );",
            "};",
        ])

        return "\n".join(lines)

    @classmethod
    def _generate_track_comment(cls, track) -> str:
        return f"{{\n      /* Track: {track.name} ({track.track_type.value}) - Layer: {track.order} */\n      }}"

    @classmethod
    def _generate_clip_element(cls, clip: Clip, track_type: TrackType, indent: str = "        ") -> str:
        transform = clip.transform
        style = {
            "transform": f"translate({transform.x}px, {transform.y}px) rotate({transform.rotation}deg) scale({transform.scale_x}, {transform.scale_y})",
            "opacity": transform.opacity,
        }

        if track_type == TrackType.VIDEO:
            src = f"staticFile('{clip.asset_id}')" if clip.asset_id else "''"
            return (
                f"{indent}<Video\n"
                f"{indent}  src={{{src}}}\n"
                f"{indent}  volume={{{clip.volume}}}\n"
                f"{indent}  playbackRate={{{clip.playback_rate}}}\n"
                f"{indent}  style={{{json.dumps(style)}}}\n"
                f"{indent}/>"
            )
        elif track_type == TrackType.AUDIO:
            src = f"staticFile('{clip.asset_id}')" if clip.asset_id else "''"
            return (
                f"{indent}<Audio\n"
                f"{indent}  src={{{src}}}\n"
                f"{indent}  volume={{{clip.volume}}}\n"
                f"{indent}/>"
            )
        elif track_type in (TrackType.CAPTION, TrackType.GRAPHICS, TrackType.OVERLAY):
            custom_style = {
                **style,
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center",
                "color": clip.style_props.get("color", "#FFFFFF"),
                "fontSize": clip.style_props.get("font_size", "48px"),
                "fontWeight": clip.style_props.get("font_weight", "bold"),
                "fontFamily": clip.style_props.get("font_family", "sans-serif"),
                **clip.style_props.get("extra_style", {}),
            }
            escaped_text = (clip.text_content or "").replace('"', '&quot;')
            return (
                f"{indent}<AbsoluteFill style={{{json.dumps(custom_style)}}}>\n"
                f"{indent}  <span>{escaped_text}</span>\n"
                f"{indent}</AbsoluteFill>"
            )
        else:
            return f"{indent}<div style={{{json.dumps(style)}}} />"

