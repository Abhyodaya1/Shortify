"""Unit tests for the Model Context Protocol (MCP) Server tools."""

import json
import pytest
from mcp_server.server import (
    create_video,
    create_followup,
    upload_asset,
    get_session_status,
    list_engines,
    list_templates,
    get_credit_balance,
    show_plans_and_credits,
)


@pytest.mark.anyio
async def test_mcp_upload_asset():
    res = await upload_asset(filename="raw_interview.mp4", content_type="video/mp4", byte_size=2048)
    data = json.loads(res)
    assert "upload_url" in data
    assert "attachment_url" in data
    assert data["headers"]["Content-Type"] == "video/mp4"


@pytest.mark.anyio
async def test_mcp_create_video_and_followup_cycle():
    # 1. create_video
    raw_res = await create_video(
        prompt="Make a high energy product launch video for our calendar agent",
        engine="gva",
        effort="extended",
        aspect_ratio="16:9",
        attachments=["http://localhost:8000/api/v1/assets/demo.mp4"],
    )
    result = json.loads(raw_res)
    assert "job_id" in result
    assert "thread_id" in result
    assert result["status"] == "completed"

    thread_id = result["thread_id"]
    job_id = result["job_id"]

    # 2. get_session_status
    status_raw = await get_session_status(job_id=job_id)
    status_data = json.loads(status_raw)
    assert status_data["status"] == "completed"
    assert "download_url" in status_data["output"]

    # 3. create_followup
    followup_raw = await create_followup(
        thread_id=thread_id,
        instruction="Isolate the active speaker in a close-up",
        timestamp_ms=2500,
        annotation_bounds={"x": 100.0, "y": 50.0},
    )
    followup_data = json.loads(followup_raw)
    assert followup_data["status"] == "completed"
    assert "isolate speaker" in followup_data["diff_summary"]


@pytest.mark.anyio
async def test_mcp_metadata_and_billing_tools():
    # list_engines
    engines = json.loads(await list_engines())
    assert len(engines["engines"]) == 3
    engine_ids = [e["id"] for e in engines["engines"]]
    assert "gva" in engine_ids
    assert "motion" in engine_ids

    # list_templates
    templates = json.loads(await list_templates(engine="gva"))
    assert len(templates["templates"]) >= 3

    # get_credit_balance
    balance = json.loads(await get_credit_balance())
    assert balance["credits_available"] > 0
    assert balance["plan"] == "Pro"

    # show_plans_and_credits
    plans = json.loads(await show_plans_and_credits())
    assert len(plans["plans"]) == 3

