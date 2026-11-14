# SHORTIFY — MVP FINAL OPTIMIZATION MASTER PLAN
## Architecture-First Analysis → Planning → Controlled Execution → Validation

Act as a Principal Software Architect, Senior AI/LLM Engineer, FFmpeg Performance Engineer, Application Security Engineer, and YouTube Growth Strategist with 15+ years of engineering experience.

You are working on **Shortify**, an existing AI-powered YouTube Shorts generation and channel automation application.

Your mission is to bring the existing MVP to its highest practical level of quality, performance, reliability, security, and cost efficiency without breaking its existing functionality, changing its established workflow, or unnecessarily rewriting working components.

**This is an existing, functional application. Your first responsibility is to understand it, not modify it.**

---

# NON-NEGOTIABLE WORKING METHODOLOGY

You MUST follow these four stages in order:

1. THINK AND UNDERSTAND — Read the existing architecture, inspect the repository, and understand the actual implementation.
2. PLAN — Create a comprehensive Markdown optimization plan based on your findings.
3. REVIEW AND APPROVE — Present the plan and wait for my approval before implementation.
4. EXECUTE AND VALIDATE — Implement the approved plan incrementally, testing each stage before proceeding.

Do not skip stages.

Do not start implementing optimizations during the architecture-analysis or planning stage.

Do not assume that features described in documentation are implemented correctly. Verify them against the actual source code.

# STAGE 1 — THINK, READ AND UNDERSTAND THE EXISTING SYSTEM

Before changing anything:

### 1.1 Read the existing architecture

Locate and thoroughly read all relevant project documentation, including:

- Existing system architecture documents.
- README and setup documentation.
- Backend and frontend architecture.
- API specifications.
- Pipeline and data-flow documentation.
- Database schemas and migrations.
- Existing agent/skill configurations.
- FFmpeg rendering documentation.
- YouTube OAuth and publishing documentation.
- Existing optimization notes and TODO files.

If documentation is missing, identify the gaps.

### 1.2 Inspect the actual repository

Explore the complete project structure and identify:

- Frontend framework, components, hooks and state management.
- Backend framework, API routes and services.
- Database and persistence layer.
- Background workers and scheduling mechanisms.
- LLM providers and model configurations.
- Transcription and semantic clip-discovery pipeline.
- FFmpeg rendering and subtitle generation.
- YouTube integration and publishing pipeline.
- File handling and storage.
- Error handling, logging and monitoring.
- Existing tests and validation mechanisms.
- Existing YouTube Agent Skills integration.

Pay particular attention to the existing implementation of:

- `shorts_mvp_api.py`
- `youtube_channel_api.py`
- `viral_clipper_api.py`
- `timeline_compositor.py`
- `card_overlay_generator.py`
- `persistent_scheduler.py`
- `youtube_oauth_service.py`
- `youtube_uploader.py`
- `youtube_intelligence_service.py`

These are examples of known project components. Verify their actual existence, names and responsibilities before relying on them.

### 1.3 Trace the complete existing workflow

Understand and document the real execution path:

1. User selects a YouTube URL, local video or folder.
2. Source ingestion and validation.
3. Audio extraction.
4. Speech transcription.
5. Word-level timestamp generation.
6. Semantic clip discovery.
7. Hook and clip quality evaluation.
8. Clip selection and editing.
9. Subtitle and caption generation.
10. Layout, background and visual-style application.
11. FFmpeg rendering.
12. Metadata, title, description and SEO generation.
13. Preview and user approval.
14. YouTube channel connection.
15. Scheduling and uploading.
16. Persistence, recovery and status tracking.

Trace the actual function calls, API requests, data structures and dependencies connecting these stages.

Identify where LLM calls, FFmpeg processes, external APIs and database operations occur.

### 1.4 Establish the current baseline

Before optimization, record measurable baseline values wherever possible:

- Average processing time per video.
- Transcription duration.
- LLM calls per video.
- LLM tokens and approximate cost.
- Clip-discovery latency.
- Rendering duration per clip.
- Peak RAM usage.
- GPU/VRAM usage where measurable.
- Output file size.
- Rendering failures.
- API failures and retry behavior.
- Scheduler reliability.
- Current test coverage and regression status.

Do not fabricate measurements. Clearly label unavailable metrics.

### 1.5 Create an architecture assessment

Identify:

- Existing strengths.
- Performance bottlenecks.
- Redundant operations.
- Expensive LLM operations.
- Security vulnerabilities.
- Reliability weaknesses.
- Technical debt.
- Missing tests.
- Opportunities for deterministic processing.
- Opportunities for caching and reuse.

