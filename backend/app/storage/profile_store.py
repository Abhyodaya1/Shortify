"""Profile Store: Local persistent storage for active and snapshotted Editorial Profiles."""

from __future__ import annotations
import json
from pathlib import Path
from typing import Optional, Dict, Any
from ..models.editorial_profile import EditorialProfile

PROFILE_DIR = Path("data/profiles")
PROFILE_DIR.mkdir(parents=True, exist_ok=True)
ACTIVE_PROFILE_FILE = PROFILE_DIR / "active_profile.json"


class ProfileStore:
    """Manages profile loading, updating, and immutable snapshot generation."""

    @classmethod
    def get_active_profile(cls) -> EditorialProfile:
        """Loads the active profile from disk, or initializes default if missing."""
        if not ACTIVE_PROFILE_FILE.exists():
            default_profile = EditorialProfile()
            cls.save_active_profile(default_profile)
            return default_profile

        try:
            with open(ACTIVE_PROFILE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return EditorialProfile(**data)
        except Exception:
            default_profile = EditorialProfile()
            cls.save_active_profile(default_profile)
            return default_profile

    @classmethod
    def save_active_profile(cls, profile: EditorialProfile) -> EditorialProfile:
        """Persists the profile to disk with incremented version."""
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        with open(ACTIVE_PROFILE_FILE, "w", encoding="utf-8") as f:
            json.dump(profile.model_dump(), f, indent=2)
        return profile

    @classmethod
    def snapshot_profile(cls, override_profile: Optional[EditorialProfile] = None) -> Dict[str, Any]:
        """Creates an immutable snapshot dictionary for associating with a job or clip."""
        active = override_profile or cls.get_active_profile()
        return active.snapshot()

