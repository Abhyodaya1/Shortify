"""API endpoints for Viral Clipping, Hook Scoring, and Dead-Air Editing."""

from __future__ import annotations
from typing import Optional, List, Dict, Any
from uuid import uuid4
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ..services.viral_clipper import ViralHookScorer, DeadAirDetector, ViralClipperService
from .generation import jobs_db, timelines_db

router = APIRouter(prefix="/api/v1/viral", tags=["Viral Clipping & Hook Engine"])


class ScoreHookRequest(BaseModel):
    hook_text: str = Field(..., min_length=3, description="Hook opening sentence to score")


class AnalyzeTranscriptRequest(BaseModel):
    transcript_text: str = Field(..., min_length=10, description="SRT, VTT, or plain text transcript")
    video_asset_id: Optional[str] = Field(default="source_video.mp4")
    target_platform: str = Field(default="shorts", description="'shorts' (9:16) or 'widescreen' (16:9)")


class CreateShortRequest(BaseModel):
    candidate_data: Dict[str, Any] = Field(..., description="Selected viral short candidate object")
    video_asset_id: str = Field(default="source_video.mp4")
    aspect_ratio: str = Field(default="9:16", description="'9:16' or '16:9'")


@router.post("/score-hook", summary="Score a YouTube hook across 5 properties (yt-script hookscore contract)")
def score_hook(payload: ScoreHookRequest):
    """Evaluates hook against 21 formulas with weakest-link weighting."""
    return ViralHookScorer.score_hook(payload.hook_text)


@router.post("/analyze-transcript", summary="Analyze transcript for dead-air and generate viral shorts candidates")
def analyze_transcript(payload: AnalyzeTranscriptRequest):
    """Finds silent gaps, extracts self-contained 20-55s clips, and scores opening hooks."""
    try:
        return ViralClipperService.process_transcript_to_clips(
            transcript_text=payload.transcript_text,
            video_asset_id=payload.video_asset_id,
            target_platform=payload.target_platform,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/create-short", status_code=status.HTTP_201_CREATED, summary="Turn candidate into a renderable Timeline")
def create_short(payload: CreateShortRequest):
    """Builds a Universal Timeline with 9:16 vertical crop, kinetic captions, and audio sync."""
    timeline = ViralClipperService.assemble_short_timeline(
        candidate_data=payload.candidate_data,
        video_asset_id=payload.video_asset_id,
        aspect_ratio=payload.aspect_ratio,
    )
    job_id = str(uuid4())
    timelines_db[job_id] = timeline
    jobs_db[job_id] = {
        "job_id": job_id,
        "status": "completed",
        "progress_percent": 100,
        "engine": "viral_clipper",
    }
    return {
        "job_id": job_id,
        "timeline_id": str(timeline.timeline_id),
        "timeline": timeline,
    }

