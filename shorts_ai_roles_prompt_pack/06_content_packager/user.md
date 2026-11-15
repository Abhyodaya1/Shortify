Package this YouTube Short using dynamic content understanding and Jake Schincariol's YouTube creator skills.

INPUT CONTEXT:
Source Video Title: {{video_title}}
Selected Clip Spoken Transcript: {{transcript}}
Clip Time Boundaries: {{start_time}} - {{end_time}}
Central Idea / Core Subject: {{central_idea}}
Opening Hook: {{opening_hook}}
Visual Headline / Text Overlay: {{visual_headline}}

JAKE SCHINCARIOL SKILL GUIDANCE:
{{skill_guidance}}

TASK:
1. Infer the true content type and subject matter (e.g. music performance, reaction, podcast/interview, documentary, gaming, tutorial, comedy/storytelling) strictly from the source title and transcript evidence.
2. Generate 5 distinct title candidates exploring different angles (Curiosity, Direct Subject Identification, Compelling Moment / Surprise, Memorable Statement / Quote, Contextual / Benefit / Search-Optimized).
3. Select the best recommended title index (0 to 4) and provide a concise rationale.
4. Craft an original, natural description (50–120 words). The first two lines MUST act as the search snippet answering real search queries. Include 3–5 hyper-relevant hashtags at the end (including #Shorts).
5. Generate up to 15 substantive plain-text SEO search tags for disambiguation (artist, subject, title variations, key queries; no '#' symbols).
6. Provide an opening hook grounded in the actual content.

Return strictly valid JSON matching this schema:
{
  "clip_id": "{{clip_id}}",
  "inferred_content_type": "string",
  "inferred_content_understanding": "string",
  "metadata_evidence": ["evidence point 1", "evidence point 2"],
  "titles": [
    {"text": "Candidate 1", "angle": "curiosity", "accuracy_note": "Grounded explanation"},
    {"text": "Candidate 2", "angle": "direct", "accuracy_note": "Grounded explanation"},
    {"text": "Candidate 3", "angle": "surprise_or_compelling", "accuracy_note": "Grounded explanation"},
    {"text": "Candidate 4", "angle": "memorable_statement", "accuracy_note": "Grounded explanation"},
    {"text": "Candidate 5", "angle": "search_optimized", "accuracy_note": "Grounded explanation"}
  ],
  "recommended_title_index": 0,
  "title_rationale": "Why this title wins the search snippet and feed placement.",
  "description": "First two lines act as the search snippet for real search queries.\n\nSupporting details and context about what is actually happening.\n\n#Shorts #Subject1 #Subject2",
  "hashtags": ["#Shorts", "#Subject1", "#Subject2"],
  "tags": ["entity1", "entity2", "query variation", "song or subject", "artist or speaker"],
  "opening_hook": "Attention-grabbing opening hook based on actual spoken content",
  "skill_guidance_used": ["yt-seo: search snippet & disambiguation tags", "yt-package: 40/60 char cutoffs & entity primacy"]
}
