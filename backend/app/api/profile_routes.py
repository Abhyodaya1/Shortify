"""API routes for managing the persistent Editorial Profile."""

from __future__ import annotations
from fastapi import APIRouter, HTTPException, status
from ..models.editorial_profile import EditorialProfile
from ..storage.profile_store import ProfileStore

router = APIRouter(prefix="/api/v1/profile", tags=["Editorial Profile"])


@router.get("", response_model=EditorialProfile, summary="Get current active editorial profile")
async def get_profile():
    """Returns the persistent active editorial profile used for clip generation."""
    return ProfileStore.get_active_profile()


@router.put("", response_model=EditorialProfile, summary="Update active editorial profile")
async def update_profile(updated: EditorialProfile):
    """Updates the active profile and persists changes to disk."""
    current = ProfileStore.get_active_profile()
    updated.version = current.version + 1
    saved = ProfileStore.save_active_profile(updated)
    return saved


@router.post("/reset", response_model=EditorialProfile, summary="Reset editorial profile to defaults")
async def reset_profile():
    """Resets the profile to personal default parameters."""
    default_profile = EditorialProfile()
    saved = ProfileStore.save_active_profile(default_profile)
    return saved
