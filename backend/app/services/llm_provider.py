"""Modular LLM provider abstraction supporting API-based inference and test mocks."""

from __future__ import annotations
import os
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


class LLMResponse(BaseModel):
    content: str
    parsed_json: Optional[Dict[str, Any]] = None
    model_name: str
    tokens_used: int = 0


class BaseLLMProvider(ABC):
    """Abstract interface for LLM reasoning and multimodal orchestration."""

    @abstractmethod
    async def generate_completion(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        json_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.2,
    ) -> LLMResponse:
        """Generate a text or JSON completion from prompt."""
        pass


class MockLLMProvider(BaseLLMProvider):
    """Deterministic mock provider for unit testing, offline CI/CD, and fast validation."""

    def __init__(self, predefined_json: Optional[Dict[str, Any]] = None):
        self.predefined_json = predefined_json

    async def generate_completion(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        json_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.2,
    ) -> LLMResponse:
        if self.predefined_json:
            return LLMResponse(
                content=json.dumps(self.predefined_json),
                parsed_json=self.predefined_json,
                model_name="mock-deterministic",
                tokens_used=120,
            )

        # Dynamic mock response based on prompt keywords
        if "multicam" in prompt.lower() or "camera" in prompt.lower():
            mock_plan = {
                "title": "Multicam Interview Cut",
                "summary": "Synchronized multicam cut alternating between wide and active speaker",
                "tracks": [
                    {
                        "name": "Camera Video Track",
                        "track_type": "video",
                        "clips": [
                            {"asset_id": "wide_cam.mp4", "start_time_ms": 0, "duration_ms": 4000, "source_in_ms": 0},
                            {"asset_id": "speaker_cam.mp4", "start_time_ms": 4000, "duration_ms": 6000, "source_in_ms": 4000},
                            {"asset_id": "wide_cam.mp4", "start_time_ms": 10000, "duration_ms": 3000, "source_in_ms": 10000},
                        ],
                    },
                    {
                        "name": "Master Audio",
                        "track_type": "audio",
                        "clips": [
                            {"asset_id": "master_audio.wav", "start_time_ms": 0, "duration_ms": 13000, "source_in_ms": 0}
                        ],
                    },
                    {
                        "name": "Captions",
                        "track_type": "caption",
                        "clips": [
                            {"text_content": "Welcome to our discussion", "start_time_ms": 500, "duration_ms": 3000},
                            {"text_content": "Here is the active demonstration", "start_time_ms": 4500, "duration_ms": 4000},
                        ],
                    },
                ],
            }
        else:
            mock_plan = {
                "title": "Autonomous Video Project",
                "summary": "Standard video cut based on user brief",
                "tracks": [
                    {
                        "name": "Main Visuals",
                        "track_type": "video",
                        "clips": [
                            {"asset_id": "source_clip.mp4", "start_time_ms": 0, "duration_ms": 8000, "source_in_ms": 0}
                        ],
                    },
                    {
                        "name": "Title Graphic",
                        "track_type": "caption",
                        "clips": [
                            {"text_content": "Motion GVA Cut", "start_time_ms": 500, "duration_ms": 3000}
                        ],
                    },
                ],
            }

        return LLMResponse(
            content=json.dumps(mock_plan),
            parsed_json=mock_plan,
            model_name="mock-planner-v1",
            tokens_used=185,
        )


