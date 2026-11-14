"""YouTube Channel & Scheduling API
Provides endpoints for channel connection (Sandbox & OAuth), video import, and scheduled upload publishing.
"""

from __future__ import annotations
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from ..services.persistent_scheduler import PersistentScheduler
from ..services.youtube_oauth_service import YouTubeOAuthService

router = APIRouter(prefix="/api/v1/youtube", tags=["YouTube Integration"])


class SaveGoogleCredentialsRequest(BaseModel):
    client_id: str
    client_secret: str


class ScheduleUploadRequest(BaseModel):
    clip_id: str
    title: str
    description: str = ""
    tags: List[str] = Field(default_factory=list)
    video_file_path: str = ""
    thumbnail_url: str = ""
    scheduled_time: str
    target_channel_id: str = "UC_abhyodaya_clips_sandbox"
    visibility: str = "unlisted"


@router.get("/status", summary="Get YouTube channel connection status")
def get_channel_status(user_id: str = "default_user"):
    """Returns the currently connected YouTube channel, or None if unconnected."""
    status = PersistentScheduler.get_channel_status(user_id)
    return {
        "is_connected": status is not None,
        "channel": status,
        "is_oauth_configured": YouTubeOAuthService.is_configured(),
        "quota": {
            "daily_limit": 10000,
            "used_today": 0,
            "remaining": 10000,
            "cost_per_upload": 1600,
        }
    }


