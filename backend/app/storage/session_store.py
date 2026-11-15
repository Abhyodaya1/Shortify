"""Session Store & Clip Persistence
Persists ingested video metadata and discovered clip candidate sessions in local SQLite.
Ensures user sessions, discovered clips, and render artifacts survive backend restarts (REL-02).
"""

from __future__ import annotations
import os
import json
import sqlite3
from collections.abc import MutableMapping
from pathlib import Path
from typing import Dict, Any, Optional, List, Iterator

STORAGE_DIR = Path("backend/storage")
if not STORAGE_DIR.exists():
    STORAGE_DIR = Path("storage")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_DB_PATH = STORAGE_DIR / "session.db"


def _json_serialize(obj: Any) -> str:
    def default_serializer(o):
        if isinstance(o, (Path, os.PathLike)):
            return str(o)
        if hasattr(o, "isoformat"):
            return o.isoformat()
        if hasattr(o, "__dict__"):
            return o.__dict__
        return str(o)
    return json.dumps(obj, default=default_serializer)


class SessionStore:
    """SQLite-backed persistent store for ingested videos and discovered clip candidates."""

    _db_path: Path = DEFAULT_DB_PATH
    _initialized: bool = False
    _videos_cache: Dict[str, Dict[str, Any]] = {}
    _clips_cache: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def set_db_path(cls, path: Path) -> None:
        """Configures custom database path (useful for testing)."""
        cls._db_path = Path(path)
        cls._initialized = False
        cls._videos_cache.clear()
        cls._clips_cache.clear()

    @classmethod
    def get_db_path(cls) -> Path:
        return cls._db_path

    @classmethod
    def _get_connection(cls) -> sqlite3.Connection:
        cls._ensure_initialized()
        conn = sqlite3.connect(str(cls._db_path.resolve()), timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    @classmethod
    def _ensure_initialized(cls) -> None:
        if cls._initialized:
            return
        cls._db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(cls._db_path.resolve()), timeout=10.0)
        try:
            conn.row_factory = sqlite3.Row
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS session_videos (
                video_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                filepath TEXT NOT NULL,
                duration_sec REAL DEFAULT 0,
                thumbnail TEXT DEFAULT '',
                width INTEGER DEFAULT 0,
                height INTEGER DEFAULT 0,
                data_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS session_clips (
                clip_id TEXT PRIMARY KEY,
                parent_video_id TEXT NOT NULL,
                title TEXT,
                start_sec REAL,
                end_sec REAL,
                rendered_file TEXT,
                data_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_clips_parent_video ON session_clips(parent_video_id);
            """)
            conn.commit()

            # Warm in-memory cache from database
            cur = conn.execute("SELECT video_id, data_json FROM session_videos")
            for row in cur.fetchall():
                try:
                    cls._videos_cache[row["video_id"]] = json.loads(row["data_json"])
                except Exception:
                    pass

            cur = conn.execute("SELECT clip_id, data_json FROM session_clips")
            for row in cur.fetchall():
                try:
                    cls._clips_cache[row["clip_id"]] = json.loads(row["data_json"])
                except Exception:
                    pass

            cls._initialized = True
        finally:
            conn.close()

    @classmethod
    def save_video(cls, video_id: str, data: Dict[str, Any]) -> None:
        """Saves or updates video metadata in SQLite and in-memory cache."""
        cls._ensure_initialized()
        cls._videos_cache[video_id] = data
        raw_json = _json_serialize(data)
        title = data.get("title", "")
        filepath = str(data.get("filepath", ""))
        duration = float(data.get("duration_sec", 0.0) or 0.0)
        thumb = str(data.get("thumbnail", "") or "")
        w = int(data.get("width", 0) or 0)
        h = int(data.get("height", 0) or 0)

        with cls._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO session_videos (video_id, title, filepath, duration_sec, thumbnail, width, height, data_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(video_id) DO UPDATE SET
                    title = excluded.title,
                    filepath = excluded.filepath,
                    duration_sec = excluded.duration_sec,
                    thumbnail = excluded.thumbnail,
                    width = excluded.width,
                    height = excluded.height,
                    data_json = excluded.data_json,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (video_id, title, filepath, duration, thumb, w, h, raw_json)
            )

    @classmethod
    def get_video(cls, video_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves video data by ID from cache or SQLite."""
        cls._ensure_initialized()
        if video_id in cls._videos_cache:
            return cls._videos_cache[video_id]

        with cls._get_connection() as conn:
            cur = conn.execute("SELECT data_json FROM session_videos WHERE video_id = ?", (video_id,))
            row = cur.fetchone()
            if row:
                try:
                    data = json.loads(row["data_json"])
                    cls._videos_cache[video_id] = data
                    return data
                except Exception:
                    return None
        return None

    @classmethod
    def has_video(cls, video_id: str) -> bool:
        cls._ensure_initialized()
        if video_id in cls._videos_cache:
            return True
        with cls._get_connection() as conn:
            cur = conn.execute("SELECT 1 FROM session_videos WHERE video_id = ?", (video_id,))
            return cur.fetchone() is not None

    @classmethod
    def list_videos(cls) -> List[Dict[str, Any]]:
        cls._ensure_initialized()
        with cls._get_connection() as conn:
            cur = conn.execute("SELECT data_json FROM session_videos ORDER BY updated_at DESC")
            results = []
            for row in cur.fetchall():
                try:
                    results.append(json.loads(row["data_json"]))
                except Exception:
                    pass
            return results

    @classmethod
    def delete_video(cls, video_id: str) -> bool:
        cls._ensure_initialized()
        cls._videos_cache.pop(video_id, None)
        with cls._get_connection() as conn:
            cur = conn.execute("DELETE FROM session_videos WHERE video_id = ?", (video_id,))
            # Cascade clips
            conn.execute("DELETE FROM session_clips WHERE parent_video_id = ?", (video_id,))
            # Clean clips cache
            cls._clips_cache = {cid: c for cid, c in cls._clips_cache.items() if c.get("parent_video_id") != video_id}
            return cur.rowcount > 0

    @classmethod
    def save_clip(cls, clip_id: str, data: Dict[str, Any]) -> None:
        """Saves or updates clip candidate metadata in SQLite and in-memory cache."""
        cls._ensure_initialized()
        cls._clips_cache[clip_id] = data
        raw_json = _json_serialize(data)
        parent_id = str(data.get("parent_video_id", ""))
        title = data.get("title", "")
        start = float(data.get("start_sec", 0.0) or 0.0)
        end = float(data.get("end_sec", 0.0) or 0.0)
        rendered_file = str(data.get("rendered_file", "") or "")

        with cls._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO session_clips (clip_id, parent_video_id, title, start_sec, end_sec, rendered_file, data_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(clip_id) DO UPDATE SET
                    parent_video_id = excluded.parent_video_id,
                    title = excluded.title,
                    start_sec = excluded.start_sec,
                    end_sec = excluded.end_sec,
                    rendered_file = excluded.rendered_file,
                    data_json = excluded.data_json,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (clip_id, parent_id, title, start, end, rendered_file, raw_json)
            )

    @classmethod
    def get_clip(cls, clip_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves clip data by ID from cache or SQLite."""
        cls._ensure_initialized()
        if clip_id in cls._clips_cache:
            return cls._clips_cache[clip_id]

        with cls._get_connection() as conn:
            cur = conn.execute("SELECT data_json FROM session_clips WHERE clip_id = ?", (clip_id,))
            row = cur.fetchone()
            if row:
                try:
                    data = json.loads(row["data_json"])
                    cls._clips_cache[clip_id] = data
                    return data
                except Exception:
                    return None
        return None

    @classmethod
    def has_clip(cls, clip_id: str) -> bool:
        cls._ensure_initialized()
        if clip_id in cls._clips_cache:
            return True
        with cls._get_connection() as conn:
            cur = conn.execute("SELECT 1 FROM session_clips WHERE clip_id = ?", (clip_id,))
            return cur.fetchone() is not None

    @classmethod
    def list_clips(cls, parent_video_id: Optional[str] = None) -> List[Dict[str, Any]]:
        cls._ensure_initialized()
        with cls._get_connection() as conn:
            if parent_video_id:
                cur = conn.execute(
                    "SELECT data_json FROM session_clips WHERE parent_video_id = ? ORDER BY start_sec ASC",
                    (parent_video_id,)
                )
            else:
                cur = conn.execute("SELECT data_json FROM session_clips ORDER BY updated_at DESC")
            results = []
            for row in cur.fetchall():
                try:
                    results.append(json.loads(row["data_json"]))
                except Exception:
                    pass
            return results

    @classmethod
    def delete_clip(cls, clip_id: str) -> bool:
        cls._ensure_initialized()
        cls._clips_cache.pop(clip_id, None)
        with cls._get_connection() as conn:
            cur = conn.execute("DELETE FROM session_clips WHERE clip_id = ?", (clip_id,))
            return cur.rowcount > 0

    @classmethod
    def clear(cls) -> None:
        """Clears memory and database tables."""
        cls._ensure_initialized()
        cls._videos_cache.clear()
        cls._clips_cache.clear()
        with cls._get_connection() as conn:
            conn.execute("DELETE FROM session_clips")
            conn.execute("DELETE FROM session_videos")


class SessionVideosProxy(MutableMapping):
    """Dict-compatible proxy for ingested_videos backed by SessionStore."""

    def __getitem__(self, key: str) -> Dict[str, Any]:
        item = SessionStore.get_video(key)
        if item is None:
            raise KeyError(key)
        return item

    def __setitem__(self, key: str, value: Dict[str, Any]) -> None:
        SessionStore.save_video(key, value)

    def __delitem__(self, key: str) -> None:
        if not SessionStore.delete_video(key):
            raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        return iter(v.get("video_id", "") for v in SessionStore.list_videos() if "video_id" in v)

    def __len__(self) -> int:
        return len(SessionStore.list_videos())

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, str):
            return False
        return SessionStore.has_video(key)

    def get(self, key: str, default: Any = None) -> Any:
        item = SessionStore.get_video(key)
        return item if item is not None else default


class SessionClipsProxy(MutableMapping):
    """Dict-compatible proxy for discovered_clips backed by SessionStore."""

    def __getitem__(self, key: str) -> Dict[str, Any]:
        item = SessionStore.get_clip(key)
        if item is None:
            raise KeyError(key)
        return item

    def __setitem__(self, key: str, value: Dict[str, Any]) -> None:
        SessionStore.save_clip(key, value)

    def __delitem__(self, key: str) -> None:
        if not SessionStore.delete_clip(key):
            raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        return iter(c.get("clip_id", "") for c in SessionStore.list_clips() if "clip_id" in c)

    def __len__(self) -> int:
        return len(SessionStore.list_clips())

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, str):
            return False
        return SessionStore.has_clip(key)

    def get(self, key: str, default: Any = None) -> Any:
        item = SessionStore.get_clip(key)
        return item if item is not None else default
