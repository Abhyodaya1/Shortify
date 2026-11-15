"""Indian Standard Time (IST — Asia/Kolkata) Timezone Engine.
Provides strict timezone-aware conversions, future validation, and formatting conforming to Parts D & E.
"""

from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Dict, Any, List
from zoneinfo import ZoneInfo

IST_TZ = ZoneInfo("Asia/Kolkata")
IST = IST_TZ
UTC_TZ = timezone.utc


class TimezoneService:
    """Official Timezone Engine for Shortify (Source of Truth: Asia/Kolkata)."""

    TIMEZONE_NAME = "Asia/Kolkata"
    TIMEZONE_DISPLAY = "Indian Standard Time (IST — Asia/Kolkata)"

    @classmethod
    def now_ist(cls) -> datetime:
        """Returns the current instant in Asia/Kolkata timezone."""
        return datetime.now(IST_TZ)

    @classmethod
    def now_utc(cls) -> datetime:
        """Returns the current instant in UTC."""
        return datetime.now(UTC_TZ)

    @classmethod
    def parse_to_utc(cls, time_input: str) -> datetime:
        """Parses an input time string and converts to a timezone-aware UTC datetime.
        If the input string is naive (e.g. '2026-11-20T18:30'), it is localized to Asia/Kolkata.
        If it contains a timezone offset or 'Z', it is parsed timezone-aware and converted to UTC.
        """
        clean_str = time_input.strip()
        # Handle trailing Z
        if clean_str.endswith("Z"):
            clean_str = clean_str[:-1] + "+00:00"

        dt = datetime.fromisoformat(clean_str)
        if dt.tzinfo is None:
            # Naive string -> strictly localize to Asia/Kolkata
            dt_ist = dt.replace(tzinfo=IST_TZ)
            return dt_ist.astimezone(UTC_TZ)
        else:
            return dt.astimezone(UTC_TZ)

    @classmethod
    def to_utc_iso(cls, time_input: str) -> str:
        """Returns RFC 3339 formatted UTC string: YYYY-MM-DDTHH:MM:SSZ."""
        utc_dt = cls.parse_to_utc(time_input)
        return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    @classmethod
    def utc_to_ist(cls, utc_dt_or_str: datetime | str) -> datetime:
        """Converts a UTC datetime or ISO string to an Asia/Kolkata datetime."""
        if isinstance(utc_dt_or_str, str):
            utc_dt = cls.parse_to_utc(utc_dt_or_str)
        else:
            if utc_dt_or_str.tzinfo is None:
                utc_dt = utc_dt_or_str.replace(tzinfo=UTC_TZ)
            else:
                utc_dt = utc_dt_or_str.astimezone(UTC_TZ)
        return utc_dt.astimezone(IST_TZ)

    @classmethod
    def utc_to_ist_iso(cls, utc_dt_or_str: datetime | str) -> str:
        """Converts UTC datetime or ISO string to Asia/Kolkata ISO 8601 string (+05:30)."""
        dt_ist = cls.utc_to_ist(utc_dt_or_str)
        return dt_ist.isoformat()

    @classmethod
    def format_ist_display(cls, time_input: str | datetime) -> str:
        """Formats for user display: '20 Nov 2026, 06:30 PM (IST — Asia/Kolkata)'."""
        dt_ist = cls.utc_to_ist(time_input) if isinstance(time_input, str) else time_input.astimezone(IST_TZ)
        return dt_ist.strftime("%d %b %Y, %I:%M %p (IST — Asia/Kolkata)")

    @classmethod
    def validate_future_ist(
        cls,
        time_input: str,
        min_lead_seconds: int = 30,
        min_minutes_ahead: Optional[int] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Validates that the scheduled time is strictly in the future compared to current IST instant."""
        if min_minutes_ahead is not None:
            min_lead_seconds = min_minutes_ahead * 60
        try:
            utc_dt = cls.parse_to_utc(time_input)
            now_utc = cls.now_utc()
            if utc_dt <= now_utc + timedelta(seconds=min_lead_seconds):
                diff_sec = (utc_dt - now_utc).total_seconds()
                if diff_sec <= 0:
                    return False, "Scheduled time cannot be in the past (must be in the future)."
                return False, f"Scheduled time must be at least {min_lead_seconds} seconds in the future."
            return True, None
        except Exception as e:
            return False, f"Invalid date/time format: {e}"

    @classmethod
    def generate_bulk_ist_schedule(
        cls,
        start_time_ist: str = "",
        interval_minutes: int = 30,
        count: int = 0,
        start_ist: str = "",
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """Generates dynamic IST timestamps for any number of selected Shorts."""
        effective_start = start_time_ist or start_ist or kwargs.get("start", "")
        if count <= 0 or not effective_start:
            return []

        base_utc = cls.parse_to_utc(effective_start)
        interval = timedelta(minutes=interval_minutes)

        schedule_entries = []
        for i in range(count):
            item_utc = base_utc + (interval * i)
            item_ist = item_utc.astimezone(IST_TZ)
            utc_iso_str = item_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
            ist_iso_str = item_ist.isoformat()
            schedule_entries.append({
                "sequence_index": i + 1,
                "utc_iso": utc_iso_str,
                "scheduled_time_utc": utc_iso_str,
                "scheduled_time_ist_iso": ist_iso_str,
                "display_ist": item_ist.strftime("%d %b %Y, %I:%M %p (IST — Asia/Kolkata)"),
                "time_only_ist": item_ist.strftime("%I:%M %p"),
                "date_only_ist": item_ist.strftime("%d %b %Y"),
                "timezone": cls.TIMEZONE_NAME,
            })
        return schedule_entries
        return schedule_entries
