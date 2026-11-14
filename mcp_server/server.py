"""Model Context Protocol (MCP) Server for the General Video Agent.

Implements the official tool contracts observed on https://docs.motion.so/guides/mcp.
Compatible with Claude Desktop, Cursor, ChatGPT, and external autonomous agents.
"""

from __future__ import annotations
import json
import asyncio
from typing import List, Optional, Dict, Any
from uuid import uuid4
from mcp.server.mcpserver import MCPServer
from backend.app.services.planner import SequencePlanner
from backend.app.services.revision import DeltaPatcher
from backend.app.services.storage import StorageService
from backend.app.models.timeline import Timeline

server = MCPServer("motion-gva-mcp")
planner = SequencePlanner()
storage_service = StorageService()

# In-memory storage for active MCP sessions
mcp_sessions: Dict[str, Dict[str, Any]] = {}
mcp_timelines: Dict[str, Timeline] = {}


@server.tool()
async def create_video(
    prompt: str,
    engine: str = "gva",
    effort: str = "standard",
    aspect_ratio: str = "16:9",
    duration: Optional[str] = None,
    template: Optional[str] = None,
    design_system_id: Optional[str] = None,
    design_md: Optional[str] = None,
    style_reference_url: Optional[str] = None,
    attachments: Optional[List[str]] = None,
) -> str:
    """Generate a video from a prompt (async).
    
    Parameters:
    - prompt: 1–12,000 characters describing the video cut.
    - engine: 'gva' (General Video Agent), 'motion' (Remotion motion graphics), or 'motion_legacy'.
    - effort: 'standard', 'high', or 'extended'.
    - aspect_ratio: '16:9', '9:16', '1:1', '4:5', '21:9'.
    - attachments: Array of public HTTPS URLs uploaded via upload_asset.
    """
    job_id = str(uuid4())
    thread_id = str(uuid4())

    timeline = await planner.plan_timeline(
        prompt=prompt,
        engine=engine,
        effort=effort,
        aspect_ratio=aspect_ratio,
        attachments=attachments or [],
        style_reference_url=style_reference_url,
        design_md=design_md,
    )

    mcp_timelines[job_id] = timeline
    mcp_sessions[job_id] = {
        "job_id": job_id,
        "thread_id": thread_id,
        "status": "completed",
        "progress_percent": 100,
        "output": {
            "download_url": f"http://localhost:8000/api/v1/videos/{job_id}/export/remotion"
        },
        "poll_after_seconds": 2,
    }

    result = {
        "job_id": job_id,
        "thread_id": thread_id,
        "status": "completed",
        "poll_after_seconds": 2,
        "timeline_id": str(timeline.timeline_id),
        "output": mcp_sessions[job_id]["output"],
    }
    return json.dumps(result, indent=2)


@server.tool()
async def create_followup(
    thread_id: str,
    instruction: str,
    timestamp_ms: Optional[int] = None,
    annotation_bounds: Optional[Dict[str, float]] = None,
) -> str:
    """Revise a completed video job or reply to interactive pause."""
    # Find matching job
    target_job_id = None
    for jid, session in mcp_sessions.items():
        if session.get("thread_id") == thread_id or jid == thread_id:
            target_job_id = jid
            break

    if not target_job_id or target_job_id not in mcp_timelines:
        return json.dumps({"error": f"Session or timeline not found for thread_id '{thread_id}'"})

    timeline = mcp_timelines[target_job_id]
    updated_timeline, diff_summary = DeltaPatcher.apply_followup_instruction(
        timeline=timeline,
        instruction=instruction,
        timestamp_ms=timestamp_ms,
        annotation_bounds=annotation_bounds,
    )

    mcp_timelines[target_job_id] = updated_timeline
    return json.dumps({
        "status": "completed",
        "thread_id": thread_id,
        "diff_summary": diff_summary,
        "updated_timeline_id": str(updated_timeline.timeline_id),
    }, indent=2)


@server.tool()
async def upload_asset(filename: str, content_type: str, byte_size: Optional[int] = None) -> str:
    """Get a signed upload URL for a local file (video/audio/image) so it can be used in attachments.
    The server cannot read file:// paths — upload first, then pass the returned attachment_url.
    """
    ticket = storage_service.create_upload_ticket(
        filename=filename,
        content_type=content_type,
        byte_size=byte_size,
    )
    return ticket.model_dump_json(indent=2)


@server.tool()
async def get_session_status(job_id: str) -> str:
    """Read job status and download_url when completed."""
    session = mcp_sessions.get(job_id)
    if not session:
        return json.dumps({"error": f"Job '{job_id}' not found"})
    return json.dumps(session, indent=2)


@server.tool()
async def list_engines() -> str:
    """List accessible video creation engines and effort tiers."""
    engines = [
        {
            "id": "gva",
            "name": "General Video Agent",
            "description": "Multicam video cutting, talking head tracking, and autonomous sequence assembly",
            "efforts": ["standard", "extended"],
        },
        {
            "id": "motion",
            "name": "Motion Graphics",
            "description": "Code-based motion design, kinetic typography, and Remotion animations",
            "efforts": ["standard", "high"],
        },
        {
            "id": "motion_legacy",
            "name": "Motion Legacy",
            "description": "Backward-compatible video composition pipeline",
            "efforts": ["standard"],
        },
    ]
    return json.dumps({"engines": engines}, indent=2)


@server.tool()
async def list_templates(engine: str = "gva") -> str:
    """List account-accessible templates for an engine."""
    templates = [
        {"id": "multicam-interview", "name": "Multicam Interview / Podcast", "aspect_ratios": ["16:9", "9:16"]},
        {"id": "article-to-video", "name": "Article to Video Digest", "aspect_ratios": ["16:9", "9:16", "1:1"]},
        {"id": "launch-video", "name": "Product Launch Video", "aspect_ratios": ["16:9", "21:9"]},
        {"id": "talking-head", "name": "Social Talking Head with Captions", "aspect_ratios": ["9:16", "4:5"]},
    ]
    return json.dumps({"engine": engine, "templates": templates}, indent=2)


@server.tool()
async def list_chats() -> str:
    """Browse historical video project chats."""
    chats = [
        {"chat_id": jid, "thread_id": s["thread_id"], "status": s["status"]}
        for jid, s in mcp_sessions.items()
    ]
    return json.dumps({"chats": chats}, indent=2)


@server.tool()
async def get_credit_balance() -> str:
    """Read current account credit balance and plan status."""
    return json.dumps({
        "credits_available": 1000,
        "plan": "Pro",
        "auto_topup": False,
        "currency": "credits",
    }, indent=2)


@server.tool()
async def show_plans_and_credits() -> str:
    """Show plans, balance, and top-up options for out-of-credits recovery."""
    plans = [
        {"plan_id": "flex", "name": "Flex", "price": "$6", "credits": 200, "type": "one_time"},
        {"plan_id": "pro", "name": "Pro", "price": "$29/mo", "credits": 1000, "type": "monthly"},
        {"plan_id": "enterprise", "name": "Enterprise", "price": "Custom", "credits": 50000, "type": "annual"},
    ]
    return json.dumps({"plans": plans, "portal_url": "https://motion.so/pricing"}, indent=2)


if __name__ == "__main__":
    server.run(transport="stdio")

