import os
import json
import asyncio
from pathlib import Path
from backend.app.services.tts_engine import VoiceDirectorService, TTSManager, EdgeTTSProvider

def test_voice_director_plan():
    """Tests Role 07 (Voice Director) prompt generation and Groq LLM response."""
    plan_raw = VoiceDirectorService.create_performance_plan(
        clip_id="test_clip_01",
        approved_hook_text="Stop making this mistake if you want your videos to actually get views.",
        segment_type="opening",
        transcript="You need to stop making this mistake when editing.",
    )
    assert plan_raw is not None
    if isinstance(plan_raw, str):
        plan = json.loads(plan_raw)
    else:
        plan = plan_raw

    assert "performance" in plan or "spoken_text" in plan
    assert "speaking_rate_multiplier" in plan.get("performance", {}) or "speaking_rate" in str(plan)
    print("\n[Voice Director Plan] Received valid plan from Role 07:", json.dumps(plan, indent=2)[:300] + "...")

def test_tts_synthesis_and_normalization(tmp_path):
    """Tests audio synthesis using EdgeTTS, loudness normalization, and FFprobe measurement."""
    async def _run():
        hook_text = "Here is the one secret top creators never tell you."
        return await TTSManager.generate_voiceover_hook(
            clip_id="test_clip_tts",
            hook_text=hook_text,
            segment_type="opening",
            output_dir=str(tmp_path),
            voice_id="en-US-ChristopherNeural",
        )

    result = asyncio.run(_run())

    assert result["success"] is True
    audio_path = Path(result["audio_file"])
    assert audio_path.exists()
    assert audio_path.stat().st_size > 1000

    plan_path = tmp_path / "opening_voice_plan.json"
    assert plan_path.exists()

    duration = result["actual_duration_seconds"]
    assert duration > 1.0 and duration < 8.0

    print(f"\n[TTS Synthesis Success] Generated audio: {audio_path.name}")
    print(f"[Audio Duration] {duration:.2f} seconds measured via FFprobe")
    print(f"[Provider Used] {result['provider_used']}")

