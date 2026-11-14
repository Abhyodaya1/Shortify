Create mobile-first visual headings for this Short.

CLIP: {{clip_id}}
Niche: {{channel_niche}}
Audience: {{target_audience}}
Brand voice: {{brand_voice}}
Language: {{language}}
Visual style: {{visual_style}}

TRANSCRIPT
{{transcript}}

ANALYSIS
{{transcript_analysis_json}}

APPROVED VOICEOVER
Opening: {{approved_opening_hook}}
Ending: {{approved_ending_hook}}

Generate 3 opening headline options, up to 2 context headings only if they add clarity, and 3 closing headline options. Complement, do not copy, the voiceover.

Return JSON:
{
  "clip_id": "{{clip_id}}",
  "opening": [
    {"id": "headline_open_1", "text": "", "line_breaks": [], "emphasis_word": "",
     "why_it_works": "", "scores": {"clarity": 9, "relevance": 9, "readability": 9, "distinctiveness": 8}}
  ],
  "context": [],
  "closing": [],
  "recommendations": {"opening_id": "headline_open_1", "context_id": null, "closing_id": null},
  "no_heading_reason": null
}
Do not invent facts or repeat the hook.