For every finding, include its evidence: relevant file, function, component or observed behavior.

**Stage 1 deliverable:** A clear understanding of the current Shortify system and its verified architecture.

No code modifications during this stage, except temporary, non-destructive diagnostic artifacts if necessary.

---

# STAGE 2 — CREATE THE MASTER MARKDOWN OPTIMIZATION PLAN

After completing Stage 1, create:

`SHORTIFY_MVP_OPTIMIZATION_PLAN.md`

Place it in the project root.

This file is the authoritative execution plan for the entire optimization project.

It must contain the following sections.

## 2.1 Executive Summary

Explain:

- What Shortify currently does.
- What is already working.
- What needs improvement.
- What optimization outcomes are expected.
- What must remain unchanged.

## 2.2 Verified Existing Architecture

Include:

- Frontend architecture.
- Backend architecture.
- Database and persistence.
- AI/LLM architecture.
- Transcription pipeline.
- Clip-generation pipeline.
- Rendering architecture.
- YouTube integration.
- Scheduling and background processing.

Include a Mermaid architecture diagram showing the actual existing implementation.

## 2.3 Existing Workflow and Dependencies

Document the complete pipeline with a Mermaid flowchart.

Identify critical dependencies between stages and components that must not be broken.

## 2.4 Findings and Prioritization

Create a table:

| ID | Finding | Evidence/File | Impact | Risk | Priority |
|---|---|---|---|---|---|

Prioritize using:

- P0: Critical security or data-integrity issue.
- P1: Major reliability or performance issue.
- P2: Significant optimization opportunity.
- P3: Optional improvement.

Clearly distinguish verified vulnerabilities from potential risks.

## 2.5 Optimization Roadmap

Divide the work into independently testable stages.

### Stage A — YouTube Intelligence and Skill Integration

Integrate and optimize the existing YouTube Agent Skill repository:

https://github.com/Jakeschincariol/youtube-agent-skill

Inspect the repository and its MIT license before integrating anything.

The repository contains 11 editorial skills:

1. `yt-script`
2. `yt-package`
3. `yt-edit`
4. `yt-comment`
5. `yt-plan`
6. `yt-viral`
7. `yt-retention`
8. `yt-shorts`
9. `yt-seo`
10. `yt-chapters`
11. `yt-audit`

It also provides Python helpers for selected deterministic evaluations.

Do not blindly invoke every skill for every video. Design a workflow that invokes only the skills relevant to the current task.

Prioritize:

- Transcript-grounded clip selection.
- Strong opening hooks.
- Context-preserving editing.
- Relevant captions.
- Accurate titles.
- Descriptions and hashtags.
- Search intent and keyword relevance.
- Metadata consistency.
- Editorial quality checks.

Use the transcript and timestamps as the source of truth.

The LLM must not invent dialogue, events, claims or context absent from the video.

Treat hook scores as editorial heuristics, not guarantees of virality.

### Stage B — Transcript-Grounded Creative Intelligence

Design an efficient creative-intelligence pipeline.

For each clip, evaluate:

- Opening hook.
- Clarity and context.
- Emotional or informational value.
- Audience relevance.
- Standalone completeness.
- Ending quality.
- Caption relevance.
- Title relevance.
- Search intent.

Generate:

- Multiple hook candidates where useful.
- Best recommended hook.
- Title candidates.
- SEO-optimized description.
- Relevant hashtags.
- YouTube tags where genuinely useful.
- Captions and subtitles grounded in actual speech.
- A concise editorial explanation.

Avoid keyword stuffing and misleading metadata.

Use deterministic checks wherever possible.

### Stage C — Trending Topics and Audio Intelligence

Develop a responsible trend-research and audio-recommendation workflow.

Investigate:

- Relevant trending topics.
- Current content formats.
- Relevant Shorts trends.
- Audio popularity and suitability.
- Audience and niche relevance.

Audio recommendations must consider:

- Mood.
- Video category.
- Speech clarity.
- Pacing.
- Platform suitability.
- Copyright and licensing.

Important limitations:

- Do not claim that the YouTube Data API can automatically attach arbitrary trending Shorts music.
- Do not download copyrighted trending audio from unauthorized sources.
- Distinguish between trend discovery, recommendation, licensing verification and actual audio insertion.
- Prefer appropriately licensed tracks and the YouTube Audio Library where suitable.
- Provide a manual selection workflow when direct integration is unsupported.

### Stage D — LLM Cost and Latency Optimization

Inspect every LLM call.

