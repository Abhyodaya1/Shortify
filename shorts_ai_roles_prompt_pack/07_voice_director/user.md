Prepare a professional TTS performance direction for this approved hook. Make it attention-grabbing, natural, clear, and appropriate to the clip.

CLIP / CHANNEL
Clip ID: {{clip_id}}
Segment type: {{opening_or_ending}}
Niche: {{channel_niche}}
Audience: {{target_audience}}
Language/locale: {{language_locale}}
Desired voice description: {{voice_description}}
Brand tone: {{brand_tone}}
Emotional intent: {{emotional_intent}}

APPROVED HOOK TEXT — PRESERVE EXACTLY
{{approved_hook_text}}

SUPPORTING CONTEXT
Transcript: {{transcript}}
Transcript analysis: {{transcript_analysis_json}}
Editorial Judge feedback: {{editorial_judge_feedback}}

TTS CONFIGURATION
Provider: {{tts_provider}}
Voice ID: {{tts_voice_id}}
Supported controls: {{provider_supported_controls}}
SSML support status: {{ssml_support_status}}
Target duration: {{target_duration_seconds}} seconds
Allowed speed range: {{allowed_speed_range}}
Audio format: {{audio_format}}

Decide delivery style, target speaking rate, emphasis, natural micro-pauses, emotional delivery, SSML compatibility, and fallback behavior. Do not change approved spoken words. If text needs editing to fit duration, recommend separately and wait for approval.

Return JSON:
{
  "clip_id": "{{clip_id}}",
  "segment_type": "{{opening_or_ending}}",
  "spoken_text": "{{approved_hook_text}}",
  "performance": {
    "delivery_style": "conversational and confident",
    "emotional_intent": "",
    "energy": 7,
    "speaking_rate_multiplier": 1.0,
    "clarity_priority": "high",
    "voice_characteristics": {"warmth": "medium", "brightness": "medium", "articulation": "crisp but natural"}
  },
  "phrasing": [
    {"text": "Exact phrase", "emphasis": ["meaningful word"], "pause_after_ms": 120, "direction": "Brief performance instruction"}
  ],
  "pronunciation_hints": [],
  "estimated_duration_seconds": 2.8,
  "duration_is_estimate": true,
  "ssml": {"supported": "unknown", "provider_specific": false, "payload": null},
  "plain_text_fallback": "{{approved_hook_text}}",
  "provider_payload": null,
  "unsupported_controls": [],
  "duration_warning": null,
  "requires_text_edit_approval": false,
  "recommended_audio_checks": ["No clipping", "Natural pause timing", "Clear consonants", "No rushed final word"]
}

`spoken_text` must remain exact. Use only listed provider controls. Measure actual audio duration after synthesis. Do not fabricate audio-quality results.