@router.post("/save-credentials", summary="Save Google OAuth Client ID and Secret")
def save_google_credentials(payload: SaveGoogleCredentialsRequest):
    """Saves Google OAuth Client ID and Secret into .env and current runtime environment."""
    env_path = Path(".env")
    lines = []
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

    new_lines = [l for l in lines if not l.startswith("GOOGLE_CLIENT_ID=") and not l.startswith("GOOGLE_CLIENT_SECRET=")]
    new_lines.append(f"GOOGLE_CLIENT_ID={payload.client_id.strip()}\n")
    new_lines.append(f"GOOGLE_CLIENT_SECRET={payload.client_secret.strip()}\n")
    if not any(l.startswith("GOOGLE_OAUTH_REDIRECT_URI=") for l in new_lines):
        new_lines.append("GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/api/v1/youtube/callback\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    os.environ["GOOGLE_CLIENT_ID"] = payload.client_id.strip()
    os.environ["GOOGLE_CLIENT_SECRET"] = payload.client_secret.strip()
    os.environ["GOOGLE_OAUTH_REDIRECT_URI"] = "http://localhost:8000/api/v1/youtube/callback"

    return {"status": "saved", "message": "Google OAuth credentials saved successfully!"}


@router.get("/auth-url", summary="Get Google OAuth Authorization URL")
def get_auth_url(user_id: str = "default_user"):
    """Generates the Google OAuth 2.0 authorization URL for real channel connection."""
    try:
        url = YouTubeOAuthService.get_authorization_url(state=user_id)
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/callback", summary="Google OAuth 2.0 Redirect Callback")
async def oauth_callback(code: Optional[str] = None, error: Optional[str] = None, state: Optional[str] = "default_user"):
    """Handles the redirect from Google OAuth, exchanges the code, and saves channel info."""
    if error:
        return RedirectResponse(f"http://localhost:3000?oauth_error={error}")
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    try:
        token_data = await YouTubeOAuthService.exchange_code_for_tokens(code)
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")

        # Retain previous refresh_token if Google omitted it on re-consent
        existing_channel = PersistentScheduler.get_channel_status(state or "default_user")
        if not refresh_token and existing_channel:
            refresh_token = existing_channel.get("refresh_token")

        channel_info = await YouTubeOAuthService.fetch_channel_profile(access_token)

        PersistentScheduler.save_connected_channel(
            user_id=state or "default_user",
            channel_id=channel_info["channel_id"],
            channel_title=channel_info["channel_title"],
            custom_url=channel_info["custom_url"],
            thumbnail_url=channel_info["thumbnail_url"],
            subscriber_count=channel_info["subscriber_count"],
            video_count=channel_info["video_count"],
            refresh_token=refresh_token,
            access_token=access_token,
            is_sandbox=False,
        )

        return RedirectResponse("http://localhost:3000?youtube_connected=true")
    except Exception as e:
        import urllib.parse
        err_msg = urllib.parse.quote(str(e))
        return RedirectResponse(f"http://localhost:3000?oauth_error={err_msg}")


@router.post("/connect-sandbox", summary="1-Click Connect Sandbox YouTube Channel")
def connect_sandbox(user_id: str = "default_user"):
    """Instantly connects a verified sandbox channel for zero-friction development."""
    channel = PersistentScheduler.connect_sandbox_channel(user_id)
    return {
        "status": "connected",
        "channel": channel,
        "message": "Connected @AbhyodayaClips (Sandbox) successfully!",
    }


@router.post("/disconnect", summary="Disconnect YouTube channel")
def disconnect_channel(user_id: str = "default_user"):
    PersistentScheduler.disconnect_channel(user_id)
    return {"status": "disconnected"}


@router.get("/channel-videos", summary="List channel's available videos for 1-click import")
async def get_channel_videos(user_id: str = "default_user"):
    """Returns videos from the user's connected YouTube channel ready to be clipped."""
    channel = PersistentScheduler.get_channel_status(user_id)
    if channel and not channel.get("is_sandbox") and channel.get("refresh_token"):
        try:
            access_token = await YouTubeOAuthService.refresh_access_token(channel["refresh_token"])
            real_videos = await YouTubeOAuthService.fetch_channel_videos(access_token, max_results=10)
            if real_videos:
                return {"videos": real_videos, "is_live": True}
        except Exception as e:
            print(f"[YouTube] Error fetching live channel videos: {e}")

    # Fallback to sample videos when in sandbox or when channel has 0 videos
    return {
        "is_live": False,
        "videos": [
            {
                "id": "vid_sanatana_dharma",
                "title": "The Hidden Foundation of Sanatana Dharma",
                "youtube_url": "https://www.youtube.com/watch?v=sample1",
                "duration_min": "14:20",
                "views": "142K",
                "published_date": "Nov 8, 2026",
                "thumbnail": "https://images.unsplash.com/photo-1544717305-2782549b5136?w=600&auto=format&fit=crop&q=80",
            },
            {
                "id": "vid_life_lessons",
                "title": "35 Years of Life Lessons in Just 5 Minutes",
                "youtube_url": "https://www.youtube.com/watch?v=sample2",
                "duration_min": "09:16",
                "views": "380K",
                "published_date": "Nov 11, 2026",
                "thumbnail": "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=600&auto=format&fit=crop&q=80",
            },
            {
                "id": "vid_creator_mindset",
                "title": "The Mindset Shift That Changes Your Creator Growth",
                "youtube_url": "https://www.youtube.com/watch?v=sample3",
                "duration_min": "18:45",
                "views": "89K",
                "published_date": "Nov 5, 2026",
                "thumbnail": "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?w=600&auto=format&fit=crop&q=80",
            },
            {
                "id": "vid_back_to_school",
                "title": "TYPES OF BACK TO SCHOOL STUDENTS || Relatable comedy by 5-Minute Crafts",
                "youtube_url": "https://www.youtube.com/watch?v=sample4",
                "duration_min": "12:10",
                "views": "1.2M",
                "published_date": "Nov 1, 2026",
                "thumbnail": "https://images.unsplash.com/photo-1509062522246-3755977927d7?w=600&auto=format&fit=crop&q=80",
            }
        ]
    }


@router.post("/schedule", summary="Schedule a clip for automated YouTube publishing")
def schedule_upload(payload: ScheduleUploadRequest):
    """Schedules a clip to be published at a specified time with metadata."""
    res = PersistentScheduler.schedule_clip_upload(
        clip_id=payload.clip_id,
        title=payload.title,
        description=payload.description,
        tags=payload.tags,
        video_file_path=payload.video_file_path,
        scheduled_time=payload.scheduled_time,
        target_channel_id=payload.target_channel_id,
        visibility=payload.visibility,
        thumbnail_url=payload.thumbnail_url,
    )
    return {"status": "success", "scheduled_job": res}


@router.get("/queue", summary="List scheduled and published upload queue")
def list_upload_queue(channel_id: Optional[str] = None):
    """Returns the persistent queue of scheduled and published YouTube Shorts."""
    jobs = PersistentScheduler.list_scheduled_uploads(channel_id)
    return {"queue": jobs}


@router.delete("/queue/{job_id}", summary="Cancel a scheduled upload")
def cancel_upload(job_id: str):
    success = PersistentScheduler.cancel_scheduled_upload(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Scheduled job not found")
    return {"status": "cancelled", "job_id": job_id}


@router.post("/queue/{job_id}/publish-now", summary="Force instant publish (Sandbox or Live)")
async def publish_now(job_id: str):
    try:
        res = await PersistentScheduler.trigger_publish(job_id)
        return {"status": "success", "result": res}
    except Exception as e:
        logger.error(f"Failed to publish job {job_id}: {e}")
        raise HTTPException(status_code=400, detail=f"Publish failed: {str(e)}")


@router.get("/worker/status", summary="Background Publishing Worker Status")
def get_worker_status():
    from ..services.background_worker import BackgroundPublishWorker
    return BackgroundPublishWorker.get_instance().get_status()


class EmergencyStopRequest(BaseModel):
    stopped: bool = True
    user_id: str = "default_user"


@router.post("/worker/emergency-stop", summary="Emergency Stop / Resume Scheduled Publishing")
def set_emergency_stop(payload: EmergencyStopRequest):
    PersistentScheduler.set_emergency_stop(payload.user_id, payload.stopped)
    from ..services.background_worker import BackgroundPublishWorker
    return {
        "emergency_stop": payload.stopped,
        "worker_status": BackgroundPublishWorker.get_instance().get_status(),
        "message": "Emergency stop activated. Background publishing paused." if payload.stopped else "Publishing resumed.",
    }


# --------------------------------------------------------------------------
# YouTube Intelligence Agent Endpoints (yt-script, yt-package, yt-seo)
# --------------------------------------------------------------------------

class ScoreHookRequest(BaseModel):
    hook_text: str

class LintPackagingRequest(BaseModel):
    title: str
    thumbnail_text: Optional[str] = None

class GenerateSeoRequest(BaseModel):
    topic: str
    headline: str
    channel_handle: str = "@AbhyodayaClips"


@router.post("/intel/score-hook", summary="Deterministic Hook Scoring (yt-script)")
def score_hook(payload: ScoreHookRequest):
    from ..services.youtube_intelligence_service import YouTubeIntelligenceService
    return YouTubeIntelligenceService.score_hook(payload.hook_text)


@router.post("/intel/lint-packaging", summary="Title & Thumbnail Synergy Linter (yt-package)")
def lint_packaging(payload: LintPackagingRequest):
    from ..services.youtube_intelligence_service import YouTubeIntelligenceService
    return YouTubeIntelligenceService.lint_packaging(payload.title, payload.thumbnail_text)


@router.post("/intel/generate-seo", summary="Generate High-CTR SEO Metadata (yt-seo)")
def generate_seo(payload: GenerateSeoRequest):
    from ..services.youtube_intelligence_service import YouTubeIntelligenceService
    return YouTubeIntelligenceService.generate_seo_metadata(payload.topic, payload.headline, payload.channel_handle)

