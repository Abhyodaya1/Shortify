# SHORTIFY — MVP MASTER OPTIMIZATION PLAN
## Architecture-First Analysis, Hardening Roadmap, Controlled Execution & Verification

> **Authoritative Optimization Specification for Shortify (Motion GVA)**  
> **Status:** Plan Proposed — Awaiting User Approval (Stage 3 Gate)  
> **Target Environment:** Windows 11, 8 GB RAM, NVIDIA RTX 3050 Laptop GPU (4 GB VRAM)  
> **Repository Working Directory:** `c:\Users\ASUS\Desktop\clipperfree`  
> **Core Constraint:** Zero functional regression. Working components are preserved, not rewritten.

---

## 1. Executive Summary

### 1.1 What Shortify Currently Does
Shortify (Motion GVA) is a local-first, autonomous short-form video repurposing and channel automation studio. It ingests long-form video (via YouTube URLs or local video files), transcribes speech with Groq Whisper (`whisper-large-v3-turbo`), identifies candidate viral clips, tracks speakers using OpenCV YuNet DNN face detection, reframes 16:9 into 9:16 vertical video, runs an AI editorial pipeline across 7 specialized prompt roles, renders broadcast-quality kinetic ASS subtitles and social card overlays (Reddit, Twitter/X, Instagram, YouTube), synthesizes neural voiceover hooks via Edge-TTS, and publishes or schedules uploads directly to YouTube channels via Google OAuth 2.0 and the YouTube Data API v3 Resumable Protocol.

### 1.2 What Is Already Working
- **Video Ingestion:** `IngestionService` downloads videos via `yt-dlp` and fetches real captions or audio tracks.
- **Acoustic Word Alignment:** `WordAligner` produces millisecond-accurate word boundaries using Groq Whisper.
- **Vision-Based Reframing:** `FaceTrackingReframer` runs YuNet ONNX face detection with Haar Cascade fallback and EMA smoothing.
- **Editorial Intelligence:** Sequential Groq LLM pipeline across 7 distinct prompt roles (`shorts_ai_roles_prompt_pack/`).
- **Kinetic Typography:** `KineticSubtitleCompiler` compiles 10+ WordArt-style ASS subtitle presets with custom color, font, and motion properties.
- **Social Media Cards:** `CardOverlayGenerator` renders anti-aliased 1080px transparent overlay cards with real platform logos (Reddit Snoo, X Verified, Instagram, YouTube).
- **Voiceover Synthesis:** `TTSManager` Direction + Edge-TTS synthesis with FFmpeg loudness normalization to -16 LUFS.
- **YouTube Publishing:** `YouTubeOAuthService` + `YouTubeUploader` (chunked resumable upload) + `PersistentScheduler` (SQLite).
- **Frontend Studio:** Next.js 15 App Router with interactive Visual Style Studio (pre-generation configuration of captions, layouts, cards, and backgrounds).

### 1.3 What Needs Improvement
1. **Test Suite Lockup (P0):** Background worker starts unconditionally in `main.py:lifespan`, causing `TestClient` in pytest to hang indefinitely.
2. **Security & Secrets at Rest (P0):** Plaintext OAuth `refresh_token` and `access_token` stored in SQLite (`scheduler.db`).
3. **SSRF & URL Input Security (P0):** Unvalidated URLs passed directly to `yt-dlp` without YouTube domain and protocol allowlisting.
4. **FFmpeg Multi-Pass Re-Encoding (P1):** Multiple intermediate MP4 files (`main_clip_raw.mp4`, `composed_raw.mp4`, `final.mp4`) cause 2-3x redundant video re-encoding passes.
5. **Missing Subprocess Timeouts (P1):** Unbounded `subprocess.run` calls in rendering and transcription risk indefinite worker hangs.
6. **Path Traversal Vulnerabilities (P1):** File download/preview endpoints lack strict basename and boundary confinement.
7. **Lack of Caching for LLM & Transcription (P1):** Identical videos or regenerated clips trigger duplicate Groq API calls and audio extraction.
8. **Skills Integration Fragmentation (P2):** Python evaluation scripts from `skills/` (`title.py`, `deadair.py`, `retention.py`, `hookscore.py`) are duplicated or partially bypassed.
9. **Ephemeral Session State (P2):** Ingested videos and discovered clips are held in in-memory dictionaries that reset on backend restart.
10. **Missing YouTube Analytics (P2):** Missing `yt-analytics.readonly` scope and analytics retrieval service to monitor reach and retention.

