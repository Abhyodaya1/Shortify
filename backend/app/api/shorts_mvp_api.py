"""FastAPI endpoints for the Personal AI YouTube Shorts Generator MVP.
Conforms to 03_IMPLEMENTATION_SPEC.md.
"""

from __future__ import annotations
import os
import re
import math
from pathlib import Path
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query, status
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from ..services.video_ingestion import IngestionService
from ..services.url_security_validator import SSRFSecurityError, URLSecurityValidator
from ..services.face_tracker import FaceTrackingReframer
from ..services.clip_selector import SmartClipSelector
from ..services.shorts_renderer import ShortsRenderer
from ..services.quality_assurance import QualityAssuranceEngine
from ..services.timeline_compositor import MasterTimelineCompositor, ContentPackagerService
from ..services.youtube_intelligence_service import YouTubeIntelligenceService
from ..storage.profile_store import ProfileStore
from ..storage.dataset_store import DatasetStore, ClipFeedbackSubmission
from ..storage.session_store import SessionStore, SessionVideosProxy, SessionClipsProxy

router = APIRouter(prefix="/api/v1/shorts", tags=["Personal Shorts MVP"])

# SQLite-backed persistent session storage for active videos and clips (REL-02)
ingested_videos = SessionVideosProxy()
discovered_clips = SessionClipsProxy()
face_reframer = FaceTrackingReframer()


class IngestUrlRequest(BaseModel):
    url: str = Field(..., description="YouTube video URL")


class DiscoverClipsRequest(BaseModel):
    video_id: str = Field(..., description="ID of ingested video")
    duration_mode: str = Field(default="31s", description="'31s' or '45s'")
    layout_mode: str = Field(default="split_screen", description="'split_screen', 'split_screen_comment', 'tweet_card', 'full_9_16', 'fit_ambient_blur'")
    card_type: Optional[str] = Field(default=None, description="Card archetype: 'none', 'reddit_card', 'tweet_card', 'instagram_card', 'youtube_comment'")
    background_id: Optional[str] = Field(default="minecraft_parkour", description="Background video ID")
    video_scale_percent: int = Field(default=48, description="Main video height percent (30-80)")
    auto_hook: bool = Field(default=False, description="Enable opening AI voiceover hook by default")
    social_author: Optional[str] = Field(default="Peak Heist Clips", description="Social author name")
    social_handle: Optional[str] = Field(default="@peakheistclips", description="Social handle")
    social_badge: Optional[str] = Field(default="verified", description="Verified or currency badge")
    social_text: Optional[str] = Field(default=None, description="Custom social / comment card text")
    card_vertical_position: Optional[int] = Field(default=20, description="Card vertical position percent (10-85)")
    card_width_percent: Optional[int] = Field(default=90, description="Card width scale percent (70-100)")
    subtitle_vertical_position: Optional[int] = Field(default=75, description="Subtitle vertical position percent (10-90)")
    enable_title_frame: bool = Field(default=False, description="Enable opening title frame")
    title_frame_mode: str = Field(default="blurred_footage", description="blank_bg or blurred_footage")
    title_frame_duration: float = Field(default=2.5, description="Title frame duration in seconds")
    subtitle_preset: Optional[str] = Field(default="bold_impact", description="Subtitle preset ID")
    custom_active_color: Optional[str] = Field(default=None, description="Active word color hex e.g. #FFE600")
    custom_primary_color: Optional[str] = Field(default=None, description="Non-highlighted text color hex e.g. #FFFFFF")
    custom_font_name: Optional[str] = Field(default=None, description="Font family override e.g. Arial Black, Impact, Space Grotesk")
    custom_animation: Optional[str] = Field(default=None, description="Animation type: word_pop, glow_pulse, fade_in, slide_up, karaoke")
    custom_all_caps: Optional[bool] = Field(default=None, description="Whether to uppercase text")
    custom_outline_width: Optional[float] = Field(default=None, description="Custom stroke thickness")
    tts_voice: Optional[str] = Field(default=None, description="TTS voice override")


class ProgressiveBatchRequest(BaseModel):
    video_id: str = Field(..., description="ID of ingested video")
    batch_index: int = Field(default=0, ge=0, description="0-indexed 1-hour batch index (e.g. 0=0-1h, 1=1-2h)")
    batch_duration_sec: float = Field(default=3600.0, ge=60.0, description="Batch window duration in seconds")
    duration_mode: str = Field(default="31s", description="'31s' or '45s'")
    layout_mode: str = Field(default="split_screen", description="Layout mode")
    card_type: Optional[str] = Field(default=None, description="Card archetype")
    background_id: Optional[str] = Field(default="minecraft_parkour", description="Background video ID")
    video_scale_percent: int = Field(default=48, description="Main video height percent")
    auto_hook: bool = Field(default=False, description="Enable AI hook voiceover")
    social_author: Optional[str] = Field(default="Peak Heist Clips", description="Social author name")
    social_handle: Optional[str] = Field(default="@peakheistclips", description="Social handle")
    social_badge: Optional[str] = Field(default="verified", description="Verified badge")
    social_text: Optional[str] = Field(default=None, description="Custom social text")
    card_vertical_position: Optional[int] = Field(default=20, description="Card vertical position")
    card_width_percent: Optional[int] = Field(default=90, description="Card width scale")
    subtitle_vertical_position: Optional[int] = Field(default=75, description="Subtitle vertical position")
    subtitle_preset: str = Field(default="mrbeast", description="Subtitle preset ID")
    custom_active_color: Optional[str] = Field(default=None, description="Active word hex")
    custom_primary_color: Optional[str] = Field(default=None, description="Primary word hex")
    custom_font_name: Optional[str] = Field(default=None, description="Font family override")
    custom_animation: Optional[str] = Field(default=None, description="Animation type")
    custom_all_caps: Optional[bool] = Field(default=None, description="Whether to uppercase text")
    custom_outline_width: Optional[float] = Field(default=None, description="Custom stroke thickness")
    tts_voice: Optional[str] = Field(default=None, description="TTS voice override")


