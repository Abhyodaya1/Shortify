Compare subtitle text against the audio-derived reference transcript.

CLIP: {{clip_id}}
Track: {{track_type}}
Language: {{language}}
Caption policy: {{caption_policy}}

REFERENCE TRANSCRIPT
{{reference_transcript}}

GENERATED SUBTITLES
{{subtitle_text}}

OPTIONAL UNCERTAIN AUDIO SEGMENTS
{{uncertain_segments}}

Identify every discrepancy. Do not create timestamps or rewrite the speaker's words.

Return JSON:
{
  "clip_id": "{{clip_id}}",
  "track_type": "{{track_type}}",
  "status": "pass",
  "issues": [
    {"subtitle_excerpt": "", "expected_text": "", "error_type": "omission",
     "severity": "major", "reason": "", "requires_audio_review": false}
  ],
  "uncertain_segments": [],
  "summary": {"critical_count": 0, "major_count": 0, "minor_count": 0}
}
Status must be pass, warning, or fail. If reference is uncertain, request audio review. Do not output timestamps.
