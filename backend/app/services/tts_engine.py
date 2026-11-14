"""Open-Source Voice Synthesis & Performance Direction Engine.
Implements Role 07 (Voice Director) from shorts_ai_roles_prompt_pack and provides
a pluggable TTS architecture (Kokoro ONNX, Edge-TTS, Remote HTTP) with FFmpeg loudness normalization.
"""

from __future__ import annotations
import os
import json
import asyncio
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional
import httpx
from dotenv import load_dotenv

load_dotenv()

PROMPT_PACK_DIR = Path("shorts_ai_roles_prompt_pack")
MODELS_DIR = Path("backend/models")


class BaseTTSProvider(ABC):
    """Abstract base class for all TTS synthesis backends."""

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice_id: str,
        output_path: str,
        rate_multiplier: float = 1.0,
        settings: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Synthesizes speech audio from text and saves to output_path."""
        pass


class EdgeTTSProvider(BaseTTSProvider):
    """High-fidelity neural TTS using Microsoft Edge open speech endpoints."""

    DEFAULT_VOICE = "en-US-ChristopherNeural"

    VOICES = {
        "christopher": "en-US-ChristopherNeural", # Male, authoritative, documentary
        "guy": "en-US-GuyNeural",                 # Male, casual, energetic
        "jenny": "en-US-JennyNeural",             # Female, clear, professional
        "eric": "en-US-EricNeural",               # Male, conversational
        "aria": "en-US-AriaNeural",               # Female, expressive storytelling
    }

    async def synthesize(
        self,
        text: str,
        voice_id: str = DEFAULT_VOICE,
        output_path: str = "voice.mp3",
        rate_multiplier: float = 1.0,
        settings: Optional[Dict[str, Any]] = None,
    ) -> str:
        import edge_tts

        voice = self.VOICES.get(voice_id.lower(), voice_id)

        # Calculate rate adjustment string e.g. "+5%" or "-10%"
        rate_pct = int(round((rate_multiplier - 1.0) * 100))
        rate_str = f"{rate_pct:+d}%" if rate_pct != 0 else "+0%"

        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        comm = edge_tts.Communicate(text=text, voice=voice, rate=rate_str)
        await comm.save(str(out_path.resolve()))

        return str(out_path.resolve())


class KokoroONNXProvider(BaseTTSProvider):
    """Ultra-compact 82M open-weight Kokoro TTS running locally on ONNX runtime."""

    def __init__(self, model_dir: Optional[str] = None):
        self.model_dir = Path(model_dir) if model_dir else MODELS_DIR / "kokoro"
        self.onnx_path = self.model_dir / "kokoro-v0_19.onnx"
        self.voices_path = self.model_dir / "voices.json"
        self._kokoro = None

    def is_available(self) -> bool:
        return self.onnx_path.exists() and self.voices_path.exists()

    async def synthesize(
        self,
        text: str,
        voice_id: str = "af_sky",
        output_path: str = "voice.wav",
        rate_multiplier: float = 1.0,
        settings: Optional[Dict[str, Any]] = None,
    ) -> str:
        if not self.is_available():
            raise FileNotFoundError(f"Kokoro ONNX weights not found in {self.model_dir}")

        import soundfile as sf
        from kokoro_onnx import Kokoro

        if self._kokoro is None:
            self._kokoro = Kokoro(str(self.onnx_path), str(self.voices_path))

        samples, sample_rate = self._kokoro.create(text, voice=voice_id, speed=rate_multiplier)
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(out_path.resolve()), samples, sample_rate)

        return str(out_path.resolve())


class RemoteTTSProvider(BaseTTSProvider):
    """Connects to any optional external TTS HTTP endpoint."""

    def __init__(self, endpoint_url: Optional[str] = None):
        self.endpoint_url = endpoint_url or os.getenv("TTS_REMOTE_URL")

    async def synthesize(
        self,
        text: str,
        voice_id: str = "default",
        output_path: str = "voice.wav",
        rate_multiplier: float = 1.0,
        settings: Optional[Dict[str, Any]] = None,
    ) -> str:
        if not self.endpoint_url:
            raise ValueError("TTS_REMOTE_URL is not configured.")

        payload = {"text": text, "voice": voice_id, "speed": rate_multiplier}
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(self.endpoint_url, json=payload)

        if resp.status_code != 200:
            raise RuntimeError(f"Remote TTS endpoint returned {resp.status_code}: {resp.text}")

        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(resp.content)

        return str(out_path.resolve())


class VoiceDirectorService:
    """Executes Role 07 (Voice Director) from shorts_ai_roles_prompt_pack."""

    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
    MODEL_DIRECTOR = os.getenv("GROQ_MODEL_FAST", "qwen/qwen3.8-27b")

    @classmethod
    def create_performance_plan(
        cls,
        clip_id: str,
        approved_hook_text: str,
        segment_type: str = "opening",
        channel_niche: str = "Creator Education",
        target_audience: str = "Mobile viewers",
        transcript: str = "",
        transcript_analysis: Optional[Dict[str, Any]] = None,
        tts_provider: str = "EdgeTTS / Kokoro",
        tts_voice_id: str = "en-US-ChristopherNeural",
        target_duration_seconds: float = 2.5,
    ) -> Dict[str, Any]:
        """Renders 07_voice_director prompt and queries LLM for phrasing, pauses, and rate plan."""
        sys_prompt = (PROMPT_PACK_DIR / "07_voice_director" / "system.md").read_text(encoding="utf-8")
        user_template = (PROMPT_PACK_DIR / "07_voice_director" / "user.md").read_text(encoding="utf-8")

        data = {
            "clip_id": clip_id,
            "opening_or_ending": segment_type,
            "channel_niche": channel_niche,
            "target_audience": target_audience,
            "language_locale": "en-US",
            "voice_description": "Authoritative, natural, resonant, documentary pacing",
            "brand_tone": "confident and engaging",
            "emotional_intent": "spark curiosity and emphasize key takeaway",
            "approved_hook_text": approved_hook_text,
            "transcript": transcript,
            "transcript_analysis_json": json.dumps(transcript_analysis or {}),
            "editorial_judge_feedback": "Approved for retention and factual grounding.",
            "tts_provider": tts_provider,
            "tts_voice_id": tts_voice_id,
            "provider_supported_controls": "speaking_rate_multiplier, pause_duration",
            "ssml_support_status": "unknown",
            "target_duration_seconds": str(target_duration_seconds),
            "allowed_speed_range": "0.90x - 1.15x",
            "audio_format": "wav 16kHz mono",
        }

        user_prompt = user_template
        for k, v in data.items():
            user_prompt = user_prompt.replace(f"{{{{{k}}}}}", str(v))

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            # Deterministic fallback voice plan if offline
            return {
                "clip_id": clip_id,
                "segment_type": segment_type,
                "spoken_text": approved_hook_text,
                "performance": {
                    "delivery_style": "confident, clear",
                    "speaking_rate_multiplier": 1.05,
                    "energy": 8,
                },
                "plain_text_fallback": approved_hook_text,
                "estimated_duration_seconds": 2.5,
            }

        payload = {
            "model": cls.MODEL_DIRECTOR,
            "messages": [
                {"role": "system", "content": sys_prompt + "\nOutput strictly valid JSON only."},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": 2048,
            "temperature": 0.2,
        }
        headers = {"Authorization": f"Bearer {api_key.strip()}", "Content-Type": "application/json"}

        try:
            with httpx.Client(timeout=25.0) as client:
                resp = client.post(cls.GROQ_API_URL, json=payload, headers=headers)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
        except Exception:
            pass

        return {
            "clip_id": clip_id,
            "segment_type": segment_type,
            "spoken_text": approved_hook_text,
            "performance": {"delivery_style": "confident", "speaking_rate_multiplier": 1.05},
            "plain_text_fallback": approved_hook_text,
            "estimated_duration_seconds": 2.5,
        }


class TTSManager:
    """Unified coordinator for voice direction, synthesis, and loudness normalization."""

    @classmethod
    async def generate_voiceover_hook(
        cls,
        clip_id: str,
        hook_text: str,
        segment_type: str = "opening",  # "opening" or "ending"
        output_dir: str = "backend/storage/renders",
        voice_id: str = "en-US-ChristopherNeural",
        provider_name: str = "auto",  # "auto", "kokoro", "edge_tts", "remote"
        transcript: str = "",
        transcript_analysis: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Runs Voice Director (Role 07), synthesizes audio, normalizes loudness, and measures duration."""
        if not hook_text or not hook_text.strip():
            return {"success": False, "reason": "Empty hook text"}

        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        raw_output_wav = out_dir / f"raw_{segment_type}_voice.wav"
        final_normalized_wav = out_dir / f"{segment_type}_voice.wav"
        plan_json_path = out_dir / f"{segment_type}_voice_plan.json"

        # 1. Run Role 07 Voice Director
        raw_plan = VoiceDirectorService.create_performance_plan(
            clip_id=clip_id,
            approved_hook_text=hook_text,
            segment_type=segment_type,
            transcript=transcript,
            transcript_analysis=transcript_analysis,
            tts_voice_id=voice_id,
        )
        if isinstance(raw_plan, str):
            try:
                plan = json.loads(raw_plan)
            except Exception:
                plan = {"spoken_text": hook_text, "performance": {"speaking_rate_multiplier": 1.05}}
        else:
            plan = raw_plan

        with open(plan_json_path, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=2)

        rate_multiplier = float(plan.get("performance", {}).get("speaking_rate_multiplier", 1.05))
        text_to_speak = plan.get("spoken_text") or plan.get("plain_text_fallback") or hook_text

        # 2. Select TTS Provider
        provider: BaseTTSProvider
        kokoro = KokoroONNXProvider()

        if provider_name == "kokoro" and kokoro.is_available():
            provider = kokoro
        elif provider_name == "remote" and os.getenv("TTS_REMOTE_URL"):
            provider = RemoteTTSProvider()
        else:
            # Default to high-quality EdgeTTS
            provider = EdgeTTSProvider()

        # 3. Synthesize Audio
        try:
            await provider.synthesize(
                text=text_to_speak,
                voice_id=voice_id,
                output_path=str(raw_output_wav),
                rate_multiplier=rate_multiplier,
            )
        except Exception as e:
            return {
                "success": False,
                "error": f"TTS synthesis failed: {e}",
                "hook_text": hook_text,
                "plan": plan,
            }

        # 4. Apply EBU R128 Loudness Normalization & Convert to 16kHz Mono WAV via FFmpeg
        norm_cmd = [
            "ffmpeg", "-y",
            "-i", str(raw_output_wav.resolve()),
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-ar", "16000",
            "-ac", "1",
            "-c:a", "pcm_s16le",
            str(final_normalized_wav.resolve()),
        ]
        try:
            norm_res = subprocess.run(norm_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
        except subprocess.TimeoutExpired:
            norm_res = subprocess.CompletedProcess(norm_cmd, returncode=1)
        if norm_res.returncode != 0:
            # Fallback to raw output if normalization filter hit an edge-case
            if raw_output_wav.exists():
                raw_output_wav.rename(final_normalized_wav)

        # Clean temporary raw file
        if raw_output_wav.exists() and final_normalized_wav.exists() and raw_output_wav != final_normalized_wav:
            try:
                raw_output_wav.unlink()
            except Exception:
                pass

        # 5. Measure exact generated duration with FFprobe
        actual_duration = cls.measure_audio_duration(str(final_normalized_wav))

        return {
            "success": True,
            "segment_type": segment_type,
            "audio_file": str(final_normalized_wav.resolve()),
            "actual_duration_seconds": actual_duration,
            "target_duration_seconds": plan.get("estimated_duration_seconds", 2.5),
            "voice_plan": plan,
            "provider_used": provider.__class__.__name__,
            "voice_id": voice_id,
            "spoken_text": text_to_speak,
        }

    @staticmethod
    def measure_audio_duration(audio_path: str) -> float:
        """Measures exact duration in seconds using FFprobe."""
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(Path(audio_path).resolve()),
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
            if res.returncode == 0:
                return round(float(res.stdout.strip()), 3)
        except Exception:
            pass
        return 0.0

