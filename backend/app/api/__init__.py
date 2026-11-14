"""API routers package."""
from .assets import router as assets_router
from .generation import router as generation_router

__all__ = ["assets_router", "generation_router"]
