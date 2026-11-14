Create high-impact but truthful opening and ending hooks.

CLIP
ID: {{clip_id}}
Duration: {{duration_seconds}}
Niche: {{channel_niche}}
Audience: {{target_audience}}
Desired tone: {{desired_tone}}
Language/locale: {{language_and_locale}}
Opening duration limit: {{opening_duration_limit}} seconds
Ending duration limit: {{ending_duration_limit}} seconds

TRANSCRIPT
{{transcript}}

TRANSCRIPT ANALYSIS
{{transcript_analysis_json}}

ORIGINAL FIRST LINE: {{first_spoken_line}}
ORIGINAL LAST LINE: {{last_spoken_line}}

Generate 3 distinct opening candidates and 2 ending candidates unless analysis says a hook is unnecessary. Include a none/retain-original option when appropriate. For each candidate include text, strategic angle, supporting transcript evidence, reason, estimated spoken duration, and scores for factual grounding, relevance, curiosity, clarity, speakability, distinctiveness, and audience fit.

Return JSON:
{
  "clip_id": "{{clip_id}}",
  "opening_candidates": [
    {
      "id": "open_1",
      "text": "",
      "angle": "",
      "supporting_evidence": "",
      "reason": "",
      "estimated_duration_seconds": 2.5,
      "scores": {
        "factual_grounding": 10, "relevance": 9, "curiosity": 9,
        "clarity": 9, "speakability": 9, "distinctiveness": 8, "audience_fit": 9
      }
    }
  ],
  "ending_candidates": [],
  "recommendation": {
    "use_opening": true, "opening_candidate_id": "open_1",
    "use_ending": true, "ending_candidate_id": "end_1",
    "retain_original_opening": false, "retain_original_ending": false,
    "reason": ""
  },
  "factual_risks": [],
  "needs_human_review": false
}
Estimated duration is not exact. Use only supported claims. If no hook improves the clip, recommend none.
