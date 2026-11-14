<div align="center">

# ⚡ Shortify — AI YouTube Shorts Generator

**An autonomous video repurposing studio that transforms long-form videos into high-retention 9:16 Shorts.**

*Paste a URL. Click Get Shorts. Publish to YouTube. That's the whole loop.*

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%200.111-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2015-000000?style=flat-square&logo=nextdotjs)](https://nextjs.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![FFmpeg](https://img.shields.io/badge/Rendering-FFmpeg-007808?style=flat-square&logo=ffmpeg&logoColor=white)](https://ffmpeg.org/)
[![Groq](https://img.shields.io/badge/LLM-Groq%20Whisper%20%2B%20LLaMA-F55036?style=flat-square)](https://groq.com/)

</div>

---

## Why I Built This

Short-form video has become the dominant discovery layer for creators — but the production workflow is completely broken. You record an hour of content. You spend another three hours manually: watching it back, finding the moments, rough-cutting, adding captions, exporting in the right aspect ratio, writing a title, copy-pasting to YouTube.

That loop kills output velocity. I wanted a system where **the AI does all of that for me**, and I just review and hit publish.

Existing tools either watermark your content, produce mediocre captions that look like subtitles from a 2007 DVD, don't understand viral mechanics, or require you to manually re-enter every setting for every clip. None of them close the loop into YouTube publishing.

So I built Shortify from scratch: a fully autonomous pipeline that takes a URL, finds the viral moments, reframes the speaker, burns kinetic styled captions, overlays social cards, and publishes on a schedule — all from a single browser workspace.

---

## What It Does

```
YouTube URL / Local File / Folder
           ↓
   [ Viral Clip Selector ]  ← scores every segment on 4 virality vectors
           ↓
   [ Speaker Reframer ]     ← YuNet ONNX face detection + EMA-smoothed 9:16 crop
           ↓
   [ AI Editorial Pipeline] ← 7 sequential LLM roles (Groq): hook → headline → judge
           ↓
   [ Kinetic Subtitle Burn ]← word-level ASS subtitles, 10+ WordArt presets, FFmpeg
           ↓
   [ Social Card Overlay ]  ← Reddit / X / Instagram / YouTube cards via Pillow + logos
           ↓
   [ TTS Voice Hook ]       ← Edge-TTS neural voiceover, loudness-normalized
           ↓
   [ 9:16 MP4 Render ]      ← 1080×1920 H.264, FFmpeg multi-filter composition
           ↓
   [ YouTube Scheduler ]    ← OAuth upload with SQLite queue + background worker
```

---

## Architecture Overview

```
shortify/
├── backend/                        # FastAPI Python backend
│   ├── app/
│   │   ├── main.py                 # App entrypoint, lifespan, routers
│   │   ├── api/                    # REST API layer
│   │   │   ├── viral_clipper_api.py        # Clip analysis & generation
│   │   │   ├── shorts_mvp_api.py           # Full shorts pipeline trigger
│   │   │   ├── youtube_channel_api.py      # OAuth, scheduling, publishing
│   │   │   ├── generation.py               # Timeline / clip generation
│   │   │   ├── assets.py                   # Static asset serving
│   │   │   └── profile_routes.py           # Editorial profile CRUD
│   │   ├── services/               # Core intelligence & rendering layer
│   │   │   ├── viral_clipper.py            # 4-vector virality scoring engine
│   │   │   ├── face_tracker.py             # YuNet ONNX + Haar CV2 reframer
│   │   │   ├── word_aligner.py             # Groq Whisper word timestamps
│   │   │   ├── editorial_orchestrator.py   # 4-role LLM pipeline (Groq)
│   │   │   ├── kinetic_subtitle_compiler.py # ASS subtitle + WordArt engine
│   │   │   ├── card_overlay_generator.py   # Pillow social card renderer
│   │   │   ├── tts_engine.py               # Edge-TTS / Kokoro ONNX synthesis
│   │   │   ├── timeline_compositor.py      # Master render orchestrator
│   │   │   ├── shorts_renderer.py          # FFmpeg 9:16 composition engine
│   │   │   ├── youtube_uploader.py         # Resumable YT Data API v3 upload
│   │   │   ├── youtube_oauth_service.py    # OAuth 2.0 flow + token refresh
│   │   │   ├── persistent_scheduler.py     # SQLite job queue
│   │   │   ├── background_worker.py        # Async publish daemon
│   │   │   ├── clip_selector.py            # Candidate clip ranking
│   │   │   ├── video_ingestion.py          # URL download + local file prep
│   │   │   ├── llm_provider.py             # Groq API abstraction layer
│   │   │   ├── planner.py                  # Long-form plan generator
│   │   │   ├── quality_assurance.py        # QA validation layer
│   │   │   └── revision.py                 # Post-render revision engine
│   │   ├── models/                 # Pydantic data models
│   │   │   ├── timeline.py                 # Timeline / Track / Clip schema
│   │   │   └── editorial_profile.py        # Channel profile config schema
│   │   ├── serializers/            # Export format serializers
│   │   │   ├── fcpxml_serializer.py        # Final Cut Pro XML export
│   │   │   └── remotion_serializer.py      # Remotion JSON export
│   │   ├── storage/                # Persistence layer
│   │   │   ├── profile_store.py            # Profile read/write/cache
│   │   │   └── dataset_store.py            # Clip dataset registry
│   │   └── assets/logos/           # Social card logo assets
│   ├── models/
│   │   └── face_detection_yunet_2023mar.onnx  # YuNet DNN model
│   ├── tests/                      # pytest test suite (13 modules)
│   └── requirements.txt
│
├── frontend/                       # Next.js 15 / React 19 frontend
│   ├── app/
│   │   ├── page.tsx                # App shell / router
│   │   ├── layout.tsx              # Root layout
│   │   └── globals.css             # Global CSS + custom properties
│   ├── components/
│   │   ├── ViralClipperStudio.tsx  # Main studio view + pipeline trigger
│   │   ├── PersonalShortsStudio.tsx # Visual Style Studio host
│   │   ├── InteractivePlayer.tsx   # In-browser clip player + controls
│   │   ├── TimelineEditor.tsx      # Timeline scrubbing interface
│   │   ├── DashboardView.tsx       # Clips dashboard + status panel
│   │   ├── SchedulerView.tsx       # YouTube schedule manager
│   │   ├── ConversationalSidebar.tsx # AI chat sidebar
│   │   ├── ChannelConnectModal.tsx # YouTube OAuth connect modal
│   │   ├── ScheduleModal.tsx       # Schedule time picker modal
│   │   ├── Navbar.tsx              # Top navigation
│   │   └── visual-style-studio/    # Pre-generation visual configurator
│   │       ├── VisualStyleStudio.tsx   # Studio container + section layout
│   │       ├── CaptionPresetCard.tsx   # Caption style selector card
│   │       ├── LayoutPresetCard.tsx    # Video layout selector card
│   │       ├── SocialCardView.tsx      # Social platform card selector
│   │       ├── BackgroundPresetCard.tsx # Background preset selector
│   │       ├── StylePreviewModal.tsx   # 9:16 live preview modal
│   │       └── types.ts                # All preset data + VisualStyleConfig
│   ├── public/logos/               # Social card logos (PNG)
│   │   ├── instagram_logo.png
│   │   ├── reddit_logo.png
│   │   ├── twitter_verified.png
│   │   └── youtube_logo.png
│   └── types/timeline.ts
│
├── shorts_ai_roles_prompt_pack/    # LLM role prompt templates (7 roles)
│   ├── 01_transcript_analyst/      # Extracts segments, intent, value moments
│   ├── 02_hook_strategist/         # Generates 21-formula opening + ending hooks
│   ├── 03_headline_writer/         # Writes visual headlines and title badges
│   ├── 04_editorial_judge/         # Scores and selects the best hook
│   ├── 05_subtitle_qa/             # Validates subtitle accuracy and timing
│   ├── 06_content_packager/        # YouTube title, description, tags, hashtags
│   ├── 07_voice_director/          # TTS performance direction + voice selection
│   └── manifest.json
│
├── mcp_server/server.py            # MCP protocol server for agent integration
├── design-system/                  # Visual design reference
├── docs/                           # Audit reports + benchmarks
└── .gitignore
```

---

## Core Subsystems — Deep Dive

### 1. Viral Clip Selector (`viral_clipper.py`)

The clip selection engine doesn't guess — it scores every transcript segment on **four independent virality vectors**:

| Vector | What it measures |
|---|---|
| **Hook strength** | Curiosity words, stakes, specificity, "you"-address, concrete numbers |
| **Engagement signal** | Questions, pattern-interrupts, contrarian framing |
| **Value density** | Information per second ratio, filler word penalty |
| **Shareability** | Memorable quotes, surprising reversals, audience-identity anchors |

Each segment gets a composite virality score. The top N clips are returned as candidates. The scorer also implements **21 proven hook formulas** (from the yt-script skill system) and flags which formula each winning hook maps to.

Dead air and filler words are stripped at the transcript level before scoring, so the AI never wastes processing cycles on "um", "basically", "you know".

---

### 2. Face Tracking & Dynamic 9:16 Reframing (`face_tracker.py`)

Converting 16:9 footage to 9:16 without cutting off the speaker is a hard problem. The solution uses a **two-tier computer vision chain**:

**Tier 1 — YuNet ONNX Neural Face Detector** (`face_detection_yunet_2023mar.onnx`)
- Runs on downscaled 480×270 frames for speed
- Detects the largest face (primary speaker) with sub-pixel precision
- Returns center X coordinate in source resolution

**Tier 2 — Haar Cascade Fallback**
- OpenCV Haar frontal-face classifier
- Activates automatically when YuNet fails (no face, low-light, motion blur)

**EMA Smoothing** — Raw face detection produces jittery crop windows. The reframer applies an **Exponential Moving Average** over center X across frames, producing butter-smooth panning that feels like a real camera operator following the subject. The smoothing factor is tuned per scene type (talking head vs. dynamic motion).

The result is passed to FFmpeg as a `crop=W:H:x_expr:0` filter with dynamic expressions evaluated per-frame.

---

### 3. The 7-Role AI Editorial Pipeline (`editorial_orchestrator.py`)

The editorial intelligence is a **sequential multi-role LLM pipeline** where each role specializes in one narrow task and feeds structured JSON to the next. All roles run on Groq Cloud (sub-second inference on LPUs).

```
Role 01: Transcript Analyst
  → Identifies high-value segments, central idea, speaker intent, hook candidates
  → Output: analysis.json

Role 02: Hook Strategist
  → Scores 21 hook formulas against the transcript
  → Writes 3 opening candidates + 3 ending candidates
  → Recommends the best pairing with justification
  → Output: hooks.json

Role 03: Visual Headline Writer
  → Converts the winning hook into a punchy on-screen badge text
  → Adapts for the selected social card platform tone
  → Output: headline.json

Role 04: Editorial Judge
  → Scores all candidates against: Specificity, Curiosity, Stake, You-Focus
  → Gives a final verdict and disqualifies any clickbait or vague hook
  → Output: judgment.json

Role 05: Subtitle QA
  → Validates ASS subtitle file: timing accuracy, word-count per chunk,
    safe-area bounds, font rendering, encoding correctness
  → Output: subtitle_qa.json

Role 06: Content Packager
  → Writes YouTube title (≤100 chars), description (hook-first, keyword-rich),
    15 tags, 5 hashtags, and a thumbnail concept brief
  → Output: package.json

Role 07: Voice Director
  → Selects TTS voice and performance style for the voiceover hook
  → Writes delivery direction: pacing, emphasis words, pause beats
  → Output: voice_direction.json
```

**Zero-hallucination enforcement**: Each role receives a structured JSON schema and must output strictly valid JSON. Invalid outputs are retried up to 3 times before the pipeline falls back to a safe default.

**Model routing by task complexity:**
- Heavy reasoning (Judge, Analyst): `openai/gpt-oss-120b` on Groq
- Strategy + hooks: `openai/gpt-oss-20b` on Groq
- Fast packaging (title/tags/voice): `qwen/qwen3.8-27b` on Groq

---

### 4. Kinetic Subtitle Compiler (`kinetic_subtitle_compiler.py`)

This is not a subtitle renderer — it is a **WordArt typography engine** that happens to output ASS files.

Every caption is compiled from millisecond-accurate word timestamps (Groq Whisper) into **word-by-word kinetic events** in ASS (Advanced SubStation Alpha) format. Each word gets its own timed event with:
- Active-word color (highlighted)
- Rest-of-line color (dimmed)
- Scale pop animation (bounce, glow_pulse, fade_in, karaoke, typewriter, slide_up)
- Font family, outline color, shadow depth, all-caps, letter spacing

**10+ built-in visual presets:**

| Preset | Style |
|---|---|
| `bold_impact` | Impact font, white text, yellow highlight, black stroke, 118% scale pop |
| `neon_glow` | Cyan text, neon glow shadow, animated pulse |
| `3d_depth` | Extruded shadow stack, pop animation |
| `cinematic` | Space Grotesk, warm cream, letterbox feel, fade-in |
| `gradient_wordart` | Gradient-filled letters, strong outline |
| `karaoke` | Grey inactive words, one-word-at-a-time highlight |
| `comic_pop` | Bold caps, offset shadow, retro feel |
| `minimal_modern` | Clean sans-serif, minimal effects |
| `creator_bold` | Accent brand color, tight spacing |
| `typewriter` | Monospace, character-by-character reveal |

**Safe-area enforcement**: All captions are constrained to a configurable vertical band (default: bottom 22% of frame), preventing text from overlapping social cards or the speaker's face.

**HEX → ASS color conversion** handles all formats: `#RGB`, `#RRGGBB`, `#AARRGGBB`, and native `&H00BBGGRR&` ASS format.

---

### 5. Social Card Overlay Generator (`card_overlay_generator.py`)

Renders broadcast-quality **transparent PNG overlay cards** at 1080-pixel width using Pillow with anti-aliasing.

Four platform card types, each pixel-faithful to the real UI:

| Card | Style | Logo |
|---|---|---|
| **Reddit** | White card, `r/community` header, upvotes + comments bar | Real Reddit Snoo PNG |
| **X / Twitter** | Black card, Twitter Blue verified badge, heart/reply metrics | Real verified tick PNG |
| **Instagram** | Dark card, gradient avatar, ♫ audio credit, Follow CTA | Real Instagram logo PNG |
| **YouTube Superchat** | Brand-green card, black border, CA\$ amount badge | Real YouTube logo PNG |

Cards are composited into the video at a configurable Y-position and width percentage (set in Visual Style Studio, controllable per-clip in the post-generation editor).

The card text is populated dynamically from the **AI editorial pipeline output** — the hook and headline from Role 03/06 is used as the card body text so the overlay is always contextually relevant to the clip.

---

### 6. TTS Voice Hook Engine (`tts_engine.py`)

A **pluggable TTS architecture** with hot-swappable backends:

**Primary: Edge-TTS (Microsoft Neural voices)**
- `en-US-ChristopherNeural` — Male, authoritative, documentary tone
- `en-US-GuyNeural` — Male, casual, energetic
- `en-US-JennyNeural` — Female, clear, professional
- `en-US-EricNeural` — Male, conversational
- `en-US-AriaNeural` — Female, expressive storytelling

**Secondary: Kokoro ONNX** — offline open-source neural TTS, runs fully local, no network required

**Post-synthesis processing via FFmpeg:**
- Loudness normalization to `-16 LUFS` (YouTube target)
- Peak limiting to `-1 dBTP`
- Pitch and speed adjust per voice direction output

The Role 07 Voice Director LLM writes performance instructions (emphasis words, pause beats, delivery energy) that are injected as SSML-style markup before synthesis.

---

### 7. The Render Pipeline (`shorts_renderer.py` + `timeline_compositor.py`)

The final render is a **multi-filter FFmpeg composition** that assembles every element in a single pass:

```
Input: source video + audio + ASS subtitles + social card PNG + TTS hook audio

Filter chain:
  [1] crop=W:H:{speaker_x_expr}:0          ← Dynamic 9:16 speaker crop
  [2] scale=1080:1920:force_original_...    ← Target resolution scale
  [3] pad=1080:1920:(ow-iw)/2:(oh-ih)/2    ← Black letterbox pad
  [4] ass={subtitle_file}                   ← Kinetic subtitle burn
  [5] overlay={card_png}                    ← Social card composite
  [6] amix=inputs=2:duration=first          ← Mix original + TTS audio

Output: H.264 / AAC MP4, 1080×1920, ~60fps capable
```

The compositor handles all layout modes:
- **Full Screen** — 100% crop, subtitles only
- **50/50 Split** — Speaker top half, gameplay bottom half
- **Stacked** — Speaker pinned at top, background fills bottom
- **Floating** — Rounded card window over blurred backdrop
- **Card Frame** — Brutalist border card on dark background
- **PIP** — Gameplay full canvas, speaker floating corner
- **Blurred** — Centered video over blurred duplicate background

---

### 8. YouTube Publishing Pipeline (`youtube_uploader.py` + `persistent_scheduler.py`)

**OAuth 2.0 flow:**
1. User clicks "Connect YouTube" in the Channel Connect Modal
2. Backend generates OAuth authorization URL (Google Identity)
3. User grants access, callback stores refresh token in `scheduler.db` (SQLite, local only, never committed)
4. All subsequent API calls auto-refresh access tokens

**Resumable Upload Protocol (YouTube Data API v3):**
1. POST to `googleapis.com/upload/youtube/v3/videos?uploadType=resumable`
2. Receive upload session URI
3. Stream video file in chunks with `Content-Range` headers
4. YouTube processes and assigns video ID
5. Set privacy, title, description, tags, category from Role 06 output

**Job Queue + Background Worker:**
- `PersistentScheduler` stores upload jobs in SQLite with `scheduled_at` timestamp
- `BackgroundPublishWorker` runs as an async daemon (started at app lifespan)
- Worker polls the queue every 60s, fires jobs when `now >= scheduled_at`
- Failed jobs are retried up to 3 times with exponential backoff
- Job status exposed via `/api/v1/youtube/queue` endpoint

---

## Visual Style Studio

The **Visual Style Studio** is a pre-generation configuration panel that sits between the source input and the "Get Shorts" button. It configures the visual identity that will be applied consistently across all generated clips.

### Four configuration categories:

**1. Caption Styles** — 10 presets with horizontal scroll
> Select the full typography identity: font, colors, animation, outline. Then fine-tune: active highlight color, rest-of-text color, font family, animation type (word_pop / bounce / glow_pulse / fade_in / slide_up / karaoke / typewriter), all-caps toggle, outline thickness.

**2. Video Layouts** — 7 layout presets with visual previews
> Full Screen, 50/50, Stacked, Floating, Card, Blurred, PIP. Layouts with gameplay background auto-select the Minecraft background preset.

**3. Social Cards** — 5 platform cards + None
> Reddit Community, X/Twitter Post, Instagram Reel, YouTube Superchat, Quote Card, or pure video with no overlay. The card text is auto-populated from the AI pipeline's hook output.

**4. Background & Effects** — 5 background treatments
> Dark, Gradient, Blur, Custom Mint, Minecraft 4K Gameplay. When a split layout is selected, the background fills the non-speaker region.

**Advanced settings panel (collapsible):**
- Card Y-position (% from top) — independent drag control
- Card width percent (75–98%)
- Subtitle Y-position — independent from card, allows full decoupling
- Voice hook toggle + TTS voice selector

The entire config is serialized as `VisualStyleConfig` and sent with the generation request, so the backend applies it consistently to every clip in the batch.

---

## LLM Prompt Pack

The `shorts_ai_roles_prompt_pack/` directory contains the **production prompt system** used by the editorial pipeline. Each role has:

```
{role_id}/
├── system.md   ← Role identity, constraints, output schema definition
└── user.md     ← Input template with {variable} placeholders
```

This prompt-as-code pattern means you can iterate on editorial quality, change scoring weights, or add new roles without touching any Python code. The orchestrator loads prompts at runtime from the filesystem.

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Frontend framework | Next.js 15 + React 19 | App Router, server components, streaming |
| Styling | Tailwind CSS 3.4 | Utility-first, design token consistency |
| Backend framework | FastAPI 0.111 | Async-first, automatic OpenAPI, Pydantic v2 |
| LLM inference | Groq Cloud | LPU hardware = sub-100ms response on 70B models |
| Speech-to-text | Groq Whisper Large v3 Turbo | Word-level timestamps, fastest Whisper deployment |
| Video composition | FFmpeg | The only tool that handles every filter we need in one pass |
| Face detection | OpenCV YuNet ONNX 2023 | State-of-art face detection, offline, fast |
| Image rendering | Pillow (PIL) | Social card compositing, logo blending |
| TTS voice synthesis | Edge-TTS + Kokoro ONNX | High quality, free, no per-character billing |
| YouTube API | Google Data API v3 | Official resumable upload + OAuth 2.0 |
| Scheduling | SQLite + asyncio daemon | Zero-dependency, works offline, persistent across restarts |
| Testing | pytest + httpx | 13 test modules covering all services |
| Type safety | Pydantic v2 (backend) + TypeScript strict (frontend) | Prevents entire classes of runtime errors |

---

## Setup & Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- FFmpeg installed and on PATH (`ffmpeg -version` should work)
- A [Groq API key](https://console.groq.com/) (free tier is enough to start)
- A Google Cloud project with YouTube Data API v3 enabled (for publishing)

### 1. Clone the repo

```bash
git clone https://github.com/Abhyodaya1/Shortify.git
cd Shortify
```

### 2. Backend setup

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp ../.env.example .env
# Then edit .env — add your GROQ_API_KEY at minimum
```

### 3. Frontend setup

```bash
cd frontend
npm install
```

### 4. Run everything

**Option A — Convenience scripts (Windows)**
```bash
# From project root:
run_backend.bat    # starts FastAPI on http://localhost:8000
run_frontend.bat   # starts Next.js on http://localhost:3000
```

**Option B — Manual**
```bash
# Terminal 1 — Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### 5. Connect your YouTube channel (optional)

1. Click the YouTube icon in the top nav → "Connect Channel"
2. Complete the OAuth flow in the popup
3. Your channel is now connected for scheduled publishing

---

## Environment Variables

Create a `.env` file in the project root:

```env
# Required
GROQ_API_KEY=gsk_...                    # Groq Cloud API key

# Optional — LLM model routing (defaults shown)
GROQ_MODEL_REASONING=openai/gpt-oss-120b
GROQ_MODEL_STRATEGY=openai/gpt-oss-20b
GROQ_MODEL_FAST=qwen/qwen3.8-27b

# Optional — YouTube OAuth (set via UI flow, not manually)
YOUTUBE_CLIENT_ID=...
YOUTUBE_CLIENT_SECRET=...

# Optional — TTS backend
TTS_BACKEND=edge_tts                    # edge_tts | kokoro
TTS_DEFAULT_VOICE=en-US-ChristopherNeural
```

---

## API Reference

The backend exposes a full REST API documented at `http://localhost:8000/docs` (Swagger UI auto-generated by FastAPI).

### Key endpoints:

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/viral/analyze` | Analyze video and return scored clip candidates |
| `POST` | `/api/v1/viral/generate` | Generate Shorts from selected clips |
| `GET` | `/api/v1/shorts/preview/{filename}` | Stream rendered MP4 |
| `GET` | `/api/v1/shorts/download/{filename}` | Download rendered MP4 |
| `POST` | `/api/v1/youtube/connect` | Initiate YouTube OAuth flow |
| `GET` | `/api/v1/youtube/queue` | List scheduled publish jobs |
| `POST` | `/api/v1/youtube/queue/{job_id}/publish-now` | Trigger immediate publish |
| `DELETE` | `/api/v1/youtube/queue/{job_id}` | Cancel scheduled job |
| `GET` | `/api/v1/youtube/worker/status` | Check background worker status |
| `GET` | `/health` | Health check |

---

## Running Tests

```bash
cd backend
pytest tests/ -v
```

The test suite covers 13 modules:
- `test_viral_clipper.py` — Virality scoring, hook formula matching
- `test_kinetic_subtitle_compiler.py` — ASS generation, color conversion, timing
- `test_word_aligner.py` — Timestamp extraction and validation
- `test_editorial_orchestrator.py` — 4-role pipeline, JSON schema enforcement
- `test_timeline_compositor.py` — Full render pipeline integration
- `test_tts_engine.py` — Voice synthesis backends
- `test_shorts_mvp.py` — End-to-end MVP workflow
- `test_e2e_workflow.py` — Full user journey simulation
- And more...

---

## Project Philosophy

**Everything is a pipeline, not a monolith.**
Every stage — transcription, scoring, hook writing, subtitle compilation, rendering, publishing — is a separate, testable, replaceable service. You can swap Groq for OpenAI, Edge-TTS for ElevenLabs, or FFmpeg for Remotion without touching anything else.

**Prompts are code.**
The `shorts_ai_roles_prompt_pack/` directory is part of the source code. Each role's editorial behavior is defined in plain Markdown, versioned in git, and loaded at runtime. Improving clip quality is an edit to a `.md` file, not a code deploy.

**The visual config travels with the job.**
`VisualStyleConfig` is serialized at generation time and stored with each clip. If you regenerate a clip, it remembers your visual preferences. This prevents the nightmare of re-selecting 12 settings every time.

**Zero lock-in.**
No proprietary render format, no cloud storage dependency, no mandatory subscription. Your videos go to a local folder. Your API keys are yours. The OAuth tokens never leave your machine.

---

## Roadmap

- [ ] Automatic transcript language detection + multilingual captions
- [ ] Face tracking with multi-speaker switching (podcast mode)
- [ ] A/B thumbnail generation via DALL-E / Imagen
- [ ] Batch processing from a full YouTube channel
- [ ] TikTok + Instagram Reels direct publishing
- [ ] Remotion-based animation renderer (alternative to FFmpeg ASS)
- [ ] Self-hosted Whisper (faster.whisper) for offline transcription

---

## License

MIT License — do whatever you want, attribution appreciated.

---

<div align="center">

Built with frustration at slow workflows, and fixed with 7 LLM roles, one FFmpeg filter chain, and a lot of ASS subtitle engineering.

**[GitHub](https://github.com/Abhyodaya1/Shortify)** · **[Issues](https://github.com/Abhyodaya1/Shortify/issues)**

</div>
