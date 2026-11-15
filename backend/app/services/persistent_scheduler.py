"""Persistent Scheduler & YouTube Upload Manager
Manages video upload jobs, automated publishing queues, and quota-safe execution.
Backed by local SQLite for 100% resilient persistence across server restarts.
"""

from __future__ import annotations
import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from .token_encryption_service import TokenEncryptionService, TokenDecryptionError

DB_DIR = Path("backend/storage")
if not DB_DIR.exists():
    DB_DIR = Path("storage")
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "scheduler.db"


class PersistentScheduler:
    """Handles durable scheduling of YouTube Shorts uploads and autopilot rules."""

    @classmethod
    def _get_connection(cls) -> sqlite3.Connection:
        conn = sqlite3.connect(str(DB_PATH.resolve()))
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def init_db(cls):
        """Initializes the SQLite schema for local persistence."""
        with cls._get_connection() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS connected_channels (
                channel_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                channel_title TEXT NOT NULL,
                custom_url TEXT,
                thumbnail_url TEXT,
                subscriber_count INTEGER DEFAULT 0,
                video_count INTEGER DEFAULT 0,
                is_sandbox BOOLEAN DEFAULT 0,
                refresh_token TEXT,
                access_token TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS scheduled_uploads (
                job_id TEXT PRIMARY KEY,
                clip_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                tags TEXT,
                video_file_path TEXT NOT NULL,
                thumbnail_url TEXT,
                target_channel_id TEXT NOT NULL,
                scheduled_time TEXT NOT NULL,
                visibility TEXT DEFAULT 'unlisted',
                status TEXT DEFAULT 'scheduled', -- 'scheduled', 'rendering', 'ready', 'uploading', 'published', 'failed'
                youtube_video_id TEXT,
                youtube_url TEXT,
                error_message TEXT,
                quota_cost INTEGER DEFAULT 1600,
                created_at TEXT NOT NULL,
                published_at TEXT
            );

            CREATE TABLE IF NOT EXISTS autopilot_config (
                user_id TEXT PRIMARY KEY,
                enabled BOOLEAN DEFAULT 0,
                frequency_per_day INTEGER DEFAULT 1,
                preferred_time TEXT DEFAULT '18:00',
                default_visibility TEXT DEFAULT 'unlisted',
                default_channel_id TEXT,
                auto_tags TEXT
            );
            """)
            try:
                conn.execute("ALTER TABLE connected_channels ADD COLUMN refresh_token TEXT")
            except Exception:
                pass
            try:
                conn.execute("ALTER TABLE connected_channels ADD COLUMN access_token TEXT")
            except Exception:
                pass
            try:
                conn.execute("ALTER TABLE scheduled_uploads ADD COLUMN retry_count INTEGER DEFAULT 0")
            except Exception:
                pass
            try:
                conn.execute("ALTER TABLE scheduled_uploads ADD COLUMN max_retries INTEGER DEFAULT 3")
            except Exception:
                pass
            try:
                conn.execute("ALTER TABLE scheduled_uploads ADD COLUMN locked_at TEXT")
            except Exception:
                pass
            try:
                conn.execute("ALTER TABLE autopilot_config ADD COLUMN emergency_stop BOOLEAN DEFAULT 0")
            except Exception:
                pass

        # Migrate any existing legacy plaintext tokens to AES-256-GCM
        try:
            TokenEncryptionService.migrate_scheduler_db(DB_PATH)
        except Exception as e:
            import logging
            logging.getLogger("persistent_scheduler").error(f"[Security] Token migration error: {e}")

    @classmethod
    def get_channel_status(cls, user_id: str = "default_user") -> Optional[Dict[str, Any]]:
        cls.init_db()
        with cls._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM connected_channels WHERE user_id = ? LIMIT 1", (user_id,))
            row = cur.fetchone()
            if row:
                res = dict(row)
                ch_id = res.get("channel_id", "")
                try:
                    if res.get("refresh_token"):
                        res["refresh_token"] = TokenEncryptionService.decrypt_token(res["refresh_token"], ch_id)
                    if res.get("access_token"):
                        res["access_token"] = TokenEncryptionService.decrypt_token(res["access_token"], ch_id)
                except TokenDecryptionError:
                    res["status"] = "reauth_required"
                    res["refresh_token"] = None
                    res["access_token"] = None
                return res
            return None

    @classmethod
    def connect_sandbox_channel(cls, user_id: str = "default_user") -> Dict[str, Any]:
        """Connects a simulated/sandbox channel for Peak Heist Clips so everything works out of the box."""
        cls.init_db()
        channel_data = {
            "channel_id": "UC_peakheistclips_sandbox",
            "user_id": user_id,
            "channel_title": "Peak Heist Clips",
            "custom_url": "@peakheistclips",
            "thumbnail_url": "https://api.dicebear.com/7.x/bottts/svg?seed=peakheistclips",
            "subscriber_count": 24500,
            "video_count": 14,
            "is_sandbox": 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with cls._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO connected_channels 
            (channel_id, user_id, channel_title, custom_url, thumbnail_url, subscriber_count, video_count, is_sandbox, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                channel_data["channel_id"],
                channel_data["user_id"],
                channel_data["channel_title"],
                channel_data["custom_url"],
                channel_data["thumbnail_url"],
                channel_data["subscriber_count"],
                channel_data["video_count"],
                channel_data["is_sandbox"],
                channel_data["created_at"],
            ))
        return channel_data

    @classmethod
    def disconnect_channel(cls, user_id: str = "default_user"):
        cls.init_db()
        with cls._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM connected_channels WHERE user_id = ?", (user_id,))

    @classmethod
    def schedule_clip_upload(
        cls,
        clip_id: str,
        title: str,
        description: str,
        tags: List[str],
        video_file_path: str,
        scheduled_time: str,
        target_channel_id: str,
        visibility: str = "unlisted",
        thumbnail_url: str = "",
    ) -> Dict[str, Any]:
        cls.init_db()
        from .youtube_uploader import YouTubeUploader
        eff_video_path = video_file_path
        try:
            resolved = YouTubeUploader.resolve_video_file(video_file_path, clip_id=clip_id)
            eff_video_path = str(resolved)
        except Exception:
            pass

        import uuid
        from .timezone_service import TimezoneService

        # Normalize incoming schedule time (naive IST or ISO) to UTC RFC 3339
        try:
            utc_scheduled_time = TimezoneService.to_utc_iso(scheduled_time)
            ist_display = TimezoneService.format_ist_display(utc_scheduled_time)
            ist_iso = TimezoneService.utc_to_ist_iso(utc_scheduled_time)
        except Exception:
            utc_scheduled_time = scheduled_time
            ist_display = scheduled_time
            ist_iso = scheduled_time

        job_id = f"job_{uuid.uuid4().hex[:10]}"
        now_str = datetime.now(timezone.utc).isoformat()
        tags_str = json.dumps(tags)

        with cls._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            INSERT INTO scheduled_uploads
            (job_id, clip_id, title, description, tags, video_file_path, thumbnail_url, target_channel_id, scheduled_time, visibility, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'scheduled', ?)
            """, (
                job_id, clip_id, title, description, tags_str, eff_video_path, thumbnail_url, target_channel_id, utc_scheduled_time, visibility, now_str
            ))

        return {
            "job_id": job_id,
            "clip_id": clip_id,
            "title": title,
            "description": description,
            "tags": tags,
            "scheduled_time": utc_scheduled_time,
            "scheduled_time_utc": utc_scheduled_time,
            "scheduled_time_ist": ist_iso,
            "display_ist": ist_display,
            "status": "scheduled",
            "visibility": visibility,
        }

    @classmethod
    def list_scheduled_uploads(cls, channel_id: Optional[str] = None) -> List[Dict[str, Any]]:
        cls.init_db()
        from .timezone_service import TimezoneService
        with cls._get_connection() as conn:
            cur = conn.cursor()
            if channel_id:
                cur.execute("SELECT * FROM scheduled_uploads WHERE target_channel_id = ? ORDER BY scheduled_time ASC", (channel_id,))
            else:
                cur.execute("SELECT * FROM scheduled_uploads ORDER BY scheduled_time ASC")
            rows = cur.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                try:
                    item["tags"] = json.loads(item["tags"]) if item.get("tags") else []
                except Exception:
                    item["tags"] = []
                # Provide explicit IST fields alongside UTC
                item["scheduled_time_utc"] = item.get("scheduled_time", "")
                try:
                    item["scheduled_time_ist"] = TimezoneService.utc_to_ist_iso(item["scheduled_time"])
                    item["display_ist"] = TimezoneService.format_ist_display(item["scheduled_time"])
                except Exception:
                    item["scheduled_time_ist"] = item.get("scheduled_time", "")
                    item["display_ist"] = item.get("scheduled_time", "")
                results.append(item)
            return results

    @classmethod
    def cancel_scheduled_upload(cls, job_id: str) -> bool:
        cls.init_db()
        with cls._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM scheduled_uploads WHERE job_id = ?", (job_id,))
            return cur.rowcount > 0

    @classmethod
    def save_connected_channel(
        cls,
        user_id: str,
        channel_id: str,
        channel_title: str,
        custom_url: str,
        thumbnail_url: str,
        subscriber_count: int,
        video_count: int,
        refresh_token: Optional[str] = None,
        access_token: Optional[str] = None,
        is_sandbox: bool = False,
    ) -> Dict[str, Any]:
        cls.init_db()
        now_str = datetime.now(timezone.utc).isoformat()
        enc_refresh = TokenEncryptionService.encrypt_token(refresh_token)
        enc_access = TokenEncryptionService.encrypt_token(access_token)
        with cls._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO connected_channels
            (channel_id, user_id, channel_title, custom_url, thumbnail_url, subscriber_count, video_count, is_sandbox, refresh_token, access_token, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                channel_id, user_id, channel_title, custom_url, thumbnail_url,
                subscriber_count, video_count, 1 if is_sandbox else 0,
                enc_refresh, enc_access, now_str
            ))
        return cls.get_channel_status(user_id) or {}

    @classmethod
    def get_job_by_id(cls, job_id: str) -> Optional[Dict[str, Any]]:
        cls.init_db()
        with cls._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM scheduled_uploads WHERE job_id = ?", (job_id,))
            row = cur.fetchone()
            if row:
                res = dict(row)
                try:
                    res["tags"] = json.loads(res["tags"]) if res.get("tags") else []
                except Exception:
                    res["tags"] = []
                res["scheduled_time_utc"] = res.get("scheduled_time", "")
                try:
                    from .timezone_service import TimezoneService
                    res["scheduled_time_ist"] = TimezoneService.utc_to_ist_iso(res["scheduled_time"])
                    res["display_ist"] = TimezoneService.format_ist_display(res["scheduled_time"])
                except Exception:
                    res["scheduled_time_ist"] = res.get("scheduled_time", "")
                    res["display_ist"] = res.get("scheduled_time", "")
                return res
            return None

    @classmethod
    async def trigger_publish(cls, job_id: str) -> Dict[str, Any]:
        """Publishes a video to YouTube (Live upload if real channel, or mock if sandbox)."""
        cls.init_db()
        job = cls.get_job_by_id(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # Check channel connection
        channel = cls.get_channel_status(job.get("user_id", "default_user"))
        is_sandbox = not channel or bool(channel.get("is_sandbox", 1))
        refresh_token = channel.get("refresh_token") if channel else None

        if not is_sandbox and refresh_token:
            # Perform REAL YouTube Data API Resumable Upload!
            from .youtube_uploader import YouTubeUploader
            # Update job status to uploading
            with cls._get_connection() as conn:
                conn.cursor().execute("UPDATE scheduled_uploads SET status = 'uploading' WHERE job_id = ?", (job_id,))

            try:
                resolved_file = YouTubeUploader.resolve_video_file(
                    video_path=job.get("video_file_path", ""),
                    clip_id=job.get("clip_id")
                )
                res = await YouTubeUploader.upload_video(
                    refresh_token=refresh_token,
                    video_path=str(resolved_file),
                    title=job["title"],
                    description=job.get("description", ""),
                    tags=job.get("tags", []),
                    privacy_status=job.get("visibility", "unlisted"),
                    clip_id=job.get("clip_id"),
                )
                now_str = datetime.now(timezone.utc).isoformat()
                with cls._get_connection() as conn:
                    conn.cursor().execute("""
                    UPDATE scheduled_uploads
                    SET status = 'published', youtube_video_id = ?, youtube_url = ?, published_at = ?, video_file_path = ?, error_message = NULL
                    WHERE job_id = ?
                    """, (res["youtube_video_id"], res["youtube_url"], now_str, str(resolved_file), job_id))

                return {
                    "job_id": job_id,
                    "status": "published",
                    "youtube_video_id": res["youtube_video_id"],
                    "youtube_url": res["youtube_url"],
                    "published_at": now_str,
                    "is_live_youtube": True,
                }
            except Exception as e:
                with cls._get_connection() as conn:
                    conn.cursor().execute("""
                    UPDATE scheduled_uploads
                    SET status = 'failed', error_message = ?
                    WHERE job_id = ?
                    """, (str(e), job_id))
                raise e

        # Fallback to sandbox simulation
        return cls.trigger_mock_publish(job_id)

    @classmethod
    def trigger_mock_publish(cls, job_id: str) -> Dict[str, Any]:
        """Simulates successful YouTube publication for sandbox verification."""
        cls.init_db()
        mock_yt_id = f"shorts_{job_id[-8:]}"
        mock_yt_url = f"https://youtube.com/shorts/{mock_yt_id}"
        now_str = datetime.now(timezone.utc).isoformat()

        with cls._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            UPDATE scheduled_uploads
            SET status = 'published', youtube_video_id = ?, youtube_url = ?, published_at = ?
            WHERE job_id = ?
            """, (mock_yt_id, mock_yt_url, now_str, job_id))

        return {
            "job_id": job_id,
            "status": "published",
            "youtube_url": mock_yt_url,
            "published_at": now_str,
        }

    @classmethod
    def get_due_scheduled_jobs(cls, now_iso: Optional[str] = None) -> List[Dict[str, Any]]:
        """Finds all scheduled upload jobs whose scheduled_time is <= current time."""
        cls.init_db()
        current_time = now_iso or datetime.now(timezone.utc).isoformat()
        with cls._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            SELECT * FROM scheduled_uploads
            WHERE status = 'scheduled' AND scheduled_time <= ?
            ORDER BY scheduled_time ASC
            """, (current_time,))
            rows = cur.fetchall()
            return [dict(r) for r in rows]

    @classmethod
    def acquire_job_lock(cls, job_id: str) -> bool:
        """Atomically transitions a job from 'scheduled' to 'uploading' to prevent double-uploads."""
        cls.init_db()
        now_str = datetime.now(timezone.utc).isoformat()
        with cls._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            UPDATE scheduled_uploads
            SET status = 'uploading', locked_at = ?
            WHERE job_id = ? AND status = 'scheduled'
            """, (now_str, job_id))
            return cur.rowcount > 0

    @classmethod
    def record_job_failure(cls, job_id: str, error_msg: str, max_retries: int = 3):
        """Records a job failure and increments retry_count; fails permanently if max retries reached."""
        cls.init_db()
        with cls._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT retry_count, max_retries FROM scheduled_uploads WHERE job_id = ?", (job_id,))
            row = cur.fetchone()
            current_retries = (row["retry_count"] or 0) if row else 0
            limit = (row["max_retries"] or max_retries) if row else max_retries

            new_retries = current_retries + 1
            if new_retries >= limit:
                # Retries exhausted -> mark as permanent failure
                cur.execute("""
                UPDATE scheduled_uploads
                SET status = 'failed', retry_count = ?, error_message = ?
                WHERE job_id = ?
                """, (new_retries, f"[Retries Exhausted] {error_msg}", job_id))
            else:
                # Requeue for retry
                cur.execute("""
                UPDATE scheduled_uploads
                SET status = 'scheduled', retry_count = ?, error_message = ?
                WHERE job_id = ?
                """, (new_retries, f"[Attempt {new_retries}/{limit}] {error_msg}", job_id))

    @classmethod
    def recover_stale_jobs(cls):
        """Resets jobs stuck in 'uploading' status (e.g. from an abrupt server restart) back to 'scheduled'."""
        cls.init_db()
        with cls._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            UPDATE scheduled_uploads
            SET status = 'scheduled',
                error_message = '[Recovered after server restart] Job reset to scheduled'
            WHERE status = 'uploading'
            """)
            recovered_count = cur.rowcount
            if recovered_count > 0:
                print(f"[Worker] Recovered {recovered_count} stale in-flight upload jobs.")

    @classmethod
    def is_emergency_stopped(cls, user_id: str = "default_user") -> bool:
        """Checks if emergency publishing stop is enabled."""
        cls.init_db()
        with cls._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT emergency_stop FROM autopilot_config WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            if row and row["emergency_stop"]:
                return bool(row["emergency_stop"])
            return False

    @classmethod
    def set_emergency_stop(cls, user_id: str = "default_user", stopped: bool = True):
        """Sets or resets emergency stop."""
        cls.init_db()
        with cls._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            INSERT INTO autopilot_config (user_id, emergency_stop)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET emergency_stop = excluded.emergency_stop
            """, (user_id, 1 if stopped else 0))