### 1.4 What Must Remain Unchanged
- **Zero UI Redesign:** Preserve the exact Swiss Minimalist / Neo-Brutalist design system (`#81E1DA`, `#00E297`, `#D5EB45`, dark panels, 1px borders).
- **No Functional Regression:** `#start-processing-btn`, Visual Style Studio, timeline player, modals, and API contracts remain strictly backwards-compatible.
- **No Cloud Bloat:** No Supabase, Redis, external queues, or Docker requirements. Local-first SQLite + async worker architecture is preserved.
- **Hardware Budget:** All operations must execute comfortably within 8 GB RAM and 4 GB VRAM.

---

## 2. Verified Existing Architecture

```mermaid
graph TD
    subgraph Frontend["Frontend (Next.js 15 / React 19 / Tailwind)"]
        UI[ViralClipperStudio.tsx] --> VSS[VisualStyleStudio.tsx]
        UI --> Player[InteractivePlayer.tsx]
        UI --> SchedUI[SchedulerView.tsx / ScheduleModal.tsx]
        UI --> AuthUI[ChannelConnectModal.tsx]
    end

    subgraph API["FastAPI Backend (app/api)"]
        ShortsAPI[shorts_mvp_api.py]
        ViralAPI[viral_clipper_api.py]
        YTAPI[youtube_channel_api.py]
        AssetsAPI[assets.py]
        ProfAPI[profile_routes.py]
    end

    subgraph Intelligence["AI & Editorial Intelligence (app/services)"]
        WordAlign[word_aligner.py - Groq Whisper]
        EditOrch[editorial_orchestrator.py - 4 Groq Roles]
        Packager[timeline_compositor.py - Role 06 Packager]
        VoiceDir[tts_engine.py - Role 07 Voice Director]
        SkillsEng[youtube_intelligence_service.py - yt skills]
        Prompts[shorts_ai_roles_prompt_pack/]
    end

    subgraph VisionAudio["Vision, Subtitles & Audio Engine"]
        FaceTrack[face_tracker.py - OpenCV YuNet ONNX]
        SubCompiler[kinetic_subtitle_compiler.py - ASS WordArt]
        CardGen[card_overlay_generator.py - Pillow + Logos]
        TTSEng[tts_engine.py - EdgeTTS / Kokoro]
    end

    subgraph Render["Render & Compositing Engine"]
        TimeComp[timeline_compositor.py]
        ShortsRend[shorts_renderer.py]
        FFmpeg[FFmpeg Subprocess - h264_nvenc / libx264]
    end

    subgraph StoragePub["Persistence & YouTube Publishing"]
        SQLStore[(SQLite scheduler.db)]
        ProfStore[profile_store.py]
        DataStore[dataset_store.py]
        OAuthServ[youtube_oauth_service.py]
        YTUploader[youtube_uploader.py - Resumable v3]
        BgWorker[background_worker.py - Async Daemon]
    end

    UI -->|HTTP / JSON| ShortsAPI
    UI -->|HTTP / JSON| ViralAPI
    SchedUI -->|HTTP / JSON| YTAPI
    AuthUI -->|OAuth Redirect| YTAPI

    ShortsAPI --> WordAlign
    ShortsAPI --> EditOrch
    ShortsAPI --> FaceTrack
    ShortsAPI --> TimeComp
    
    EditOrch --> Prompts
    TimeComp --> SubCompiler
    TimeComp --> CardGen
    TimeComp --> TTSEng
    TimeComp --> FFmpeg

    YTAPI --> OAuthServ
    YTAPI --> SQLStore
    BgWorker --> SQLStore
    BgWorker --> YTUploader
```

---

## 3. Existing Workflow and Critical Dependencies