Investigate:

- Duplicate prompts.
- Repeated transcript processing.
- Unnecessary model calls.
- Excessive context.
- Oversized responses.
- Poor model selection.
- Unnecessary retries.
- Missing caching.
- Repeated structured-output validation.

Implement appropriate optimizations:

- Transcript and intermediate-result caching.
- Content-hash-based cache invalidation.
- Structured JSON output.
- Smaller models for simple tasks.
- Stronger models only for tasks that need them.
- Deterministic processing for simple checks.
- Prompt consolidation where quality is preserved.
- Bounded retries and timeouts.
- Token and cost tracking.
- Failure-safe fallback behavior.

Never sacrifice editorial quality simply to reduce token usage.

### Stage E — FFmpeg and Rendering Optimization

Profile the existing rendering pipeline before modifying it.

Investigate:

- Repeated decoding and encoding.
- Unnecessary intermediate files.
- Repeated subtitle rendering.
- Unnecessary scaling and frame conversion.
- Audio/video synchronization.
- Filter graph efficiency.
- Excessive subprocess creation.
- Rendering bottlenecks.
- Memory usage.
- Temporary-file management.
- Hardware encoding availability.

Optimize:

- Filter graphs.
- Intermediate processing.
- Asset reuse.
- Encoding configuration.
- Rendering concurrency.
- Resource management.
- Temporary-file cleanup.
- Error handling.

Benchmark CPU encoding against available hardware acceleration.

Do not assume hardware acceleration is always faster.

Preserve output quality, aspect ratio, audio quality, subtitles, layouts, animations and visual styles.

Use FFprobe to validate output resolution, codecs, FPS, duration, audio streams and synchronization.

### Stage F — Security Hardening

Audit the entire application, especially:

- File uploads.
- File paths and path traversal.
- URL ingestion and SSRF.
- FFmpeg subprocess execution.
- Shell command construction.
- YouTube OAuth and token handling.
- API keys and secrets.
- Local storage permissions.
- CORS and API validation.
- External API responses.
- Prompt injection.
- AI-generated content used as tool input.
- Scheduler inputs.
- File deletion and cleanup.

Implement appropriate safeguards.

Never trust user-provided URLs, filenames, transcripts or LLM output.

Avoid exposing credentials to the frontend or logs.

Do not break existing YouTube OAuth functionality.

### Stage G — Reliability and Recovery

Inspect and improve:

- Worker lifecycle.
- Persistent job states.
- Scheduler restart behavior.
- Retry policies.
- Idempotency.
- Duplicate uploads.
- Partial rendering failures.
- Interrupted downloads.
- API outages.
- Disk-full conditions.
- Process timeouts.
- Database transaction safety.
- Recovery after application restart.

Ensure failed jobs can recover without corrupting completed work.

### Stage H — Regression and Quality Validation

Build tests around the existing pipeline.

Validate:

- URL ingestion.
- Local-file ingestion.
- Transcription.
- Clip discovery.
- Hook generation.
- Captions.
- Metadata.
- Visual styles.
- Subtitle timing.
- FFmpeg rendering.
- Audio synchronization.
- Preview generation.
- OAuth.
- Scheduling.
- Uploading.
- Job recovery.

Compare before-and-after results.

## 2.6 Implementation Details

For every planned task, document:

- Exact files likely to change.
- Current behavior.
- Proposed behavior.
- Dependencies.
- Implementation approach.
- Expected benefit.
- Risk.
- Test strategy.
- Rollback strategy.
- Acceptance criteria.

Do not list speculative file paths as verified facts.

## 2.7 Execution Order and Dependencies

Create a dependency-aware implementation sequence.

Prefer small, isolated changes.

Security and data-integrity problems take precedence.

Do not optimize components before understanding their dependencies.

## 2.8 Baseline and Target Metrics

Include a comparison table:

| Metric | Baseline | Target | Measurement Method |
|---|---|---|---|

Use realistic, measurable targets. Do not promise arbitrary percentage improvements before benchmarking.

## 2.9 Risks and Rollback Strategy

Document:

- Potential regressions.
- Critical dependencies.
- Database migration risks.
- Rendering compatibility risks.
- API compatibility risks.
- Rollback instructions.

## 2.10 Definition of Done

The MVP optimization is complete when:

- Existing workflows remain functional.
- No critical regression remains.
- Security issues are addressed or explicitly documented.
- LLM calls and costs are measurably improved where possible.
- Rendering performance is measured and improved where possible.
- Transcript-grounded creative quality is maintained or improved.
- YouTube metadata is relevant and accurate.
- Audio recommendations respect licensing limitations.
- Scheduler and upload reliability are tested.
- Documentation is updated.
- All changes are traceable and reversible.

