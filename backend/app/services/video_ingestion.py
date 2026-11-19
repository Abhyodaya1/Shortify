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
    TARGETED_DOWNLOAD_THRESHOLD_SEC = 900.0  # Videos > 15 minutes use fast metadata-first range ingestion

    @classmethod
    def ingest_youtube_url(cls, url: str) -> Dict[str, Any]:
        """Downloads metadata, video stream, and extracts real speech transcripts.
        For videos > 15 minutes, employs fast metadata & caption-first ingestion with targeted range downloads.
        """
        import yt_dlp
        from youtube_transcript_api import YouTubeTranscriptApi

        # 0. Deep Multi-Layer SSRF and Protocol Validation
        clean_url, validated_yt_id = URLSecurityValidator.validate_url(url)

        video_id = str(uuid4())[:8]

        # 1. Fast metadata extraction WITHOUT downloading video (completes in 1-2s)
        meta_opts = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "allowed_extractors": ["youtube", "youtube:tab"],
        }
        try:
            with yt_dlp.YoutubeDL(meta_opts) as ydl:
                info = ydl.extract_info(clean_url, download=False)
        except Exception as e:
            raise RuntimeError(f"Failed to fetch YouTube metadata: {str(e)}")

        title = info.get("title", "YouTube Video")
        duration = float(info.get("duration", 0) or 0)
        thumbnail = info.get("thumbnail", "")
        yt_id = info.get("id", validated_yt_id)
        width = int(info.get("width") or 1920)
        height = int(info.get("height") or 1080)
        fps = float(info.get("fps") or 30.0)

        # 2. Retrieve transcript with timestamps
        transcript_cues: List[Dict[str, Any]] = []
        if yt_id:
            try:
                if hasattr(YouTubeTranscriptApi, "list_transcripts"):
                    transcript_list = YouTubeTranscriptApi.list_transcripts(yt_id)
                elif hasattr(YouTubeTranscriptApi, "list"):
                    transcript_list = YouTubeTranscriptApi.list(yt_id)
                else:
                    transcript_list = YouTubeTranscriptApi().list(yt_id)

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

        is_long_video = duration > cls.TARGETED_DOWNLOAD_THRESHOLD_SEC or info.get("live_status") in ("is_live", "post_live")
        video_filepath = ""

        # 3. Audio/Video Ingestion Strategy
        if is_long_video:
            # Long video (1h, 10h+, 24h VOD): DO NOT download 20GB video upfront!
            # If captions are missing, download audio-only and chunk for Whisper
            if not transcript_cues:
                temp_audio_out = str(STORAGE_UPLOADS / f"yt_audio_{video_id}.%(ext)s")
                # For long videos (> 1 hour), bound fallback audio download to a 1-hour window (3600s)
                # to prevent downloading 40,000+ HLS live fragments and exhausting bandwidth/rate limits
                max_scan_sec = min(duration, 3600.0) if duration > 3600.0 else duration
                audio_opts = {
                    "format": "bestaudio[ext=m4a]/bestaudio/best",
                    "outtmpl": temp_audio_out,
                    "download_ranges": yt_dlp.utils.download_range_func(None, [(0.0, max_scan_sec)]),
                    "force_keyframes_at_cuts": True,
                    "quiet": True,
                    "no_warnings": True,
                    "noplaylist": True,
                }
                with yt_dlp.YoutubeDL(audio_opts) as ydl:
                    ydl.download([clean_url])
                audio_files = list(STORAGE_UPLOADS.glob(f"yt_audio_{video_id}.*"))
                if audio_files:
                    transcript_cues = cls.transcribe_long_media_audio(str(audio_files[0]))
                    try:
                        audio_files[0].unlink()
                    except Exception:
                        pass
        else:
            # Short video (<= 15 min): Download full video upfront
            out_template = str(STORAGE_UPLOADS / f"yt_{video_id}.%(ext)s")
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
                    ydl.download([clean_url])
                potential = list(STORAGE_UPLOADS.glob(f"yt_{video_id}.*"))
                if potential:
                    video_filepath = str(potential[0].resolve())
                    dims = cls.get_video_dimensions(video_filepath)
                    width, height, fps = dims
            except Exception as e:
                raise RuntimeError(f"Failed to download YouTube video: {str(e)}")

            if not transcript_cues and video_filepath and os.path.exists(video_filepath):
                transcript_cues = cls.transcribe_media_audio(video_filepath)

        if not transcript_cues:
            raise RuntimeError("No speech detected in audio track. Video must contain spoken dialogue to extract viral shorts.")

        return {
            "video_id": video_id,
            "source_type": "youtube",
            "url": clean_url,
            "title": title,
            "duration_sec": duration,
            "thumbnail": thumbnail,
            "filepath": video_filepath,
            "width": width,
            "height": height,
            "fps": fps,
            "transcript_cues": transcript_cues,
            "is_targeted_ranges": is_long_video,
        }

    @classmethod
    def download_clip_section(
        cls,
        url: str,
        start_sec: float,
        end_sec: float,
        clip_id: str,
        pre_pad_sec: float = 1.0,
        post_pad_sec: float = 1.0,
    ) -> str:
        """Downloads only the specified 30-60s range of a YouTube video using HTTP range requests.
        Bypasses downloading multi-hour raw video streams entirely.
        """
        import yt_dlp
        target_path = STORAGE_UPLOADS / f"clip_src_{clip_id}.mp4"
        if target_path.exists() and target_path.stat().st_size > 10000:
            return str(target_path.resolve())

        clean_url, _ = URLSecurityValidator.validate_url(url)
        pad_start = max(0.0, start_sec - pre_pad_sec)
        pad_end = end_sec + post_pad_sec

        temp_out = STORAGE_UPLOADS / f"raw_range_{clip_id}.%(ext)s"
        ydl_opts = {
            "format": "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "outtmpl": str(temp_out),
            "download_ranges": yt_dlp.utils.download_range_func(None, [(pad_start, pad_end)]),
            "force_keyframes_at_cuts": True,
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "allowed_extractors": ["youtube", "youtube:tab"],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([clean_url])

        candidates = list(STORAGE_UPLOADS.glob(f"raw_range_{clip_id}.*"))
        if not candidates:
            raise RuntimeError(f"Failed to download clip range [{start_sec:.2f}-{end_sec:.2f}] for clip {clip_id}")

        raw_downloaded = candidates[0]
        trim_offset = start_sec - pad_start
        trim_duration = end_sec - start_sec

        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{trim_offset:.3f}",
            "-i", str(raw_downloaded),
            "-t", f"{trim_duration:.3f}",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-c:a", "aac",
            str(target_path),
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60)
        try:
            raw_downloaded.unlink()
        except Exception:
            pass

        if not target_path.exists() or target_path.stat().st_size == 0:
            raise RuntimeError(f"FFmpeg trim failed for clip range: {res.stderr}")

        return str(target_path.resolve())

    @classmethod
    def transcribe_long_media_audio(cls, audio_filepath: str, chunk_duration_sec: int = 1800) -> List[Dict[str, Any]]:
        """Splits long audio into 30-minute chunks and transcribes each chunk via Groq Whisper."""
        duration = cls.get_video_duration(audio_filepath)
        if duration <= chunk_duration_sec:
            return cls.transcribe_media_audio(audio_filepath)

        chunk_dir = STORAGE_UPLOADS / f"chunks_{uuid4().hex[:6]}"
        chunk_dir.mkdir(parents=True, exist_ok=True)
        chunk_template = str(chunk_dir / "part_%03d.mp3")

        cmd = [
            "ffmpeg", "-y",
            "-i", str(Path(audio_filepath).resolve()),
            "-vn",
            "-ar", "16000",
            "-ac", "1",
            "-b:a", "32k",
            "-f", "segment",
            "-segment_time", str(chunk_duration_sec),
            chunk_template,
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        parts = sorted(list(chunk_dir.glob("part_*.mp3")))
        all_cues: List[Dict[str, Any]] = []

        for idx, part in enumerate(parts):
            offset_sec = idx * chunk_duration_sec
            try:
                part_cues = cls.transcribe_media_audio(str(part))
                for cue in part_cues:
                    cue["start_sec"] = round(cue["start_sec"] + offset_sec, 2)
                    cue["end_sec"] = round(cue["end_sec"] + offset_sec, 2)
                    all_cues.append(cue)
            finally:
                try:
                    part.unlink()
                except Exception:
                    pass

        try:
            chunk_dir.rmdir()
        except Exception:
            pass

        return all_cues

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
        try:
            res = subprocess.run(fast_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        except subprocess.TimeoutExpired:
            res = subprocess.CompletedProcess(fast_cmd, returncode=1)

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
            try:
                subprocess.run(compact_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
            except subprocess.TimeoutExpired:
                raise RuntimeError("FFmpeg audio compression timed out after 120 seconds.")
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
