# Shorts AI Editorial Roles — Prompt Pack

Seven specialized roles, each with a dedicated `system.md` and `user.md` prompt template.

## Roles
1. Transcript Analyst
2. Hook Strategist
3. Visual Headline Writer
4. Editorial Judge
5. Subtitle QA
6. YouTube Content Packager
7. Voice Director (Pacing & SSML Coach)

## Suggested execution order
Transcript Analyst → Hook Strategist → Visual Headline Writer → Editorial Judge → Voice Director → TTS synthesis → final audio composition → word alignment/subtitle rendering → Subtitle QA → final validation → Content Packager.

## Important engineering rules
- Replace all `{{placeholders}}` with validated runtime data.
- Keep prompts versioned; store prompt version, model ID, input hash, and validation result per clip.
- Validate all model responses against JSON schemas before using them.
- Use forced alignment (e.g. WhisperX or a compatible aligner) for word timestamps. An LLM must not invent subtitle timestamps.
- Align against the final composed audio after voiceovers are inserted.
- Model-estimated speech duration is not authoritative; measure the generated audio with FFprobe.
- SSML support is provider-specific. Do not assume Kokoro and Piper support identical SSML tags.
- Keep Groq API keys on the backend in environment variables, never in client code.
- Treat generated output as untrusted until validated. Preserve human approval for final creative decisions and publication.

## Model routing
Configure model IDs centrally, outside these prompt files. Choose from models actually available to your Groq account and benchmark on your own clips. Use stronger reasoning models for analysis, hook strategy, and judging; faster models for headline and metadata tasks. Model availability and rate limits can change.

## Quality philosophy
Make content attention-grabbing through relevance, specificity, curiosity, contrast, and payoff—not fabricated claims, manipulative bait, or exaggerated promises.