class RenderClipRequest(BaseModel):
    clip_id: str = Field(..., description="ID of selected clip candidate")
    layout_mode: str = Field(default="split_screen", description="'split_screen', 'split_screen_comment', 'tweet_card', 'full_9_16', 'fit_ambient_blur'")
    card_type: Optional[str] = Field(default=None, description="Card archetype: 'none', 'reddit_card', 'tweet_card', 'instagram_card', 'youtube_comment'")
    background_id: Optional[str] = Field(default="minecraft_parkour", description="Background video ID")
    video_scale_percent: int = Field(default=48, description="Main video height percent (30-80)")
    enable_opening_hook: bool = Field(default=False, description="Enable AI hook voiceover")
    opening_hook_text: Optional[str] = Field(default=None, description="Custom or approved hook text")
    enable_ending_hook: bool = Field(default=False, description="Enable ending hook voiceover")
    ending_hook_text: Optional[str] = Field(default=None, description="Custom ending hook text")
    headline_text: Optional[str] = Field(default=None, description="Top visual heading")
    tts_voice: str = Field(default="en-US-ChristopherNeural", description="Voice ID")
    subtitle_preset: str = Field(default="mrbeast", description="'mrbeast', 'clean_minimal', 'neon_punch', 'tiktok_yellow', 'red_alert'")
    custom_active_color: Optional[str] = Field(default=None, description="Active word hex e.g. #FFE600 or &H0000D7FF&")
    custom_primary_color: Optional[str] = Field(default=None, description="Non-highlighted word hex e.g. #FFFFFF")
    custom_font_name: Optional[str] = Field(default=None, description="Font family override e.g. Arial Black, Montserrat")
    custom_animation: Optional[str] = Field(default=None, description="Animation type: word_pop, glow_pulse, fade_in, slide_up, karaoke")
    custom_all_caps: Optional[bool] = Field(default=None, description="Force uppercase text")
    custom_outline_width: Optional[float] = Field(default=None, description="Custom stroke thickness")
    social_author: Optional[str] = Field(default="Peak Heist Clips", description="Social author name")
    social_handle: Optional[str] = Field(default="@peakheistclips", description="Social handle")
    social_badge: Optional[str] = Field(default="verified", description="Verified or currency badge")
    social_text: Optional[str] = Field(default=None, description="Custom social / comment card text")
    card_vertical_position: Optional[int] = Field(default=20, description="Card vertical position percent (10-85)")
    card_width_percent: Optional[int] = Field(default=90, description="Card width scale percent (70-100)")
    subtitle_vertical_position: Optional[int] = Field(default=75, description="Subtitle vertical position percent (10-90)")
    enable_title_frame: bool = Field(default=False, description="Enable opening title frame")
    title_frame_mode: str = Field(default="blurred_footage", description="blank_bg or blurred_footage")
    title_frame_duration: float = Field(default=2.5, description="Title frame duration in seconds")


class BatchRenderRequest(BaseModel):
    clip_ids: List[str] = Field(..., description="List of clip candidate IDs to render")
    layout_mode: str = Field(default="split_screen", description="Layout mode")
    background_id: Optional[str] = Field(default="minecraft_parkour", description="Background ID")
    video_scale_percent: int = Field(default=48, description="Split ratio percent")
    subtitle_preset: str = Field(default="mrbeast", description="Subtitle preset")
    custom_font_name: Optional[str] = Field(default=None, description="Font name")
    custom_active_color: Optional[str] = Field(default=None, description="Active word color")
    enable_opening_hook: bool = Field(default=False, description="Opening AI voiceover hook")
    tts_voice: str = Field(default="en-US-ChristopherNeural", description="Voice ID")


class FastReRenderRequest(BaseModel):
    clip_id: str = Field(..., description="ID of selected clip candidate")
    subtitle_preset: str = Field(default="mrbeast", description="'mrbeast', 'clean_minimal', 'neon_punch', 'tiktok_yellow', 'red_alert'")
    custom_active_color: Optional[str] = Field(default=None, description="Active word hex")
    custom_font_name: Optional[str] = Field(default=None, description="Font family override")
    headline_text: Optional[str] = Field(default=None, description="Updated headline")


@router.post("/ingest-url", summary="Download YouTube video & extract transcript")
def ingest_youtube_url(payload: IngestUrlRequest):
    """Downloads YouTube video, captures title, duration, and extracts transcript."""
    try:
        video_data = IngestionService.ingest_youtube_url(payload.url)
        vid_id = video_data["video_id"]
        ingested_videos[vid_id] = video_data
        duration = float(video_data.get("duration_sec", 0.0))
        is_long = video_data.get("is_targeted_ranges", False)
        total_batches = max(1, math.ceil(duration / 3600.0)) if is_long else 1
        return {
            "video_id": vid_id,
            "title": video_data["title"],
            "duration_sec": video_data["duration_sec"],
            "thumbnail": video_data["thumbnail"],
            "width": video_data["width"],
            "height": video_data["height"],
            "cue_count": len(video_data["transcript_cues"]),
            "is_targeted_ranges": is_long,
            "total_batches": total_batches,
        }
    except SSRFSecurityError as e:
        raise HTTPException(status_code=403, detail=f"Security violation: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid URL: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upload-file", summary="Upload local video file")
