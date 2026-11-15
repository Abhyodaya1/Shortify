"""Multi-Dimensional Content-Hash Caching Service for Shortify.
Provides persistent SQLite-backed caching for Whisper audio alignments and LLM editorial pipelines,
ensuring visual styling adjustments never trigger redundant network transcription or prompting.
"""

from __future__ import annotations
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional

STORAGE_CACHE_DB = Path("backend/storage/cache.db")


class ContentCacheService:
    """Manages multi-dimensional caching for speech-to-text and AI editorial roles."""

    _db_path: Path = STORAGE_CACHE_DB

    @classmethod
    def set_db_path(cls, path: Path | str) -> None:
        """Sets custom DB path (used primarily for unit testing)."""
        cls._db_path = Path(path)
        cls.init_db()

    @classmethod
    def get_connection(cls) -> sqlite3.Connection:
        cls._db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(cls._db_path.resolve()))
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def init_db(cls) -> None:
        """Initializes SQLite schema for content cache."""
        with cls.get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pipeline_cache (
                    cache_key TEXT PRIMARY KEY,
                    cache_type TEXT NOT NULL,
                    content_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata_json TEXT
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_cache_type ON pipeline_cache (cache_type)"
            )
            conn.commit()

    @classmethod
    def get(cls, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieves cached content if key exists, returning None otherwise."""
        cls.init_db()
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT content_json FROM pipeline_cache WHERE cache_key = ?",
                (cache_key,),
            )
            row = cursor.fetchone()
            if row:
                try:
                    return json.loads(row["content_json"])
                except Exception:
                    return None
        return None

    @classmethod
    def set(
        cls,
        cache_key: str,
        cache_type: str,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Stores content in SQLite cache under given key."""
        cls.init_db()
        content_json = json.dumps(content)
        meta_json = json.dumps(metadata) if metadata else None
        with cls.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO pipeline_cache (cache_key, cache_type, content_json, metadata_json)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    content_json = excluded.content_json,
                    metadata_json = excluded.metadata_json,
                    created_at = CURRENT_TIMESTAMP
                """,
                (cache_key, cache_type, content_json, meta_json),
            )
            conn.commit()

    @classmethod
    def compute_whisper_cache_key(
        cls,
        audio_bytes: bytes,
        model_id: str,
        language: str = "auto",
        temperature: float = 0.0,
    ) -> str:
        """Computes deterministic cache key for Whisper acoustic transcription."""
        audio_sha = hashlib.sha256(audio_bytes).hexdigest()
        raw_key = f"whisper:{audio_sha}:{model_id}:{language}:{temperature:.2f}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    @classmethod
    def compute_editorial_cache_key(
        cls,
        transcript_text: str,
        reasoning_model: str,
        strategy_model: str,
        channel_niche: str,
        target_audience: str,
        editorial_preferences: str,
        prompt_version: str = "1.0.0",
        schema_version: str = "1.0.0",
    ) -> str:
        """Computes deterministic cache key for multi-role editorial generation."""
        transcript_sha = hashlib.sha256(transcript_text.strip().encode("utf-8")).hexdigest()
        raw_key = (
            f"editorial:{transcript_sha}:{reasoning_model}:{strategy_model}:"
            f"{prompt_version}:{schema_version}:{channel_niche}:{target_audience}:{editorial_preferences}"
        )
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    @classmethod
    def compute_packaging_cache_key(
        cls,
        transcript_text: str,
        central_idea: str = "",
        opening_hook: str = "",
        channel_niche: str = "",
        model_id: str = "qwen/qwen3.8-27b",
        prompt_version: str = "1.0.0",
        schema_version: str = "1.0.0",
    ) -> str:
        """Computes deterministic cache key for AI YouTube content packaging and SEO metadata."""
        transcript_sha = hashlib.sha256(transcript_text.strip().encode("utf-8")).hexdigest()
        raw_key = (
            f"packaging:{transcript_sha}:{central_idea.strip()}:{opening_hook.strip()}:{channel_niche.strip()}:"
            f"{model_id}:{prompt_version}:{schema_version}"
        )
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    @classmethod
    def clear(cls, cache_type: Optional[str] = None) -> int:
        """Clears all or type-specific entries from cache, returning deleted count."""
        cls.init_db()
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            if cache_type:
                cursor.execute("DELETE FROM pipeline_cache WHERE cache_type = ?", (cache_type,))
            else:
                cursor.execute("DELETE FROM pipeline_cache")
            deleted = cursor.rowcount
            conn.commit()
            return deleted

    @classmethod
    def stats(cls) -> Dict[str, Any]:
        """Returns statistics on cached items."""
        cls.init_db()
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT cache_type, COUNT(*) as count FROM pipeline_cache GROUP BY cache_type")
            type_counts = {row["cache_type"]: row["count"] for row in cursor.fetchall()}
            cursor.execute("SELECT COUNT(*) as total FROM pipeline_cache")
            total = cursor.fetchone()["total"]
            return {"total_cached_items": total, "by_type": type_counts}

