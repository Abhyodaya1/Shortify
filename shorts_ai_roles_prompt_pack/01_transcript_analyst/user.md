Analyze this short-form video before hooks, headings, voiceover, or editing are generated.

CLIP
ID: {{clip_id}}
Duration: {{duration_seconds}} seconds
Language: {{language}}
Target audience: {{target_audience}}
Channel niche: {{channel_niche}}
Editorial preferences: {{editorial_preferences}}

SOURCE CONTEXT
{{source_context}}

TRANSCRIPT
{{transcript}}

Identify the strongest truthful narrative opportunity. Do not write hooks.

Return JSON:
{
  "clip_id": "{{clip_id}}",
  "central_idea": "What the clip actually says",
  "key_insight": "Most valuable supported insight",
  "strongest_moment": {"text": "Exact transcript excerpt", "why_it_matters": "Reason"},
  "audience_relevance": "Who should care and why",
  "narrative_structure": {"setup": "", "development": "", "payoff": ""},
  "curiosity_gaps": [],
  "opening_strength": 0,
  "ending_strength": 0,
  "opening_hook_needed": true,
  "ending_hook_needed": true,
  "context_heading_needed": false,
  "self_contained": true,
  "missing_context": [],
  "factual_risks": [],
  "claims_requiring_verification": [],
  "recommended_cut_in": null,
  "recommended_cut_out": null,
  "editorial_direction": "",
  "confidence": 0.0
}
Use scores from 0–10. Never fabricate timestamps. Set unknown values to null.