async def upload_local_file(file: UploadFile = File(...)):
    """Accepts a local MP4 or MOV video file for Shorts processing."""
    raw_name = Path(file.filename or "video.mp4").name
    clean_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', raw_name)
    temp_dir = Path("backend/storage/uploads").resolve()
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = (temp_dir / clean_name).resolve()
    if not temp_path.is_relative_to(temp_dir):
        raise HTTPException(status_code=400, detail="Invalid upload filename")

    with open(temp_path, "wb") as f:
        content = await file.read()
        f.write(content)

    video_data = IngestionService.ingest_local_file(str(temp_path), clean_name)
    vid_id = video_data["video_id"]
    ingested_videos[vid_id] = video_data
    duration = float(video_data.get("duration_sec", 0.0))
    total_batches = max(1, math.ceil(duration / 3600.0)) if duration > 3600.0 else 1

    return {
        "video_id": vid_id,
        "title": video_data["title"],
        "duration_sec": video_data["duration_sec"],
        "thumbnail": "",
        "width": video_data["width"],
        "height": video_data["height"],
        "cue_count": len(video_data["transcript_cues"]),
        "is_targeted_ranges": duration > 900.0,
        "total_batches": total_batches,
    }


def _enrich_and_store_clip(clip: Dict[str, Any], video: Dict[str, Any], payload: Any) -> Dict[str, Any]:
    total_vid_dur = float(video.get("duration_sec", 99999.0))
    filepath = video.get("filepath", "")

    # OpenShorts Phase 1 Audio Attack & Decay Buffering:
    # Pre-roll 80ms to preserve attack transients, post-roll 150ms for natural vocal decay
    raw_start = float(clip["start_sec"])
    raw_end = float(clip["end_sec"])
    buffered_start = max(0.0, round(raw_start - 0.08, 2))
    buffered_end = min(total_vid_dur, round(raw_end + 0.15, 2))
    clip["start_sec"] = buffered_start
    clip["end_sec"] = buffered_end
    clip["duration_sec"] = round(buffered_end - buffered_start, 2)

    crop_info = None
    clip_source_path = filepath
    track_start = clip["start_sec"]
    track_end = clip["end_sec"]

    # Progressive / Targeted Range Ingestion Architecture:
    # For long videos, do NOT eagerly download video ranges during transcript discovery.
    # Discovery evaluates text in seconds. Targeted Range Download is executed on-demand
    # when rendering the selected 45s clips in render_clip().
    if video.get("is_targeted_ranges"):
        clip_source_path = ""
    elif filepath and os.path.exists(filepath):
        clip_source_path = filepath
    else:
        clip_source_path = ""

    if clip_source_path and os.path.exists(clip_source_path):
        crop_info = face_reframer.track_clip_faces(
            video_filepath=clip_source_path,
            start_sec=track_start,
            end_sec=track_end,
            sample_fps=3.0,
        )
    clip["crop_data"] = crop_info
    clip["parent_video_id"] = payload.video_id
    clip["batch_index"] = getattr(payload, "batch_index", 0)
    clip["layout_mode"] = payload.layout_mode
    clip["card_type"] = payload.card_type
    clip["background_id"] = payload.background_id
    clip["video_scale_percent"] = getattr(payload, "video_scale_percent", 48)
    clip["social_author"] = payload.social_author
    clip["social_handle"] = payload.social_handle
    clip["social_badge"] = payload.social_badge
    clip["social_text"] = payload.social_text
    clip["subtitle_preset"] = payload.subtitle_preset
    clip["custom_active_color"] = payload.custom_active_color
    clip["custom_primary_color"] = payload.custom_primary_color
    clip["custom_font_name"] = payload.custom_font_name
    clip["custom_animation"] = payload.custom_animation
    clip["custom_all_caps"] = payload.custom_all_caps
    clip["card_vertical_position"] = payload.card_vertical_position
    clip["card_width_percent"] = payload.card_width_percent
    clip["subtitle_vertical_position"] = payload.subtitle_vertical_position
    discovered_clips[clip["clip_id"]] = clip
    return clip


@router.post("/discover-clips", summary="Analyze video, run face tracking, and discover viral clips")
async def discover_clips(payload: DiscoverClipsRequest):
    """Uses Gemini AI + 21 Hook Formulas + Face Tracking to select 31s or 45s Shorts candidates."""
    if payload.video_id not in ingested_videos:
        raise HTTPException(status_code=404, detail="Video not found. Please ingest first.")

    video = ingested_videos[payload.video_id]
    cues = list(video["transcript_cues"])
    title = video["title"]
    total_vid_dur = float(video.get("duration_sec", 99999.0))

    # For long videos (>1h), limit the initial discover pass to the first hour (3600s)
    # so the user receives their first batch of clips immediately (e.g. in ~30s)
    if video.get("is_targeted_ranges") and total_vid_dur > 3600.0:
        cues = [c for c in cues if float(c.get("start_sec", 0)) <= 3600.0]

    # 1. Snapshot the active editorial profile for this generation job
    active_profile = ProfileStore.get_active_profile()

    # 2. AI Content & Clip Selection targeting requested duration mode
    raw_clips = await SmartClipSelector.discover_clips(
        cues=cues,
        video_title=title,
        duration_mode=payload.duration_mode,
        profile=active_profile,
    )

    # 3. Apply vocal attack/decay buffering (80ms/150ms) and compute Face Tracking for each clip
    clips = []
    for raw_clip in raw_clips:
        enriched = _enrich_and_store_clip(raw_clip, video, payload)
        clips.append(enriched)

    batch_msg = clips[0].get("batch_message") if clips else "No Shorts candidates found."
    sel_mode = clips[0].get("selection_mode", "empty") if clips else "empty"
    is_fb = clips[0].get("is_fallback", False) if clips else False
    qual_cnt = clips[0].get("qualifying_count", 0) if clips else 0
    total_batches = max(1, math.ceil(total_vid_dur / 3600.0)) if video.get("is_targeted_ranges") else 1

    return {
        "video_id": payload.video_id,
        "duration_mode": payload.duration_mode,
        "total_clips_found": len(clips),
        "batch_message": batch_msg,
        "selection_mode": sel_mode,
        "is_fallback": is_fb,
        "qualifying_count": qual_cnt,
        "profile_snapshot": active_profile.snapshot(),
        "clips": clips,
        "total_batches": total_batches,
        "batch_index": 0,
    }


