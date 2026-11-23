"""Persistent Background Worker Daemon for Scheduled YouTube Publishing.
Polls SQLite scheduled queue, handles atomic job locking, retries, and recoverability across restarts.
"""

from __future__ import annotations
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from .persistent_scheduler import PersistentScheduler

logger = logging.getLogger("background_worker")


class BackgroundPublishWorker:
    """Continuous background daemon that dispatches due scheduled YouTube uploads."""

    _instance: Optional[BackgroundPublishWorker] = None

    def __init__(self, poll_interval_seconds: float = 15.0):
        self.poll_interval = poll_interval_seconds
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self._last_poll: Optional[str] = None
        self._jobs_processed = 0

    @classmethod
    def get_instance(cls) -> BackgroundPublishWorker:
        if cls._instance is None:
            cls._instance = BackgroundPublishWorker()
        return cls._instance

    async def start(self):
        """Starts the background worker daemon."""
        if self.is_running:
            return

        self.is_running = True
        # Recover any jobs that were interrupted by a server restart/crash
        try:
            PersistentScheduler.recover_stale_jobs()
        except Exception as e:
            logger.error(f"[Worker] Error recovering stale jobs on startup: {e}")

        self._task = asyncio.create_task(self._worker_loop())
        logger.info("[Worker] Background YouTube Publishing Worker started.")

    async def stop(self):
        """Gracefully stops the worker daemon."""
        if not self.is_running:
            return

        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("[Worker] Background YouTube Publishing Worker stopped.")

    async def _worker_loop(self):
        """Main periodic polling loop."""
        while self.is_running:
            try:
                now_str = datetime.now(timezone.utc).isoformat()
                self._last_poll = now_str

                # 1. Check emergency stop
                if PersistentScheduler.is_emergency_stopped("default_user"):
                    logger.debug("[Worker] Emergency stop active. Pausing publishing.")
                    await asyncio.sleep(self.poll_interval)
                    continue

                # 2. Query due scheduled uploads
                due_jobs = PersistentScheduler.get_due_scheduled_jobs(now_str)

                for job in due_jobs:
                    job_id = job["job_id"]
                    # 3. Atomically acquire job lock to prevent race conditions & duplicate uploads
                    if not PersistentScheduler.acquire_job_lock(job_id):
                        continue

                    logger.info(f"[Worker] Publishing due job {job_id} ('{job.get('title')}')")
                    try:
                        # 4. Trigger publish (resumable live upload if real channel, or mock if sandbox)
                        res = await PersistentScheduler.trigger_publish(job_id)
                        self._jobs_processed += 1
                        logger.info(f"[Worker] Job {job_id} published successfully! Video: {res.get('youtube_url')}")
                    except Exception as upload_err:
                        is_token_expired = "invalid_grant" in str(upload_err) or "expired" in str(upload_err).lower()
                        if is_token_expired:
                            logger.warning(f"[Worker] Google OAuth session expired for job {job_id}. Pausing live uploads until re-authorized.")
                            PersistentScheduler.mark_channel_token_expired("default_user")
                        else:
                            logger.error(f"[Worker] Job {job_id} upload failed: {upload_err}")
                        PersistentScheduler.record_job_failure(job_id, str(upload_err))

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Worker] Unexpected loop exception: {e}")

            await asyncio.sleep(self.poll_interval)

    def get_status(self) -> Dict[str, Any]:
        """Returns the live status of the worker daemon."""
        return {
            "is_running": self.is_running,
            "poll_interval_seconds": self.poll_interval,
            "last_poll_at": self._last_poll,
            "jobs_processed": self._jobs_processed,
            "emergency_stop": PersistentScheduler.is_emergency_stopped("default_user"),
        }

