"""Video generation and revision endpoints (create_video and create_followup)."""

from __future__ import annotations
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from ..models.timeline import Timeline
from ..services.planner import SequencePlanner
from ..services.revision import DeltaPatcher
from ..services.render_engine import FFmpegRenderEngine
from ..serializers.remotion_serializer import RemotionSerializer
from ..serializers.fcpxml_serializer import FCPXMLSerializer

router = APIRouter(prefix="/api/v1/videos", tags=["Video Generation & Editing"])
planner = SequencePlanner()

# In-memory database of active jobs and timelines (can be swapped for Redis/PostgreSQL)
jobs_db: Dict[str, Dict[str, Any]] = {}
timelines_db: Dict[str, Timeline] = {}


class CreateVideoRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=12000, description="Creative brief (1-12000 chars)")
    engine: str = Field(default="gva", description="Execution engine ('gva', 'motion', 'motion_legacy')")
    effort: str = Field(default="standard", description="Effort level ('standard', 'high', 'extended')")
    aspect_ratio: str = Field(default="16:9", description="Aspect ratio (16:9, 9:16, 1:1, 4:5, 21:9)")
    duration: Optional[str] = Field(default=None, description="Target duration (<10s, 10-30s, 30s-1min, 1-5min)")
    template: Optional[str] = Field(default=None, description="Template identifier")
    design_system_id: Optional[str] = Field(default=None, description="Brand design system UUID")
    design_md: Optional[str] = Field(default=None, description="Markdown brand instructions")
    style_reference_url: Optional[str] = Field(default=None, description="External reference URL (YouTube)")
    attachments: List[str] = Field(default_factory=list, description="Public media attachment URLs")


class CreateFollowupRequest(BaseModel):
    job_id: str = Field(..., description="ID of the completed or active job")
    instruction: str = Field(..., description="Conversational edit request (e.g. 'remove whiteboard')")
    timestamp_ms: Optional[int] = Field(default=None, description="Exact timestamp for the modification")
    annotation_bounds: Optional[Dict[str, float]] = Field(default=None, description="Spatial coordinates (x, y, w, h)")


@router.post("/create", status_code=status.HTTP_202_ACCEPTED, summary="Create a new video generation job (create_video contract)")
async def create_video(payload: CreateVideoRequest):
    """Initiates autonomous planning and timeline assembly."""
    job_id = str(uuid4())
    thread_id = str(uuid4())

    jobs_db[job_id] = {
        "job_id": job_id,
        "thread_id": thread_id,
        "status": "planning",
        "progress_percent": 10,
        "engine": payload.engine,
        "effort": payload.effort,
        "poll_after_seconds": 2,
        "download_url": None,
    }

    # Execute planning
    timeline = await planner.plan_timeline(
        prompt=payload.prompt,
        engine=payload.engine,
        effort=payload.effort,
        aspect_ratio=payload.aspect_ratio,
        attachments=payload.attachments,
        style_reference_url=payload.style_reference_url,
        design_md=payload.design_md,
    )

    timelines_db[job_id] = timeline
    jobs_db[job_id]["status"] = "completed"
    jobs_db[job_id]["progress_percent"] = 100
    jobs_db[job_id]["download_url"] = f"/api/v1/videos/{job_id}/export/remotion"

    return {
        "job_id": job_id,
        "thread_id": thread_id,
        "status": "completed",
        "poll_after_seconds": 2,
        "timeline_id": str(timeline.timeline_id),
    }


@router.post("/followup", summary="Revise an existing video cut (create_followup contract)")
async def create_followup(payload: CreateFollowupRequest):
    """Applies surgical revisions to a timeline without regenerating from scratch."""
    if payload.job_id not in timelines_db:
        raise HTTPException(status_code=404, detail="Job or timeline not found")

    timeline = timelines_db[payload.job_id]
    updated_timeline, diff_summary = DeltaPatcher.apply_followup_instruction(
        timeline=timeline,
        instruction=payload.instruction,
        timestamp_ms=payload.timestamp_ms,
        annotation_bounds=payload.annotation_bounds,
    )

    timelines_db[payload.job_id] = updated_timeline
    return {
        "job_id": payload.job_id,
        "status": "completed",
        "diff_summary": diff_summary,
        "updated_timeline_id": str(updated_timeline.timeline_id),
    }


@router.get("/status/{job_id}", summary="Check generation status (get_session_status / job_status contract)")
async def get_job_status(job_id: str):
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs_db[job_id]


@router.get("/{job_id}/timeline", summary="Fetch structured timeline JSON")
async def get_timeline(job_id: str):
    if job_id not in timelines_db:
        raise HTTPException(status_code=404, detail="Timeline not found")
    return timelines_db[job_id]


@router.get("/{job_id}/export/{export_format}", summary="Export timeline in chosen NLE format")
async def export_timeline(job_id: str, export_format: str):
    if job_id not in timelines_db:
        raise HTTPException(status_code=404, detail="Timeline not found")
    timeline = timelines_db[job_id]

    if export_format.lower() in ("remotion", "tsx"):
        content = RemotionSerializer.serialize_to_tsx(timeline)
        return {"format": "remotion", "content": content}
    elif export_format.lower() in ("fcpxml", "premiere", "xml"):
        content = FCPXMLSerializer.serialize_to_fcpxml(timeline)
        return {"format": "fcpxml", "content": content}
    elif export_format.lower() in ("mp4", "video"):
        output_file = f"backend/storage/renders/{job_id}.mp4"
        rendered_path = FFmpegRenderEngine.render_timeline_to_mp4(timeline, output_file)
        return FileResponse(rendered_path, media_type="video/mp4", filename=f"{job_id}.mp4")
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{export_format}'. Use 'remotion', 'fcpxml', or 'mp4'",
        )