@router.post("/progressive-batch", summary="Progressive 1-hour batch analysis for long videos")
async def progressive_batch(payload: ProgressiveBatchRequest):
    """Processes a specific 1-hour slice of a long video in the background.
    Downloads targeted audio, transcribes with Whisper if missing, discovers clips,
    and returns newly extracted candidate clips to progressively append to the UI feed.
    """
    if payload.video_id not in ingested_videos:
        raise HTTPException(status_code=404, detail="Video not found. Please ingest first.")

    video = ingested_videos[payload.video_id]
    total_dur = float(video.get("duration_sec", 0.0))
    total_batches = max(1, math.ceil(total_dur / payload.batch_duration_sec)) if total_dur > 0 else 1

    start_sec = payload.batch_index * payload.batch_duration_sec
    end_sec = min(total_dur, (payload.batch_index + 1) * payload.batch_duration_sec)

    if start_sec >= total_dur:
        return {
            "video_id": payload.video_id,
            "batch_index": payload.batch_index,
            "batch_start_sec": start_sec,
            "batch_end_sec": end_sec,
            "total_batches": total_batches,
            "is_last_batch": True,
            "new_clips": [],
            "total_clips_count": len([c for c in discovered_clips.values() if c.get("parent_video_id") == payload.video_id]),
        }

    # Check if cues for this window already exist
    all_cues = list(video.get("transcript_cues", []))
    batch_cues = [c for c in all_cues if start_sec <= float(c.get("start_sec", 0)) < end_sec]

    # If no cues exist for this window and we have a URL, download targeted audio slice
    if not batch_cues and video.get("url"):
        temp_audio_out = str(STORAGE_UPLOADS / f"batch_audio_{payload.video_id}_{payload.batch_index}")
        try:
            audio_path = IngestionService.download_audio_section(
                url=video["url"],
                start_sec=start_sec,
                end_sec=end_sec,
                output_path=temp_audio_out,
            )
            raw_cues = IngestionService.transcribe_long_media_audio(
                audio_filepath=audio_path,
                time_offset_sec=start_sec,
            )
            if raw_cues:
                all_cues.extend(raw_cues)
                video["transcript_cues"] = all_cues
                ingested_videos[payload.video_id] = video
                batch_cues = raw_cues
            try:
                Path(audio_path).unlink()
            except Exception:
                pass
        except Exception as e:
            import logging
            logging.getLogger("shorts_mvp").error(f"Progressive batch {payload.batch_index} audio error: {e}")

    if not batch_cues:
        is_last = (payload.batch_index + 1) >= total_batches
        return {
            "video_id": payload.video_id,
            "batch_index": payload.batch_index,
            "batch_start_sec": start_sec,
            "batch_end_sec": end_sec,
            "total_batches": total_batches,
            "is_last_batch": is_last,
            "new_clips": [],
            "total_clips_count": len([c for c in discovered_clips.values() if c.get("parent_video_id") == payload.video_id]),
        }

    active_profile = ProfileStore.get_active_profile()
    raw_clips = await SmartClipSelector.discover_clips(
        cues=batch_cues,
        video_title=video.get("title", "Source Video"),
        duration_mode=payload.duration_mode,
        profile=active_profile,
    )

    enriched_clips = []
    for raw_clip in raw_clips:
        enriched = _enrich_and_store_clip(raw_clip, video, payload)
        enriched_clips.append(enriched)

    is_last = (payload.batch_index + 1) >= total_batches
    all_video_clips = [c for c in discovered_clips.values() if c.get("parent_video_id") == payload.video_id]

    return {
        "video_id": payload.video_id,
        "batch_index": payload.batch_index,
        "batch_start_sec": start_sec,
        "batch_end_sec": end_sec,
        "total_batches": total_batches,
        "is_last_batch": is_last,
        "new_clips": enriched_clips,
        "total_clips_count": len(all_video_clips),
    }


def _get_bg_storage_dir() -> Path:
    candidates = [
        Path("backend/storage/backgrounds"),
        Path("storage/backgrounds"),
        Path(__file__).resolve().parent.parent.parent / "storage" / "backgrounds",
    ]
    for c in candidates:
        if c.exists():
            return c
    p = candidates[0]
    p.mkdir(parents=True, exist_ok=True)
    return p


@router.get("/backgrounds", summary="List available predefined background videos")
def list_backgrounds():
    """Lists available predefined and uploaded background videos."""
    import subprocess
    bg_dir = _get_bg_storage_dir()
    backgrounds = []
    for p in bg_dir.glob("*.mp4"):
        bid = p.stem
        thumb_path = bg_dir / f"{bid}.jpg"
        if not thumb_path.exists():
            try:
                subprocess.run(
                    ["ffmpeg", "-y", "-ss", "00:00:03", "-i", str(p.resolve()), "-vframes", "1", "-q:v", "2", str(thumb_path.resolve())],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=15,
                )
            except Exception:
                pass

        has_thumb = thumb_path.exists()
        backgrounds.append({
            "id": bid,
            "name": bid.replace("_", " ").title(),
            "filename": p.name,
            "thumbnail_url": f"http://localhost:8000/api/v1/shorts/backgrounds/{bid}/thumbnail" if has_thumb else "",
        })
    return {"backgrounds": backgrounds}


