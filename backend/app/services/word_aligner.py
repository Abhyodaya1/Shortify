"""Word-Level Acoustic Alignment Engine using Groq Whisper-large-v3-turbo.
Extracts audio tracks, derives millisecond-accurate word timestamps, handles silence pauses,
and persists validated transcript.json and word_alignment.json artifacts.
"""

from __future__ import annotations
import os
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
import httpx
from dotenv import load_dotenv
from .cache_service import ContentCacheService

load_dotenv()


class WordAlignmentValidationError(Exception):
    """Raised when derived word timestamps fail consistency or ordering validation."""
    pass


class WordAligner:
    """Derives and validates millisecond-accurate word timestamps from audio waveforms."""

    GROQ_API_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
    WHISPER_MODEL = "whisper-large-v3-turbo"

    @classmethod
    def extract_clip_audio(
        cls,
        source_media_path: str,
        start_sec: float,
        end_sec: float,
        output_wav_path: str,
    ) -> str:
        """Extracts a normalized 16kHz mono WAV segment from source video or audio."""
        out_path = Path(output_wav_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        duration = max(0.5, end_sec - start_sec)

        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{start_sec:.3f}",
            "-i", str(Path(source_media_path).resolve()),
            "-t", f"{duration:.3f}",
            "-vn",
            "-ar", "16000",
            "-ac", "1",
            "-c:a", "pcm_s16le",
            str(out_path.resolve()),
        ]

        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=180)
        except subprocess.TimeoutExpired:
            raise RuntimeError("FFmpeg audio extraction timed out after 180 seconds.")
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg audio extraction failed: {res.stderr[-300:]}")

        return str(out_path.resolve())

    @classmethod
    def align_clip(
        cls,
        source_media_path: str,
        start_sec: float,
        end_sec: float,
        output_dir: str,
        clip_id: str = "clip",
    ) -> Dict[str, Any]:
        """Runs acoustic word alignment on a clip and writes transcript.json & word_alignment.json."""
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        audio_wav = out_dir / "audio.wav"
        cls.extract_clip_audio(source_media_path, start_sec, end_sec, str(audio_wav))

        # Check multi-dimensional acoustic cache before remote API call
        audio_bytes = audio_wav.read_bytes()
        cache_key = ContentCacheService.compute_whisper_cache_key(
            audio_bytes=audio_bytes,
            model_id=cls.WHISPER_MODEL,
            language="auto",
            temperature=0.0,
        )
        cached_result = ContentCacheService.get(cache_key)
        if cached_result is not None:
            raw_result = cached_result
        else:
            # Perform Whisper word alignment
            raw_result = cls._transcribe_with_groq(str(audio_wav))
            ContentCacheService.set(
                cache_key=cache_key,
                cache_type="whisper",
                content=raw_result,
                metadata={"clip_id": clip_id, "duration": end_sec - start_sec},
            )

        # Validate and clean word/segment timelines
        validated_data = cls._process_and_validate(raw_result, expected_duration=end_sec - start_sec)

        # Persist structured artifacts
        transcript_path = out_dir / "transcript.json"
        with open(transcript_path, "w", encoding="utf-8") as f:
            json.dump(validated_data["transcript"], f, indent=2)

        alignment_path = out_dir / "word_alignment.json"
        with open(alignment_path, "w", encoding="utf-8") as f:
            json.dump(validated_data["words"], f, indent=2)

        return {
            "clip_id": clip_id,
            "audio_path": str(audio_wav.resolve()),
            "transcript_path": str(transcript_path.resolve()),
            "word_alignment_path": str(alignment_path.resolve()),
            "full_text": validated_data["full_text"],
            "words": validated_data["words"],
            "segments": validated_data["transcript"]["segments"],
            "total_words": len(validated_data["words"]),
            "silence_gaps": validated_data["silence_gaps"],
        }

    @classmethod
    def _transcribe_with_groq(cls, wav_path: str) -> Dict[str, Any]:
        """Calls Groq whisper-large-v3-turbo with verbose_json and word timestamp granularity."""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set.")

        with open(wav_path, "rb") as f:
            files = {"file": (Path(wav_path).name, f, "audio/wav")}
            data = {
                "model": cls.WHISPER_MODEL,
                "response_format": "verbose_json",
                "timestamp_granularities[]": ["word", "segment"],
            }
            headers = {"Authorization": f"Bearer {api_key.strip()}"}

            with httpx.Client(timeout=30.0) as client:
                resp = client.post(cls.GROQ_API_URL, files=files, data=data, headers=headers)

        if resp.status_code != 200:
            raise RuntimeError(f"Groq Whisper API returned {resp.status_code}: {resp.text}")

        return resp.json()

    @classmethod
    def _process_and_validate(cls, raw: Dict[str, Any], expected_duration: float) -> Dict[str, Any]:
        """Validates timestamp ordering, strips whitespace, detects pauses, and formats outputs."""
        full_text = (raw.get("text") or "").strip()
        raw_words = raw.get("words", [])
        raw_segments = raw.get("segments", [])

        clean_words: List[Dict[str, Any]] = []
        silence_gaps: List[Dict[str, Any]] = []
        prev_end = 0.0

        for idx, w in enumerate(raw_words):
            word_str = w.get("word", "").strip()
            if not word_str or word_str == ".":
                continue

            start_t = max(0.0, float(w.get("start", 0.0)))
            end_t = max(start_t + 0.05, float(w.get("end", start_t + 0.1)))

            # Monotonic ordering check
            if start_t < prev_end - 0.15:
                # Slight backward drift recovery
                start_t = prev_end

            # Check for audible silence gap between words (> 400ms)
            if start_t - prev_end > 0.40 and idx > 0:
                silence_gaps.append({
                    "after_word": clean_words[-1]["word"] if clean_words else "",
                    "before_word": word_str,
                    "gap_start": round(prev_end, 3),
                    "gap_end": round(start_t, 3),
                    "duration_sec": round(start_t - prev_end, 3),
                })

            clean_words.append({
                "word_index": len(clean_words),
                "word": word_str,
                "start": round(start_t, 3),
                "end": round(end_t, 3),
                "duration": round(end_t - start_t, 3),
            })
            prev_end = end_t

        # Build clean segments
        clean_segments = []
        for s in raw_segments:
            seg_text = s.get("text", "").strip()
            if not seg_text:
                continue
            clean_segments.append({
                "id": s.get("id", len(clean_segments)),
                "start": round(float(s.get("start", 0.0)), 3),
                "end": round(float(s.get("end", 0.0)), 3),
                "text": seg_text,
            })

        transcript_data = {
            "full_text": full_text,
            "duration": round(expected_duration, 3),
            "language": raw.get("language", "en"),
            "segments": clean_segments,
        }

        return {
            "full_text": full_text,
            "transcript": transcript_data,
            "words": clean_words,
            "silence_gaps": silence_gaps,
        }