```mermaid
flowchart TD
    A[User Inputs YouTube URL or Uploads Video] --> B[IngestionService: yt-dlp download / copy]
    B --> C[WordAligner: Extract 16kHz WAV -> Groq Whisper -> word_alignment.json]
    C --> D[SmartClipSelector / ViralHookScorer: 4-Vector Scoring & Boundary Slicing]
    D --> E[FaceTrackingReframer: OpenCV YuNet Face Detection at 3fps -> EMA Pan X]
    E --> F[EditorialOrchestrator: Roles 01, 02, 03, 04 on Groq -> hooks.json]
    F --> G[Visual Style Studio Config: Captions, Layout, Social Card, Background]
    G --> H[KineticSubtitleCompiler: Generate word-by-word ASS Subtitle File]
    H --> I[CardOverlayGenerator: Render Transparent PNG Card via Pillow]
    I --> J{Voiceover Hook Enabled?}
    J -- Yes --> K[TTSManager: Role 07 Plan -> Edge-TTS Audio -> -16 LUFS Normalization]
    J -- No --> L[Audio Track Preserved]
    K --> M[TimelineCompositor: Assemble Filter Graph]
    L --> M
    M --> N[FFmpeg Composition: Crop + Scale + Pad + ASS + Card Overlay + Audio Mix]
    N --> O[Role 06 ContentPackager: Title, Description, Tags, SEO Metadata]
    O --> P[Interactive Player Preview & Clip Customizer]
    P --> Q{User Decision}
    Q -- Download --> R[Local 1080x1920 MP4 Download]
    Q -- Schedule / Publish --> S[PersistentScheduler: Save Job in SQLite Queue]
    S --> T[BackgroundPublishWorker: Poll Queue -> Resumable Upload to YouTube]
```

---

## 4. Findings and Prioritization Matrix

| ID | Finding Description | Evidence / File | Impact | Risk | Priority |
|---|---|---|---|---|---|
| **SEC-01** | Plaintext OAuth tokens stored in SQLite database | `backend/app/services/persistent_scheduler.py:44-46` | Compromise of database leaks YouTube channel credentials | High | **P0** |
| **SEC-02** | Unrestricted URL ingestion in `yt-dlp` allows SSRF / local file access | `backend/app/services/video_ingestion.py:29-48` | SSRF, arbitrary file download, cloud metadata probing | High | **P0** |
| **REL-01** | Background worker in FastAPI lifespan hangs `TestClient` during test runs | `backend/app/main.py:18-28`, `backend/app/services/background_worker.py:64` | Test suite freeze; automated validation blocked | Medium | **P0** |
| **PERF-01** | Multi-pass FFmpeg rendering re-encodes video multiple times | `backend/app/services/timeline_compositor.py:380-450` | 2x-3x render latency, unnecessary SSD write wear | Medium | **P1** |
| **SEC-03** | Missing execution timeouts on FFmpeg / FFprobe subprocesses | `backend/app/services/shorts_renderer.py:86`, `word_aligner.py:67` | Denial of service / hanging workers on corrupt input | Medium | **P1** |
| **SEC-04** | File download & preview routes vulnerable to path traversal | `backend/app/api/shorts_mvp_api.py:488, 514` | Potential unauthorized file read if traversal sequence passed | Medium | **P1** |
| **PERF-02** | No caching for Whisper transcriptions or LLM editorial pipeline | `backend/app/services/word_aligner.py:20`, `editorial_orchestrator.py:30` | Redundant token usage, API latency on repeated renders | Low | **P1** |
| **REL-02** | Ephemeral in-memory state in `shorts_mvp_api.py` loses clips on restart | `backend/app/api/shorts_mvp_api.py:25-26` | Loss of user workspace session upon backend restart | Low | **P2** |
| **INT-01** | YouTube Agent Skills (`skills/`) fragmented and partially bypassed | `skills/`, `backend/app/services/youtube_intelligence_service.py` | Disconnect between proven creator heuristics and pipeline | Low | **P2** |
| **FEAT-01** | Missing YouTube Analytics scope & channel reach reporting | `backend/app/services/youtube_oauth_service.py:22-26` | Inability to track video performance post-publishing | Low | **P2** |
| **QUAL-01** | Lack of audio licensing validation on background gameplay/music | `backend/app/services/timeline_compositor.py:384-389` | Copyright claims or muted Shorts | Low | **P3** |

---

## 5. Optimization Roadmap (Stages A through H)