@router.get("/backgrounds/{bg_id:path}/thumbnail", summary="Get background video thumbnail")
def get_background_thumbnail(bg_id: str):
    import subprocess
    if "\0" in bg_id or "/" in bg_id or "\\" in bg_id or ".." in bg_id:
        raise HTTPException(status_code=400, detail="Invalid background ID")
    clean_bg_id = Path(bg_id).name
    bg_dir = _get_bg_storage_dir().resolve()
    thumb = (bg_dir / f"{clean_bg_id}.jpg").resolve()
    if not thumb.is_relative_to(bg_dir):
        raise HTTPException(status_code=400, detail="Path traversal attempt detected")
    if not thumb.exists():
        # Try extracting on the fly from the corresponding mp4
        vid = (bg_dir / f"{clean_bg_id}.mp4").resolve()
        if vid.exists() and vid.is_relative_to(bg_dir):
            try:
                subprocess.run(
                    ["ffmpeg", "-y", "-ss", "00:00:02", "-i", str(vid), "-vframes", "1", "-q:v", "2", str(thumb)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=15,
                )
            except Exception:
                pass
    if not thumb.exists() or not thumb.is_file():
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    return FileResponse(str(thumb), media_type="image/jpeg")


@router.post("/upload-background", summary="Upload a custom background video")
async def upload_background(file: UploadFile = File(...)):
    """Uploads an additional background video to the background library."""
    import re
    import subprocess
    bg_dir = Path("backend/storage/backgrounds").resolve()
    bg_dir.mkdir(parents=True, exist_ok=True)
    clean_stem = re.sub(r'[^a-zA-Z0-9_-]', '_', Path(file.filename or "bg.mp4").stem).lower()
    target_path = (bg_dir / f"{clean_stem}.mp4").resolve()
    if not target_path.is_relative_to(bg_dir):
        raise HTTPException(status_code=400, detail="Invalid background filename")

    with open(target_path, "wb") as f:
        content = await file.read()
        f.write(content)

    thumb_path = bg_dir / f"{clean_stem}.jpg"
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-ss", "00:00:02", "-i", str(target_path), "-vframes", "1", "-q:v", "2", str(thumb_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=15,
        )
    except Exception:
        pass

    return {
        "status": "success",
        "id": clean_stem,
        "name": clean_stem.replace("_", " ").title(),
        "filename": target_path.name,
        "thumbnail_url": f"http://localhost:8000/api/v1/shorts/backgrounds/{clean_stem}/thumbnail" if thumb_path.exists() else "",
    }


@router.post("/render-clip", summary="Render 9:16 vertical MP4 with face tracking, kinetic ASS & QA check")
async def render_clip(payload: RenderClipRequest):
    """Renders the selected clip into an MP4 file with smart reframing, kinetic typography, and deterministic QA."""
    if payload.clip_id not in discovered_clips:
        raise HTTPException(status_code=404, detail="Clip candidate not found.")

    clip = discovered_clips[payload.clip_id]
    parent_vid_id = clip["parent_video_id"]
    video = ingested_videos[parent_vid_id]

    output_filename = f"short_{payload.clip_id}.mp4"
    clip_render_dir = Path("backend/storage/renders") / f"clip_{payload.clip_id}"
    clip_render_dir.mkdir(parents=True, exist_ok=True)

    # Resolve background video
    bg_video_path = None
    if payload.background_id and payload.background_id != "none":
        candidate_bg = Path("backend/storage/backgrounds") / f"{payload.background_id}.mp4"
        if candidate_bg.exists():
            bg_video_path = str(candidate_bg.resolve())
        else:
            default_bg = Path("backend/storage/backgrounds/minecraft_parkour.mp4")
            if default_bg.exists():
                bg_video_path = str(default_bg.resolve())

    # Resolve source video file and start/end boundaries (supports targeted range clips)
    source_path = video.get("filepath", "")
    r_start = clip["start_sec"]
    r_end = clip["end_sec"]

    if clip.get("source_clip_path") and os.path.exists(clip["source_clip_path"]):
        source_path = clip["source_clip_path"]
        r_start = 0.0
        r_end = clip["duration_sec"]
    elif video.get("is_targeted_ranges") and video.get("url"):
        source_path = IngestionService.download_clip_section(
            url=video["url"],
            start_sec=clip["start_sec"],
            end_sec=clip["end_sec"],
            clip_id=payload.clip_id,
        )
        clip["source_clip_path"] = source_path
        r_start = 0.0
        r_end = clip["duration_sec"]

    # Shortify Master Renderer: Compute face tracking on 45s clip if not already computed
    crop_info = clip.get("crop_data")
    if not crop_info and source_path and os.path.exists(source_path):
        try:
            crop_info = face_reframer.track_clip_faces(
                video_filepath=source_path,
                start_sec=r_start,
                end_sec=r_end,
                sample_fps=3.0,
            )
            clip["crop_data"] = crop_info
        except Exception as fe:
            import logging
            logging.getLogger("shorts_mvp").warning(f"Face tracking fallback on render: {fe}")

    report = await MasterTimelineCompositor.process_and_render_clip(
        source_video_path=source_path,
        start_sec=r_start,
        end_sec=r_end,
        clip_id=payload.clip_id,
        output_dir=str(clip_render_dir),
        crop_data=crop_info,
        layout_mode=payload.layout_mode,
        card_type=payload.card_type or clip.get("card_type"),
        background_video_path=bg_video_path,
        video_scale_percent=payload.video_scale_percent,
        enable_opening_hook=payload.enable_opening_hook,
        opening_hook_text=payload.opening_hook_text or clip.get("opening_hook"),
        enable_ending_hook=payload.enable_ending_hook,
        ending_hook_text=payload.ending_hook_text,
        headline_text=payload.headline_text or clip.get("visual_headline") or clip.get("title"),
        tts_voice=payload.tts_voice,
        subtitle_preset=payload.subtitle_preset,
        custom_active_color=payload.custom_active_color,
        custom_primary_color=payload.custom_primary_color,
        custom_font_name=payload.custom_font_name,
        custom_animation=payload.custom_animation,
        custom_all_caps=payload.custom_all_caps,
        custom_outline_width=payload.custom_outline_width,
        social_author=payload.social_author,
        social_handle=payload.social_handle,
        social_badge=payload.social_badge,
        social_text=payload.social_text,
        card_vertical_position=payload.card_vertical_position,
        card_width_percent=payload.card_width_percent,
        subtitle_vertical_position=payload.subtitle_vertical_position,
        enable_title_frame=payload.enable_title_frame,
        title_frame_mode=payload.title_frame_mode,
        title_frame_duration=payload.title_frame_duration,
    )

    rendered_file = report["output_files"]["final_video"]
    public_preview_path = Path("backend/storage/renders") / output_filename
    if Path(rendered_file).exists() and public_preview_path.resolve() != Path(rendered_file).resolve():
        import shutil
        shutil.copy2(rendered_file, public_preview_path)

    packaging = report.get("packaging", {})
    recommended_titles = packaging.get("titles", [])
    best_title = clip.get("title", "")
    if recommended_titles:
        rec_idx = packaging.get("recommended_title_index", 0)
        if rec_idx < len(recommended_titles):
            best_title = recommended_titles[rec_idx].get("text", best_title)

    desc = packaging.get("description") or clip.get("description", "")
    hashtags = packaging.get("hashtags") or clip.get("hashtags", [])
    tags = packaging.get("tags") or clip.get("tags", [])

    clip["rendered_file"] = str(public_preview_path.resolve())
    clip["render_report"] = report
    clip["title"] = best_title
    clip["title_alternatives"] = recommended_titles
    clip["description"] = desc
    clip["hashtags"] = hashtags
    clip["tags"] = tags
    discovered_clips[payload.clip_id] = clip

    mtime = int(os.path.getmtime(public_preview_path)) if public_preview_path.exists() else 0

    return {
        "status": "success",
        "clip_id": payload.clip_id,
        "filename": output_filename,
        "preview_url": f"http://localhost:8000/api/v1/shorts/preview/{output_filename}?t={mtime}",
        "download_url": f"http://localhost:8000/api/v1/shorts/download/{output_filename}",
        "title": best_title,
        "title_alternatives": recommended_titles,
        "description": desc,
        "hashtags": hashtags,
        "tags": tags,
        "hook_verdict": clip.get("hook_verdict", "Strong hook grounded in content"),
        "engagement_score": clip.get("engagement_score", 90),
        "qa_result": {
            "passed": report.get("subtitles", {}).get("qa_status") == "pass",
            "qa_status": report.get("subtitles", {}).get("qa_status", "pass"),
            "issues": report.get("subtitles", {}).get("qa_issues", []),
            "total_duration_sec": report.get("total_duration_sec"),
            "resolution": "1080x1920",
        },
        "report": report,
    }


