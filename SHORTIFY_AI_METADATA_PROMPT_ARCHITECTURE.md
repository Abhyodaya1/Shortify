# SHORTIFY — AI METADATA & YOUTUBE SEO PROMPT ARCHITECTURE

**Date:** November 15, 2026  
**Architect:** Antigravity Autonomous Systems Engineering  
**Workspace:** `C:\Users\ASUS\Desktop\clipperfree`  
**Governing Directive:** `master_seo.md`  

---

## 1. System Philosophy: Evidence vs. Copywriting

A critical architectural distinction in Shortify is that **raw transcripts are untrusted source evidence, never finished marketing copy**.

```text
[Raw Spoken Audio / Whisper Transcription]
                      ↓
           (Untrusted Source Evidence)
                      ↓
  Role 01: Transcript Intelligence & Repetition Detection
                      ↓
  Role 02 & 03: Hook Strategy & Multi-Angle Headline Generation
                      ↓
  Role 04: Editorial Quality Review (No Clickbait, No Inventions)
                      ↓
  Role 06: Content Packager (Polished Human Copywriting & SEO)
                      ↓
[Finished YouTube Metadata: 3 Titles, Clean 2-Sentence Description, 8-15 Tags, 3-5 Hashtags]
```

### The Seven-Role Collaboration
Shortify executes seven specialized roles defined in `shorts_ai_roles_prompt_pack/`:
- **Role 01 (Transcript Analyst)**: Detects repetition loops, extracts core premise, identifies entities, and flags unsupported claims.
- **Role 02 (Hook Strategist)**: Formulates attention angles (curiosity, unexpected payoff, contrarian perspective).
- **Role 03 (Headline Writer)**: Formats visual overlays and text banners.
- **Role 04 (Editorial Judge)**: Audits factual grounding and verifies title/thumbnail synergy.
- **Role 05 (Subtitle QA)**: Enforces CPS (<25) and CPL (<37) typographic standards.
- **Role 06 (Content Packager)**: Owns final YouTube metadata generation (titles, description, tags, hashtags).
- **Role 07 (Voice Director)**: Directs neural voice synthesis (TTS) timing and prosody.

---

## 2. Anti-Boilerplate & Anti-Repetition Rules

### A. Repetition & Musical Loop Suppression
When a video contains repeated lyrics, speech loops, or chants (such as *"Don't believe me, just watch"* repeated 30 times in an edit):
- **Prohibited Behavior**: Verbatim quoting of repeated syllables or cutting off raw words like `"{text[:160]}..."`.
- **Enforced Behavior**: The system detects multi-word n-gram loops ($n \ge 3$ repeated $\ge 3$ times), classifies the clip as a rhythmic/musical performance or high-energy refrain, and synthesizes the artistic context instead of echoing spoken lyrics.

### B. Prohibition of Mechanical Templates
The following patterns are permanently banned from both online prompts and deterministic fallback generators:
- `❌ "Key Takeaway from [Video Title]:"`
- `❌ "Did you know this? Drop a comment below!"`
- `❌ "What do you think? Let us know in the comments!"`
- `❌ Generic hashtags: #Knowledge #Productivity #Creator (unless the topic is literally productivity)`

### C. Clean Description Standard
Every description produced must consist of:
1. **Sentence 1 (The Hook/Premise)**: Directly states the core highlight without clickbait.
2. **Sentence 2 (Narrative / Context)**: Explains what is unique, why it matters, or the artistic energy.
3. **Sentence 3 (Clean Call to Action)**: Natural conversational sign-off (e.g. *"Watch till the end to catch every detail."*).
4. **Hashtags (3 to 5)**: Hyper-relevant tags tailored to the actual topic (e.g. `#{TopicSlug}`, `#Music`, `#Shorts`, `#Trending`).

---

## 3. SEO Search Tags Architecture

YouTube search tags index videos for algorithm recommendation, distinct from discovery hashtags:
- **Quantity**: 8 to 15 substantive keywords.
- **Formatting**: Plain strings only. `#` prefixes are strictly stripped.
- **Content**: Substantive entities (proper nouns, tools, software, artists, song titles, specific techniques, and category descriptors).
- **UI State**: Form input is initialized with pre-populated keywords and displays live count (e.g. `12 / 15 tags`). It is never empty (`0 / 15 tags`).

---

## 4. Multi-Angle Title Architecture

Shortify generates three distinct title options for every Short:
1. **Direct / Hook-Led**: Concise and punchy under 40 characters for mobile feed safety without truncation.
2. **Curiosity / Narrative**: Engaging question or observation under 60 characters for desktop search.
3. **Contrarian / Twist**: Highlights the unexpected revelation, drop, or payoff under 60 characters.

All titles are pre-linted using `YouTubeIntelligenceService.lint_title` to verify character bounds and prevent vagueness.