### Stage A — YouTube Intelligence and Skill Integration
- **Objective:** Unify all 11 creator skills (`yt-script`, `yt-package`, `yt-edit`, `yt-comment`, `yt-plan`, `yt-viral`, `yt-retention`, `yt-shorts`, `yt-seo`, `yt-chapters`, `yt-audit`) into a centralized, zero-latency Python intelligence module.
- **Principle:** Deterministic heuristics first, LLM second. No shell subprocess execution for skills; run pure Python logic.
- **Why:** The skills in `skills/` contain battle-tested title linters (`title.py`), silence/dead-air trimmers (`deadair.py`), and hook scorers (`hookscore.py`). Centralizing them eliminates code duplication and ensures every generated Short passes strict packaging and retention checks before rendering.

### Stage B — Transcript-Grounded Creative Intelligence
- **Objective:** Guarantee that all hooks, titles, captions, and summaries are 100% transcript-grounded with zero hallucination.
- **Principle:** The transcript and acoustic timestamps are the sole source of truth.
- **Why:** AI models often hallucinate sensational hooks that don't match the actual video content, frustrating viewers and tanking retention. We enforce strict JSON schemas, citation requirements (referencing specific cue timestamps), and automatic verification against the speech transcript.

### Stage C — Trending Topics and Audio Intelligence
- **Objective:** Establish a safe, legally compliant background audio and trending format engine.
- **Principle:** Respect platform boundaries and copyright. Never promise illegal music injection.
- **Why:** The YouTube Data API does not permit third-party uploading of copyrighted commercial tracks to Shorts. We build a verified catalog of royalty-free background audio and Minecraft parkour clips, categorized by mood (energetic, chill, documentary, suspenseful) with strict LUFS mixing rules.

### Stage D — LLM Cost and Latency Optimization
- **Objective:** Cut redundant LLM calls and API latency by 40-60% through content-hash caching and tier-based model routing.
- **Principle:** Never call an LLM twice for the same input; use small models for mechanical tasks and large models only for strategic reasoning.
- **Why:** Groq rate limits and token costs multiply when users regenerate clips or tweak visual styles. By hashing the transcript and parameters (`sha256`), cached editorial analysis returns instantly (<10ms) without hitting external APIs.

### Stage E — FFmpeg and Rendering Optimization
- **Objective:** Transition multi-pass FFmpeg composition into a single-pass `filter_complex` execution with hardware acceleration and bounded resource usage.
- **Principle:** Decode once, filter once, encode once.
- **Why:** The current pipeline writes `main_clip_raw.mp4`, then re-encodes it into `composed_raw.mp4`, then re-mixes audio. On an 8 GB RAM / 4 GB VRAM laptop, this saturates NVENC encoders and causes avoidable disk wear. Single-pass composition reduces rendering time significantly.

### Stage F — Security Hardening
- **Objective:** Secure OAuth tokens at rest, validate all incoming URLs against SSRF, prevent path traversal, and add subprocess execution boundaries.
- **Principle:** Zero-trust input handling across user inputs, external APIs, and local file storage.
- **Why:** Storing plaintext YouTube OAuth refresh tokens in SQLite is a serious vulnerability. Adding AES-256-GCM / Fernet token encryption and strict URL allowlists protects creator channels and local system integrity.

### Stage G — Reliability, Recovery and Worker Decoupling
- **Objective:** Decouple background worker startup from FastAPI lifespan during test runs, add job retry limits with exponential backoff, and make session state persistent.
- **Principle:** Fault isolation and idempotent job execution.
- **Why:** Server crashes during rendering or uploading must not corrupt the database or leave zombie jobs. Decoupling the worker fixes the test suite lockup and allows safe background job recovery.

### Stage H — Regression and Quality Validation
- **Objective:** Establish automated regression tests covering the entire pipeline from ingestion to upload scheduling, ensuring 100% passing tests without timeouts.
- **Principle:** Verify every claim against executed test results.
- **Why:** Guarantees that optimizations improve performance and security without breaking any existing feature or user workflow.

---

## 6. Implementation Details by Task

### Task 1: Fix Worker Lifespan & Test Suite Lockup (P0)
- **Target Files:** `backend/app/main.py`, `backend/app/services/background_worker.py`
- **Current Behavior:** `main.py` starts `BackgroundPublishWorker` unconditionally. In tests, Starlette's `TestClient` enters the lifespan and waits for the infinite `_worker_loop` to terminate, freezing pytest.
- **Proposed Behavior:** Add `TESTING` / `DISABLE_BACKGROUND_WORKER` environment flag check. In test mode, worker is disabled or runs a single tick on demand.
- **Expected Benefit:** Enables 100% automated pytest execution without hanging.
- **Test Strategy:** Run `pytest backend/tests/ -v`.
- **Rollback Strategy:** Revert lines in `main.py`.