@router.post("/batch-render", summary="Batch render multiple selected clips")
async def batch_render_clips(payload: BatchRenderRequest):
    """Renders multiple clips sequentially, returning results and status (Feature 4)."""
    results = []
    for cid in payload.clip_ids:
        if cid not in discovered_clips:
            continue
        try:
            req = RenderClipRequest(
                clip_id=cid,
                layout_mode=payload.layout_mode,
                background_id=payload.background_id,
                video_scale_percent=payload.video_scale_percent,
                subtitle_preset=payload.subtitle_preset,
                custom_font_name=payload.custom_font_name,
                custom_active_color=payload.custom_active_color,
                enable_opening_hook=payload.enable_opening_hook,
                tts_voice=payload.tts_voice,
            )
            res = await render_clip(req)
            results.append({"clip_id": cid, "status": "success", "download_url": res["download_url"], "preview_url": res["preview_url"]})
        except Exception as e:
            results.append({"clip_id": cid, "status": "failed", "error": str(e)})
    return {"total": len(results), "rendered": [r for r in results if r["status"] == "success"], "results": results}


@router.get("/batch-download-zip", summary="Download all rendered clips in a ZIP bundle")
def download_all_zip():
    """Packages all rendered MP4 shorts into a single zip archive for 1-click batch download (Feature 4)."""
    import zipfile
    renders_dir = Path("backend/storage/renders")
    zip_path = renders_dir / "motion_shorts_bundle.zip"
    mp4s = list(renders_dir.glob("short_*.mp4"))
    if not mp4s:
        raise HTTPException(status_code=404, detail="No rendered shorts found yet.")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in mp4s:
            zf.write(f, arcname=f.name)

    return FileResponse(str(zip_path), media_type="application/zip", filename="motion_shorts_bundle.zip")


