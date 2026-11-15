Create high-performance YouTube metadata for this approved Short.

CHANNEL CONTEXT:
Name: {{channel_name}}
Niche: {{channel_niche}}
Audience: {{target_audience}}
Language: {{language}}
Brand voice: {{brand_voice}}

CLIP CONTEXT:
Title / Context: {{video_title}}
Spoken Transcript: {{transcript}}
Central Premise: {{central_idea}}
Opening Hook: {{opening_hook}}
Key Entities / Terms: {{key_terms}}

TASK:
1. Generate 3 compelling title alternatives (direct mobile-safe under 40 chars, curiosity-driven under 60 chars, and contrarian/twist under 60 chars).
2. Generate 1 polished description (2-3 natural, engaging sentences explaining the highlight, followed by 3-5 specific hashtags). Do NOT quote the transcript verbatim. Do NOT use boilerplate like "Key Takeaway from...".
3. Generate 8-15 substantive SEO search tags (plain keywords, no # symbols).
4. Select the recommended title index (0, 1, or 2).

Return strictly JSON:
{
  "clip_id": "{{clip_id}}",
  "titles": [
    {"text": "Short punchy title", "angle": "direct", "accuracy_note": "Grounded in opening thesis"},
    {"text": "Curiosity driven title", "angle": "curiosity-driven", "accuracy_note": "Focuses on central premise"},
    {"text": "Contrarian or twist title", "angle": "twist", "accuracy_note": "Highlights unexpected moment"}
  ],
  "recommended_title_index": 0,
  "description": "Engaging two or three sentence description summarizing the clip's best moment.\n\n#Shorts #SpecificTopic #Keyword",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8"],
  "hashtags": ["#Shorts", "#SpecificTopic", "#Keyword"],
  "metadata_warnings": [],
  "rationale": "High-clarity metadata tailored specifically to this clip."
}
