"""FastAPI application entrypoint for the Video Agent backend."""

import os
from dotenv import load_dotenv

# Load .env variables from workspace root
load_dotenv()

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.assets import router as assets_router
from .api.generation import router as generation_router
from .api.viral_clipper_api import router as viral_router
from .api.shorts_mvp_api import router as shorts_router
from .api.profile_routes import router as profile_router
from .api.youtube_channel_api import router as youtube_router
from .services.background_worker import BackgroundPublishWorker
from .services.persistent_scheduler import PersistentScheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize persistence
    PersistentScheduler.init_db()

    # Avoid spawning the infinite background polling loop during pytest or automated test runs
    is_test_env = (
        os.getenv("TESTING", "").lower() in ("1", "true", "yes")
        or os.getenv("DISABLE_BACKGROUND_WORKER", "").lower() in ("1", "true", "yes")
        or "PYTEST_CURRENT_TEST" in os.environ
    )

    worker = None
    if not is_test_env:
        worker = BackgroundPublishWorker.get_instance()
        await worker.start()

    yield

    # Shutdown: Stop worker cleanly
    if worker is not None:
        await worker.stop()


app = FastAPI(
    title="General Video Agent (GVA) Backend",
    description="Clean-room implementation of an autonomous video creation & editing agent system.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for local frontend and MCP hosts
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(assets_router)
app.include_router(generation_router)
app.include_router(viral_router)
app.include_router(shorts_router)
app.include_router(profile_router)
app.include_router(youtube_router)


@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "healthy", "service": "video-agent-backend"}