@router.post("/re-render-subtitles", summary="Fast 2-second subtitle re-styling without re-analyzing video")
def fast_re_render_subtitles(payload: FastReRenderRequest):
    clip_render_dir = Path("backend/storage/renders") / f"clip_{payload.clip_id}"
    if not clip_render_dir.exists():
        raise HTTPException(status_code=404, detail="Clip artifacts not found. Please render clip first.")

    res = MasterTimelineCompositor.re_render_subtitles_fast(
        clip_dir=str(clip_render_dir),
        subtitle_preset=payload.subtitle_preset,
        custom_active_color=payload.custom_active_color,
        custom_primary_color=payload.custom_primary_color,
        custom_font_name=payload.custom_font_name,
        custom_animation=payload.custom_animation,
        custom_all_caps=payload.custom_all_caps,
        custom_outline_width=payload.custom_outline_width,
        headline_text=payload.headline_text,
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Re-render failed"))

    output_filename = f"short_{payload.clip_id}.mp4"
    public_preview_path = Path("backend/storage/renders") / output_filename
    final_file = Path(res["final_video"])
    if final_file.exists() and public_preview_path.resolve() != final_file.resolve():
        import shutil
        shutil.copy2(final_file, public_preview_path)

    mtime = int(os.path.getmtime(public_preview_path)) if public_preview_path.exists() else 0

    return {
        "status": "success",
        "clip_id": payload.clip_id,
        "filename": output_filename,
        "preview_url": f"http://localhost:8000/api/v1/shorts/preview/{output_filename}?t={mtime}",
        "download_url": f"http://localhost:8000/api/v1/shorts/download/{output_filename}",
        "preset": payload.subtitle_preset,
    }


class ClipMetadataPayload(BaseModel):
    transcript: Optional[str] = None
    opening_hook: Optional[str] = None
    headline: Optional[str] = None
    title: Optional[str] = None
    video_title: Optional[str] = None
    channel_name: Optional[str] = None
    channel_niche: Optional[str] = None
    regenerate: bool = False


@router.get("/clips/{clip_id}/metadata", summary="Get or generate AI YouTube metadata for a clip")
@router.post("/clips/{clip_id}/metadata", summary="Generate or regenerate AI YouTube metadata for a clip")
def get_or_generate_clip_metadata(
    clip_id: str,
    regenerate: bool = Query(default=False, description="Force regenerate even if already present"),
    payload: Optional[ClipMetadataPayload] = None,
):
    """Generates transcript-grounded YouTube metadata: title alternatives, description, tags, and hashtags.
    Eliminates formulaic boilerplate, repeated lyrics, and raw transcript excerpts (master_seo.md).
    """
    if payload and payload.regenerate:
        regenerate = True

    clip = discovered_clips.get(clip_id) or SessionStore.get_clip(clip_id)
    if not clip and payload:
        # Reconstruct clip object from incoming frontend context
        clip = {
            "clip_id": clip_id,
            "transcript_segment": payload.transcript or "",
            "opening_hook": payload.opening_hook or "",
            "visual_headline": payload.headline or "",
            "headline": payload.headline or "",
            "title": payload.title or "",
            "video_title": payload.video_title or "",
        }
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found in active session.")

    existing_desc = clip.get("description", "")
    vtitle_hint = (payload.video_title if payload and payload.video_title else None) or clip.get("video_title") or ""
    detected_intel = YouTubeIntelligenceService.classify_content_type(vtitle_hint, existing_desc)
    
    is_stale_boilerplate = (
        not existing_desc
        or "Key Takeaway from" in existing_desc
        or "Key Takeaway:" in existing_desc
        or "Did you know this? Drop a comment below!" in existing_desc
        or "#Knowledge #Productivity" in existing_desc
        or (detected_intel["is_music"] and any(k in existing_desc.lower() for k in ["video editing", "growth strategy", "production technique", "retention technique"]))
        or len(clip.get("title_alternatives", [])) < 5
    )
    has_valid_tags = bool(clip.get("tags") and len(clip.get("tags", [])) >= 5)

    if not regenerate and not is_stale_boilerplate and has_valid_tags and clip.get("title") and len(clip.get("title_alternatives", [])) >= 5:
        return {
            "status": "success",
            "clip_id": clip_id,
            "title": clip.get("title"),
            "title_alternatives": clip.get("title_alternatives", []),
            "description": clip.get("description", ""),
            "hashtags": clip.get("hashtags", []),
            "tags": clip.get("tags", []),
            "inferred_content_type": clip.get("inferred_content_type", detected_intel["content_type"]),
            "inferred_content_understanding": clip.get("inferred_content_understanding", ""),
            "metadata_evidence": clip.get("metadata_evidence", detected_intel["evidence"]),
            "skill_guidance_used": clip.get("skill_guidance_used", [
                "yt-seo: search snippet in first 2 lines & disambiguation tags",
                "yt-package: 40/60 char desktop/mobile cutoffs & entity primacy",
            ]),
            "source": "cached_session",
        }

    # Extract text from transcript segment or cues
    cues = clip.get("cues") or clip.get("subtitles") or []
    transcript_text = (
        (payload.transcript if payload and payload.transcript else None)
        or clip.get("transcript_segment")
        or " ".join([c.get("text", "") for c in cues if isinstance(c, dict)]).strip()
    )
    central_idea = (
        (payload.headline if payload and payload.headline else None)
        or clip.get("central_idea")
        or clip.get("headline")
        or clip.get("title")
        or "Key Creator Insight"
    )
    opening_hook = (
        (payload.opening_hook if payload and payload.opening_hook else None)
        or clip.get("opening_hook")
        or clip.get("visual_headline")
        or ""
    )
    vtitle = (
        (payload.video_title if payload and payload.video_title else None)
        or clip.get("video_title")
        or clip.get("parent_video_title")
        or central_idea
    )

    pkg = ContentPackagerService.package_content(
        clip_id=clip_id,
        transcript=transcript_text,
        central_idea=central_idea,
        opening_hook=opening_hook,
        video_title=vtitle,
    )

    titles = pkg.get("titles", [])
    rec_idx = pkg.get("recommended_title_index", 0)
    best_title = titles[rec_idx].get("text") if titles and rec_idx < len(titles) else clip.get("title", "Insightful Short")
    desc = pkg.get("description", clip.get("description", ""))
    hashtags = pkg.get("hashtags", clip.get("hashtags", []))
    tags = pkg.get("tags", clip.get("tags", []))

    clip["title"] = best_title
    clip["title_alternatives"] = titles
    clip["description"] = desc
    clip["hashtags"] = hashtags
    clip["tags"] = tags
    clip["inferred_content_type"] = pkg.get("inferred_content_type", "")
    clip["inferred_content_understanding"] = pkg.get("inferred_content_understanding", "")
    clip["metadata_evidence"] = pkg.get("metadata_evidence", [])
    clip["skill_guidance_used"] = pkg.get("skill_guidance_used", [])
    discovered_clips[clip_id] = clip
    SessionStore.save_clip(clip_id, clip)

    return {
        "status": "success",
        "clip_id": clip_id,
        "title": best_title,
        "title_alternatives": titles,
        "recommended_title_index": rec_idx,
        "title_rationale": pkg.get("title_rationale", ""),
        "description": desc,
        "hashtags": hashtags,
        "tags": tags,
        "opening_hook": pkg.get("opening_hook", ""),
        "hook_scoring": pkg.get("hook_scoring", {}),
        "inferred_content_type": pkg.get("inferred_content_type", ""),
        "inferred_content_understanding": pkg.get("inferred_content_understanding", ""),
        "metadata_evidence": pkg.get("metadata_evidence", []),
        "skill_guidance_used": pkg.get("skill_guidance_used", []),
        "metadata_warnings": pkg.get("metadata_warnings", []),
        "rationale": pkg.get("rationale", ""),
        "source": "ai_generated",
    }


@router.post("/clips/{clip_id}/feedback", summary="Submit structured human review and rating")
def submit_clip_feedback(clip_id: str, feedback: ClipFeedbackSubmission):
    """Logs human ratings, rejection reasons, and supervised edit deltas to the dataset."""
    if clip_id not in discovered_clips:
        raise HTTPException(status_code=404, detail="Clip not found in active session.")

    clip = discovered_clips[clip_id]
    record = DatasetStore.record_feedback(clip, feedback)
    return {
        "status": "recorded",
        "record_id": record["record_id"],
        "approved_for_reference": feedback.approved_for_reference,
    }


@router.get("/dataset/export", summary="Export preferences and reference dataset in JSONL format")
def export_dataset(dataset_type: str = Query(default="preferences", description="'preferences' or 'references'")):
    """Exports structured editorial training and benchmark dataset."""
    records = DatasetStore.export_dataset(dataset_type=dataset_type)
    return {
        "dataset_type": dataset_type,
        "record_count": len(records),
        "records": records,
    }


@router.get("/preview/{filename:path}", summary="Stream rendered video preview")
def preview_short(filename: str):
    if "\0" in filename or "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Path traversal attempt detected")
    clean_filename = Path(filename).name
    base_dir = Path("backend/storage/renders").resolve()
    target_path = (base_dir / clean_filename).resolve()
    if not target_path.is_relative_to(base_dir):
        raise HTTPException(status_code=400, detail="Path traversal attempt detected")
    if not target_path.is_file():
        raise HTTPException(status_code=404, detail="Requested video file does not exist")
    return FileResponse(str(target_path), media_type="video/mp4")


