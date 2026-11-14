"""FCPXML / Premiere Pro XML serialization."""

from __future__ import annotations
import xml.etree.ElementTree as ET
from xml.dom import minidom
from ..models.timeline import Timeline, TrackType


class FCPXMLSerializer:
    """Serializes an internal Timeline model into standard FCPXML format compatible with Premiere Pro and DaVinci Resolve."""

    @classmethod
    def serialize_to_fcpxml(cls, timeline: Timeline) -> str:
        fps = timeline.fps
        # Standard timebase representation: 1/fps s
        frame_duration = f"100/{fps * 100}s"
        total_duration_s = timeline.duration_ms / 1000.0
        total_duration_str = f"{int(total_duration_s * fps)}/{fps}s"

        fcpxml = ET.Element("fcpxml", version="1.9")
        
        # Resources
        resources = ET.SubElement(fcpxml, "resources")
        format_elem = ET.SubElement(
            resources,
            "format",
            id="r1",
            name=f"FFVideoFormat{timeline.height}p{fps}",
            frameDuration=frame_duration,
            width=str(timeline.width),
            height=str(timeline.height),
        )

        # Assets in resources
        asset_map = {}
        res_idx = 2
        for track in timeline.tracks:
            for clip in track.clips:
                if clip.asset_id and clip.asset_id not in asset_map:
                    asset_id_str = f"r{res_idx}"
                    res_idx += 1
                    asset_map[clip.asset_id] = asset_id_str
                    ET.SubElement(
                        resources,
                        "asset",
                        id=asset_id_str,
                        name=clip.asset_id,
                        src=f"file://localhost/{clip.asset_id}",
                        format="r1",
                    )

        # Library & Event
        library = ET.SubElement(fcpxml, "library")
        event = ET.SubElement(library, "event", name="Video Agent Export")
        project = ET.SubElement(event, "project", name=timeline.title)
        sequence = ET.SubElement(
            project,
            "sequence",
            format="r1",
            duration=total_duration_str,
            tcStart="0s",
            tcFormat="NDF",
        )
        spine = ET.SubElement(sequence, "spine")

        # Organize clips into spine
        # Group by video track vs audio track
        video_tracks = [t for t in timeline.tracks if t.track_type == TrackType.VIDEO]
        if video_tracks:
            # Primary story line from first video track
            for clip in video_tracks[0].clips:
                clip_start_s = clip.start_time_ms / 1000.0
                clip_dur_s = clip.duration_ms / 1000.0
                source_in_s = clip.source_in_ms / 1000.0

                ref_id = asset_map.get(clip.asset_id, "r1")
                clip_elem = ET.SubElement(
                    spine,
                    "asset-clip",
                    ref=ref_id,
                    name=clip.asset_id or "Clip",
                    offset=f"{int(clip_start_s * fps)}/{fps}s",
                    duration=f"{int(clip_dur_s * fps)}/{fps}s",
                    start=f"{int(source_in_s * fps)}/{fps}s",
                )

        # Format XML with indentation
        xml_str = ET.tostring(fcpxml, encoding="utf-8")
        parsed = minidom.parseString(xml_str)
        return parsed.toprettyxml(indent="  ")