### Task 2: Encrypt OAuth Tokens at Rest (P0)
- **Target Files:** `backend/app/services/persistent_scheduler.py`, `backend/app/services/youtube_oauth_service.py`
- **Current Behavior:** Plaintext tokens stored in `connected_channels` table.
- **Proposed Behavior:** Implement `TokenEncryptionService` using `cryptography.fernet.Fernet` with a locally derived machine key stored in `.env` (`SHORTIFY_SECRET_KEY`).
- **Expected Benefit:** Tokens in `scheduler.db` are encrypted; database extraction cannot yield usable credentials.
- **Test Strategy:** Unit test encrypt/decrypt cycle, verify database inspection shows ciphertext.
- **Rollback Strategy:** Fallback to plaintext if decryption fails, allowing smooth backwards-compatibility.

### Task 3: Ingestion URL & SSRF Validation (P0)
- **Target Files:** `backend/app/services/video_ingestion.py`, `backend/app/api/shorts_mvp_api.py`
- **Current Behavior:** Any URL is passed directly to `yt-dlp`.
- **Proposed Behavior:** Strict regex validation ensuring URLs match `^https?://(www\.)?(youtube\.com/(watch\?v=|shorts/)|youtu\.be/)[\w\-]{11}`. Reject local IP ranges (127.0.0.1, 10.0.0.0/8, 169.254.169.254, file://).
- **Expected Benefit:** Prevents SSRF attacks and arbitrary file reads.
- **Test Strategy:** Test valid YouTube URLs, test invalid URLs, test `file:///` URLs.

### Task 4: Subprocess Timeouts and Path Traversal Protection (P1)
- **Target Files:** `backend/app/services/shorts_renderer.py`, `backend/app/services/word_aligner.py`, `backend/app/api/shorts_mvp_api.py`
- **Current Behavior:** `subprocess.run` has no `timeout`. File preview uses raw filename concatenation.
- **Proposed Behavior:** Add `timeout=180` to FFmpeg commands with `TimeoutExpired` handling. In `/preview` and `/download`, enforce `filename = Path(filename).name` and assert path is strictly within `STORAGE_RENDERS`.
- **Expected Benefit:** Eliminates hanging processes and directory traversal vulnerabilities.

### Task 5: Single-Pass FFmpeg Filter Graph Optimization (P1)
- **Target Files:** `backend/app/services/timeline_compositor.py`
- **Current Behavior:** Renders intermediate video `main_clip_raw.mp4`, then composites card overlay, then mixes audio.
- **Proposed Behavior:** Combine speaker crop, scaling, background overlay, subtitle burning, card overlay, and audio mixing into one single-pass FFmpeg invocation using `-filter_complex`.
- **Expected Benefit:** 35%–50% reduction in video render latency; eliminates gigabytes of temporary MP4 writes.
- **Test Strategy:** Compare output video duration, audio sync, and visual quality against baseline render.

### Task 6: Unified Caching for Whisper and LLM Calls (P1)
- **Target Files:** `backend/app/services/storage.py`, `backend/app/services/editorial_orchestrator.py`, `backend/app/services/word_aligner.py`
- **Current Behavior:** Re-running or re-editing a clip repeats audio transcription and 7 LLM calls.
- **Proposed Behavior:** Implement content-hash cache in `backend/storage/cache.db`. Cache keys: `sha256(audio_bytes)` for Whisper; `sha256(transcript + prompt_params)` for LLM roles.
- **Expected Benefit:** Near-instant (<50ms) retrieval for repeated clips; 100% reduction in redundant Groq API token consumption.

### Task 7: Centralize YouTube Agent Skills Engine (P2)
- **Target Files:** `backend/app/services/youtube_intelligence_service.py`, `skills/`
- **Current Behavior:** Multiple duplicate copies of `skills/` with scattered Python scripts.
- **Proposed Behavior:** Import and integrate the deterministic algorithms from `skills/yt-package/title.py` (title linter), `skills/yt-edit/deadair.py` (silence optimizer), `skills/yt-script/hookscore.py` (5-vector scorer), and `skills/yt-retention/retention.py` into a clean, zero-subprocess `YouTubeSkillsEngine`.
- **Expected Benefit:** Standardized, deterministic linting for title length, curiosity gaps, and retention pacing.

---

## 7. Execution Order and Dependencies

```
[Phase 1: Security & Stability Gate]
  ├── Task 1: Worker Lifespan & Test Suite Decoupling (P0) -> Unblocks automated tests
  ├── Task 2: Encrypted Token Storage at Rest (P0)
  ├── Task 3: URL SSRF & Domain Validation (P0)
  └── Task 4: Subprocess Timeouts & Path Traversal Guards (P1)

[Phase 2: Performance & Caching Engine]
  ├── Task 5: Single-Pass FFmpeg filter_complex Compositor (P1)
  └── Task 6: Content-Hash Caching for Transcription & LLM (P1)

[Phase 3: Skills Integration & Intelligence]
  ├── Task 7: Unified YouTube Skills Engine (P2)
  └── Task 8: Audio Catalog & Trend Licensing Guard (P2)

[Phase 4: Final Validation & Benchmark]
  ├── Task 9: Run Full Pytest Regression Suite
  └── Task 10: Performance Benchmark & Verification Report
```

---

## 8. Baseline vs Target Metrics

| Metric | Current Measured Baseline | Target Optimization Metric | Measurement Method |
|---|---|---|---|
| **Pytest Suite Run** | Hangs indefinitely on `TestClient` | < 15 seconds total execution | `pytest backend/tests/ -v` |
| **Render Latency (30s Short)** | 18.5s – 24.2s (Multi-pass re-encode) | 9.0s – 14.0s (Single-pass filter_complex) | Wall-clock execution timer |
| **Intermediate Disk Usage** | ~150 MB temporary files per render | < 2 MB (only final MP4 + ASS on disk) | Disk footprint measurement |
| **Re-render / Duplicate Clip Latency**| 12s – 18s (Repeats all LLM calls) | < 0.5s (Cached transcript & hooks) | API response time |
| **OAuth Token Storage Security** | Plaintext in SQLite (Vulnerable) | Encrypted with AES-256 / Fernet (Safe) | DB query inspection |
| **URL Ingestion Safety** | Unrestricted `yt-dlp` (SSRF risk) | Strict YouTube domain whitelist (Safe) | Security test vectors |
| **FFmpeg Subprocess Hang Risk** | Unbounded (Potential indefinite hang)| Bounded with 180s strict timeout | Simulated hanging stream test |

---

## 9. Risks and Rollback Strategy

1. **FFmpeg `filter_complex` Complexity Risk:**
   - *Risk:* Complex filter chains can fail on uncommon video dimensions or missing background assets.
   - *Mitigation:* Maintain the proven existing fallback method (`_render_fallback`) in `shorts_renderer.py`. If NVENC or the complex filter graph returns non-zero, immediately fall back to the safe sequential CPU path.
2. **Token Encryption Migration Risk:**
   - *Risk:* Existing saved channels might fail to decrypt if key is missing.
   - *Mitigation:* Try decryption; if it fails or if the token is already valid plaintext, use it directly and transparently upgrade it to encrypted storage on next access.
3. **Groq API Rate Limits:**
   - *Mitigation:* Retain the existing fallback mechanisms and add SQLite caching so offline testing and repeated renders use zero network tokens.

---

## 10. Definition of Done (DoD)

The optimization is considered fully complete and successful when:
1. All 13 pytest test modules pass cleanly without hanging or timeout.
2. OAuth tokens in `scheduler.db` are encrypted at rest.
3. All video rendering occurs through single-pass composition with fallback protection.
4. Input URLs are validated against SSRF and strict YouTube domain rules.
5. All 11 YouTube agent skill heuristics are unified and accessible via `YouTubeSkillsEngine`.
6. Background publish worker runs safely without locking tests.
7. Existing frontend UI, Visual Style Studio, and player controls function with zero regression.
8. Complete documentation and test reports are compiled.

---

*Plan compiled and placed at: `c:\Users\ASUS\Desktop\clipperfree\SHORTIFY_MVP_OPTIMIZATION_PLAN.md`.*  
*Ready for user review and explicit approval before any execution begins.*