@router.get("/download/{filename:path}", summary="Download rendered MP4 Short")
def download_short(filename: str):
    if "\0" in filename or "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Path traversal attempt detected")
    clean_filename = Path(filename).name
    base_dir = Path("backend/storage/renders").resolve()
    target_path = (base_dir / clean_filename).resolve()
    if not target_path.is_relative_to(base_dir):
        raise HTTPException(status_code=400, detail="Path traversal attempt detected")
    if not target_path.is_file():
        raise HTTPException(status_code=404, detail="Requested video file does not exist")
    return FileResponse(str(target_path), media_type="video/mp4", filename=clean_filename)


@router.get("/sessions", summary="Get active session summary including persistent videos and clips")
def get_session_summary():
    """Returns persistent session summary for restoring user state after browser refresh or server restart."""
    videos = SessionStore.list_videos()
    clips = SessionStore.list_clips()
    return {
        "status": "success",
        "total_videos": len(videos),
        "total_clips": len(clips),
        "videos": [
            {
                "video_id": v.get("video_id"),
                "title": v.get("title"),
                "duration_sec": v.get("duration_sec"),
                "thumbnail": v.get("thumbnail"),
                "cue_count": len(v.get("transcript_cues", [])),
            }
            for v in videos
        ],
        "clips": [
            {
                "clip_id": c.get("clip_id"),
                "parent_video_id": c.get("parent_video_id"),
                "title": c.get("title"),
                "start_sec": c.get("start_sec"),
                "end_sec": c.get("end_sec"),
                "rendered_file": c.get("rendered_file"),
            }
            for c in clips
        ],
    }


@router.get("/sessions/videos/{video_id}/clips", summary="List persistent clips discovered for a video")
def get_video_clips(video_id: str):
    if not SessionStore.has_video(video_id):
        raise HTTPException(status_code=404, detail="Video not found in persistent session")
    clips = SessionStore.list_clips(parent_video_id=video_id)
    return {
        "video_id": video_id,
        "total_clips": len(clips),
        "clips": clips,
    }


@router.get("/intelligence/audio-trends", summary="Legally compliant audio trend recommendations (Stage C)")
def get_audio_trends(
    niche: str = Query(default="general", description="Content niche or category"),
    mood: str = Query(default="energetic", description="Desired mood: energetic, focused, calm, viral"),
    pacing: str = Query(default="fast", description="Desired pacing: fast, medium, slow"),
):
    from ..services.youtube_intelligence_service import YouTubeIntelligenceService
    return YouTubeIntelligenceService.recommend_trending_audio(niche=niche, mood=mood, pacing=pacing)


@router.get("/intelligence/content-trends", summary="Shorts format and retention trends (Stage C)")
def get_content_trends(
    niche: str = Query(default="creator economy", description="Content niche"),
):
    from ..services.youtube_intelligence_service import YouTubeIntelligenceService
    return YouTubeIntelligenceService.analyze_trending_topics(niche=niche)