class GeminiLLMProvider(BaseLLMProvider):
    """Google Gemini AI Studio provider using the modern google-genai SDK."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        from google import genai
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        self.client = genai.Client(api_key=self.api_key)

    async def generate_completion(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        json_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.2,
    ) -> LLMResponse:
        from google.genai import types

        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=system_instruction,
            response_mime_type="application/json" if json_schema or "JSON" in prompt else None,
        )

        try:
            import asyncio
            response = await asyncio.wait_for(
                self.client.aio.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=config,
                ),
                timeout=8.0,
            )
            content_text = response.text or ""
            parsed = None
            if json_schema or content_text.strip().startswith("{") or content_text.strip().startswith("["):
                try:
                    # Clean potential markdown formatting
                    clean_json = content_text.strip()
                    if clean_json.startswith("```json"):
                        clean_json = clean_json[7:]
                    if clean_json.startswith("```"):
                        clean_json = clean_json[3:]
                    if clean_json.endswith("```"):
                        clean_json = clean_json[:-3]
                    parsed = json.loads(clean_json.strip())
                except Exception:
                    pass

            tokens = 0
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                tokens = getattr(response.usage_metadata, "total_token_count", 0) or 0

            return LLMResponse(
                content=content_text,
                parsed_json=parsed,
                model_name=self.model,
                tokens_used=tokens,
            )
        except Exception as e:
            # Fallback to Mock response if offline or rate-limited
            mock_fallback = MockLLMProvider()
            return await mock_fallback.generate_completion(prompt, system_instruction, json_schema, temperature)


class GroqLLMProvider(BaseLLMProvider):
    """Ultra-fast Groq Cloud inference provider using OpenAI-compatible endpoints."""

    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
    DEFAULT_MODEL = os.getenv("GROQ_MODEL_EDITORIAL", "openai/gpt-oss-20b")
    FAST_MODEL = os.getenv("GROQ_MODEL_FAST", "qwen/qwen3.8-27b")

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model or self.DEFAULT_MODEL

    async def generate_completion(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        json_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.2,
    ) -> LLMResponse:
        import httpx

        headers = {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "Content-Type": "application/json",
        }
        sys_msg = system_instruction or "You are an expert YouTube Shorts editor and strategist."
        if json_schema or "JSON" in prompt:
            sys_msg += "\nReturn strictly valid JSON only."

        models_to_try = [self.model, self.FAST_MODEL, "openai/gpt-oss-120b"]

        async with httpx.AsyncClient(timeout=25.0) as client:
            for m in models_to_try:
                payload = {
                    "model": m,
                    "messages": [
                        {"role": "system", "content": sys_msg},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": temperature,
                    "max_tokens": 4096,
                }
                if json_schema or "JSON" in prompt:
                    payload["response_format"] = {"type": "json_object"}

                try:
                    resp = await client.post(self.GROQ_API_URL, json=payload, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        content_text = data["choices"][0]["message"]["content"]
                        parsed = None
                        try:
                            clean = content_text.strip()
                            if clean.startswith("```json"):
                                clean = clean[7:]
                            if clean.startswith("```"):
                                clean = clean[3:]
                            if clean.endswith("```"):
                                clean = clean[:-3]
                            parsed = json.loads(clean.strip())
                        except Exception:
                            pass

                        tokens = data.get("usage", {}).get("total_tokens", 0)
                        return LLMResponse(
                            content=content_text,
                            parsed_json=parsed,
                            model_name=m,
                            tokens_used=tokens,
                        )
                except Exception:
                    continue

        mock_fallback = MockLLMProvider()
        return await mock_fallback.generate_completion(prompt, system_instruction, json_schema, temperature)


_GEMINI_REACHABLE: Optional[bool] = None


def is_gemini_reachable() -> bool:
    """Fast non-blocking IP socket probe to check internet connectivity without DNS blocking."""
    global _GEMINI_REACHABLE
    if _GEMINI_REACHABLE is not None:
        return _GEMINI_REACHABLE

    if os.getenv("MOCK_LLM") == "1" or os.getenv("OFFLINE_MODE") == "1":
        _GEMINI_REACHABLE = False
        return False

    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.2)
        s.connect(("8.8.8.8", 53))
        s.close()
        _GEMINI_REACHABLE = True
        return True
    except Exception:
        _GEMINI_REACHABLE = False
        return False


def get_llm_provider() -> BaseLLMProvider:
    """Factory creating LLM provider based on configured environment variables."""
    # Priority 1: Groq API (Blazing fast sub-second inference)
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key and groq_key.strip():
        try:
            return GroqLLMProvider(api_key=groq_key.strip())
        except Exception as e:
            print(f"Warning: Failed to initialize Groq provider ({e})")

    # Priority 2: Gemini API
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key and gemini_key.strip() and is_gemini_reachable():
        try:
            return GeminiLLMProvider(api_key=gemini_key.strip())
        except Exception as e:
            print(f"Warning: Failed to initialize Gemini provider ({e}), falling back to Mock provider")

    # Default to robust Mock provider for local safety, offline execution and sandboxed tests
    return MockLLMProvider()