---

# STAGE 3 — PRESENT THE PLAN AND WAIT FOR APPROVAL

Once `SHORTIFY_MVP_OPTIMIZATION_PLAN.md` is created:

1. Do not start implementing the plan yet.
2. Present a concise summary of the architecture you discovered.
3. Present the most important findings.
4. Show the optimization stages and their priorities.
5. Identify high-risk changes.
6. Identify expected benefits and measurable targets.
7. Tell me where the Markdown plan was created.
8. Wait for my explicit approval.

Do not interpret silence as approval.

If I request changes to the plan, update the Markdown document before implementation.

---

# STAGE 4 — EXECUTE THE APPROVED PLAN STEP BY STEP

After I approve the plan, begin implementation.

Follow these rules strictly.

## 4.1 Work in small stages

Implement one logical stage at a time.

For each stage:

1. Re-read the relevant source files.
2. Verify the assumptions in the plan.
3. Check the current Git status.
4. Create a checkpoint or commit when appropriate.
5. Implement the smallest safe change.
6. Run relevant unit tests.
7. Run integration tests.
8. Run regression tests.
9. Compare behavior against the baseline.
10. Update `SHORTIFY_MVP_OPTIMIZATION_PLAN.md`.

## 4.2 Stage completion report

After every stage, report:

- What was changed.
- Why it was changed.
- Files modified.
- Tests executed.
- Test results.
- Performance measurements.
- Security impact.
- Remaining issues.
- Rollback instructions.

Do not claim a test passed unless it was actually executed and passed.

Do not silently skip failed tests.

If a change causes a regression, stop and fix or roll it back before proceeding.

After each major stage, provide a checkpoint summary. Continue to the next approved stage only when its acceptance criteria are satisfied. Ask for my decision if an unexpected architectural change, destructive operation or significant trade-off is required.

## 4.3 Preserve the existing product

Do not:

- Rewrite the application.
- Replace the existing architecture without necessity.
- Redesign the UI.
- Remove working functionality.
- Change existing API contracts unnecessarily.
- Change the current user workflow.
- Replace stable components with fashionable alternatives.
- Introduce unnecessary dependencies.
- Introduce cloud infrastructure.
- Introduce Supabase authentication or SaaS infrastructure.
- Make destructive database or storage changes.
- Remove existing visual styles or editing capabilities.
- Change rendering defaults without proving compatibility.

Preserve the current application behavior by default.

If a proposed optimization requires a behavior change, explain the reason and obtain approval first.

---

# TECHNICAL ENVIRONMENT AND CONSTRAINTS

The current project is local-first.

The optimization must respect the existing technology stack and actual repository configuration.

The development machine has limited resources:

- 8 GB RAM.
- NVIDIA RTX 3050 Laptop GPU.
- 4 GB dedicated VRAM.
- Windows development environment.

Do not assume unlimited memory, GPU resources or cloud compute.

Prefer resource-aware processing and safe concurrency limits.

Do not introduce new infrastructure unless explicitly approved.

---

# FINAL DELIVERABLES

At the end of the project, Shortify should have:

1. `SHORTIFY_MVP_OPTIMIZATION_PLAN.md` — architecture assessment, roadmap and execution history.
2. Verified architecture documentation.
3. Optimized YouTube Agent Skills integration.
4. Transcript-grounded hooks, captions and metadata generation.
5. Responsible trend and audio recommendation workflow.
6. Measurably optimized LLM usage.
7. Measurably optimized FFmpeg rendering where possible.
8. Security and reliability improvements.
9. Regression and integration tests.
10. Before-and-after performance report.
11. Updated setup and technical documentation.
12. A complete list of modified files and rollback instructions.

# YOUR FIRST ACTION

**Do not edit application code. Do not start optimization. Do not redesign anything.**

Start by:

1. Reading the existing Shortify architecture documentation.
2. Inspecting the repository and actual implementation.
3. Tracing the complete end-to-end pipeline.
4. Establishing the current baseline.
5. Identifying verified bottlenecks, vulnerabilities and optimization opportunities.
6. Creating `SHORTIFY_MVP_OPTIMIZATION_PLAN.md`.
7. Presenting the plan for my approval.

Only after I approve the plan should you begin executing it.

**The guiding principle: Understand first. Plan second. Optimize third. Validate continuously. Never compromise a working Shortify pipeline for an unmeasured optimization.**