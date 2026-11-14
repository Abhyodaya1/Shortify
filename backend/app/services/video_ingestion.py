"""Video Ingestion Service: Handles YouTube URLs and local video files.
Transcribes real speech audio using Groq Whisper (whisper-large-v3-turbo) when subtitles are absent.
"""

from __future__ import annotations
import os
import json
import re
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from uuid import uuid4
import httpx
from dotenv import load_dotenv
from .url_security_validator import URLSecurityValidator, SSRFSecurityError

load_dotenv()

STORAGE_UPLOADS = Path("backend/storage/uploads")
STORAGE_UPLOADS.mkdir(parents=True, exist_ok=True)


class IngestionService:
    """Extracts media, metadata, and real speech transcripts from YouTube or local files."""

    GROQ_API_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
    WHISPER_MODEL = "whisper-large-v3-turbo"

    @classmethod
    def ingest_youtube_url(cls, url: str) -> Dict[str, Any]:
        """Downloads metadata, video stream, and extracts real speech transcripts."""
        import yt_dlp
        from youtube_transcript_api import YouTubeTranscriptApi

        # 0. Deep Multi-Layer SSRF and Protocol Validation
        clean_url, validated_yt_id = URLSecurityValidator.validate_url(url)

        video_id = str(uuid4())[:8]
        out_template = str(STORAGE_UPLOADS / f"yt_{video_id}.%(ext)s")

        # 1. Extract metadata and download video with extractor constraints
        ydl_opts = {
            "format": "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "outtmpl": out_template,
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "allowed_extractors": ["youtube", "youtube:tab"],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(clean_url, download=True)
                title = info.get("title", "YouTube Video")
                duration = info.get("duration", 0)
                thumbnail = info.get("thumbnail", "")
                yt_id = info.get("id", validated_yt_id)
                video_filepath = ydl.prepare_filename(info)
                # In case extension changed
                if not os.path.exists(video_filepath):
                    potential = list(STORAGE_UPLOADS.glob(f"yt_{video_id}.*"))
                    if potential:
                        video_filepath = str(potential[0])
        except Exception as e:
            raise RuntimeError(f"Failed to download YouTube video: {str(e)}")

        # 2. Retrieve transcript with timestamps
        transcript_cues: List[Dict[str, Any]] = []
        if yt_id:
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(yt_id)
                try:
                    t = transcript_list.find_transcript(["en", "en-US", "en-GB", "en-IN", "hi"])
                except Exception:
                    try:
                        t = transcript_list.find_generated_transcript(["en", "en-US", "en-GB", "en-IN", "hi"])
                    except Exception:
                        t = next(iter(transcript_list))
                raw_items = t.fetch()
                for item in raw_items:
                    text = (item.get("text") or "").strip()
                    if text:
                        transcript_cues.append({
                            "start_sec": round(float(item["start"]), 2),
                            "end_sec": round(float(item["start"] + item["duration"]), 2),
                            "duration_sec": round(float(item["duration"]), 2),
                            "text": text,
                        })
            except Exception:
                pass

        # 3. If YouTube captions are missing/unavailable, transcribe real audio directly via Groq Whisper
        if not transcript_cues and os.path.exists(video_filepath):
            transcript_cues = cls.transcribe_media_audio(video_filepath)

        if not transcript_cues:
            raise RuntimeError("No speech detected in audio track. Video must contain spoken dialogue to extract viral shorts.")

        dimensions = cls.get_video_dimensions(video_filepath)

        return {
            "video_id": video_id,
            "source_type": "youtube",
            "url": url,
            "title": title,
            "duration_sec": duration,
            "thumbnail": thumbnail,
            "filepath": str(Path(video_filepath).resolve()),
            "width": dimensions[0],
            "height": dimensions[1],
            "fps": dimensions[2],
            "transcript_cues": transcript_cues,
        }

    @classmethod
    def ingest_local_file(cls, source_path: str, filename: str) -> Dict[str, Any]:
        """Extracts metadata and real speech cues from a local video file."""
        video_id = str(uuid4())[:8]
        dest_path = STORAGE_UPLOADS / f"local_{video_id}_{filename}"
        
        # Copy or save to storage uploads
        if Path(source_path) != dest_path:
            import shutil
            shutil.copy(source_path, dest_path)

        dimensions = cls.get_video_dimensions(str(dest_path))
        duration = cls.get_video_duration(str(dest_path))

        # Check for matching .srt or .vtt in same folder
        base = Path(source_path).with_suffix("")
        cues: List[Dict[str, Any]] = []
        for ext in [".srt", ".vtt", ".json"]:
            sub_file = base.with_suffix(ext)
            if sub_file.exists():
                cues = cls._parse_subtitle_file(str(sub_file))
                break

        # If no subtitle file present, transcribe video audio with Groq Whisper
        if not cues and dest_path.exists():
            cues = cls.transcribe_media_audio(str(dest_path.resolve()))

        if not cues:
            raise RuntimeError("No speech detected in audio track. Video must contain spoken dialogue to extract viral shorts.")

        return {
            "video_id": video_id,
            "source_type": "local",
            "title": filename,
            "duration_sec": duration,
            "thumbnail": "",
            "filepath": str(dest_path.resolve()),
            "width": dimensions[0],
            "height": dimensions[1],
            "fps": dimensions[2],
            "transcript_cues": cues,
        }

    @classmethod
    def transcribe_media_audio(cls, video_filepath: str) -> List[Dict[str, Any]]:
        """Extracts audio track and transcribes with Groq Whisper-large-v3-turbo for millisecond-exact cues."""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set.")

        temp_audio = Path(video_filepath).with_suffix(f".tmp_{uuid4().hex[:6]}.m4a")

        # 1. Try fast stream copy first (< 1s)
        fast_cmd = [
            "ffmpeg", "-y",
            "-i", str(Path(video_filepath).resolve()),
            "-map", "0:a:0",
            "-c:a", "copy",
            str(temp_audio.resolve()),
        ]
        res = subprocess.run(fast_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # If copy failed or size > 24MB, re-encode to compact 32k mono AAC
        if res.returncode != 0 or not temp_audio.exists() or temp_audio.stat().st_size > 24 * 1024 * 1024:
            temp_audio_fallback = Path(video_filepath).with_suffix(f".tmp_{uuid4().hex[:6]}.mp3")
            compact_cmd = [
                "ffmpeg", "-y",
                "-i", str(Path(video_filepath).resolve()),
                "-vn",
                "-ar", "16000",
                "-ac", "1",
                "-b:a", "32k",
                str(temp_audio_fallback.resolve()),
            ]
            subprocess.run(compact_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if temp_audio.exists():
                try:
                    temp_audio.unlink()
                except Exception:
                    pass
            temp_audio = temp_audio_fallback

        try:
            mime_type = "audio/mp4" if temp_audio.suffix == ".m4a" else "audio/mp3"
            with open(temp_audio, "rb") as f:
                files = {"file": (temp_audio.name, f, mime_type)}
                data = {
                    "model": cls.WHISPER_MODEL,
                    "response_format": "verbose_json",
                    "timestamp_granularities[]": ["segment"],
                }
                headers = {"Authorization": f"Bearer {api_key.strip()}"}
                with httpx.Client(timeout=90.0) as client:
                    resp = client.post(cls.GROQ_API_URL, files=files, data=data, headers=headers)

            if resp.status_code != 200:
                raise RuntimeError(f"Groq Whisper transcription returned {resp.status_code}: {resp.text}")

            result = resp.json()
            segments = result.get("segments", [])
            cues: List[Dict[str, Any]] = []

            for seg in segments:
                text = (seg.get("text") or "").strip()
                if text:
                    cues.append({
                        "start_sec": round(float(seg.get("start", 0.0)), 2),
                        "end_sec": round(float(seg.get("end", 0.0)), 2),
                        "duration_sec": round(float(seg.get("end", 0.0)) - float(seg.get("start", 0.0)), 2),
                        "text": text,
                    })
            return cues
        finally:
            if temp_audio.exists():
                try:
                    temp_audio.unlink()
                except Exception:
                    pass

    @staticmethod
    def get_video_dimensions(filepath: str) -> Tuple[int, int, float]:
        """Uses OpenCV to inspect video width, height, and fps."""
        import cv2
        cap = cv2.VideoCapture(filepath)
        if not cap.isOpened():
            return 1920, 1080, 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1920
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 1080
        fps = float(cap.get(cv2.CAP_PROP_FPS)) or 30.0
        cap.release()
        return width, height, fps

    @staticmethod
    def get_video_duration(filepath: str) -> float:
        """Retrieves duration in seconds."""
        import cv2
        cap = cv2.VideoCapture(filepath)
        if not cap.isOpened():
            return 60.0
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        cap.release()
        return float(frame_count / fps) if fps > 0 else 60.0

    @classmethod
    def _parse_subtitle_file(cls, filepath: str) -> List[Dict[str, Any]]:
        from .viral_clipper import DeadAirDetector
        loaded = DeadAirDetector.load_transcript(filepath)
        return [
            {"start_sec": c[0], "end_sec": c[1], "duration_sec": c[1] - c[0], "text": c[2]}
            for c in loaded
        ]
