# BASELINE AUDIT: Personal AI YouTube Shorts Generator MVP

**Date:** November 11, 2026  
**Auditor:** Antigravity Coding Agent  
**Repository Working Directory:** `c:\Users\ASUS\Desktop\clipperfree`  
**Specification References:** `shorts_mvp_documentation_pack/` (`00` through `05`)  
**Hardware Profile:** NVIDIA GeForce RTX 3050 Laptop GPU (4 GB VRAM), 8 GB RAM, Windows 11  

---

## 1. Executive Summary

A comprehensive reconnaissance of the existing repository was conducted against the specifications in `shorts_mvp_documentation_pack/`. The current codebase contains a working proof-of-concept pipeline consisting of:
- A Next.js 15 App Router frontend (`frontend/components/PersonalShortsStudio.tsx`)
- A FastAPI backend (`backend/app/main.py`, `backend/app/api/shorts_mvp_api.py`)
- Python services for video ingestion (`video_ingestion.py`), OpenCV/YuNet face detection (`face_tracker.py`), heuristic/Gemini clip selection (`clip_selector.py`), FFmpeg rendering (`shorts_renderer.py`), and hook scoring (`viral_clipper.py`).

While the system is able to produce vertical 9:16 MP4s, several critical deterministic defects, architectural bottlenecks, and missing components prevent it from meeting the "desirable result" standard defined in `00_README_and_Roadmap.md`.

---

## 2. Current Implementation Analysis

### 2.1 Backend Architecture & Services

| Service Module | Current Behavior | Observed Implementation State |
|---|---|---|
| `video_ingestion.py` | Downloads YouTube stream using `yt-dlp` and captions via `youtube_transcript_api`. Handles local uploads by copying to `backend/storage/uploads`. | Functional, but fallback cues are generic hardcoded strings. No audio track validation or probe caching. |
| `clip_selector.py` | Sliding window over transcript cues with duration boundaries (27.0s–35.0s for 31s; 40.0s–50.0s for 45s). Heuristic 6-parameter scoring. | **Defective**: Loops break on the very first cue exceeding minimum duration (see Section 3.1). LLM is only called to generate 3 hooks on pre-sliced text; LLM has zero role in understanding or segment discovery. |
| `viral_clipper.py` | 5-property hook scoring (Length, Punchiness, Curiosity, Word Choice, Clarity) and dead air detection. | Functional heuristic rules, but isolated from the main rendering loop. |
| `face_tracker.py` | Runs OpenCV `FaceDetectorYN` (YuNet ONNX) sampled at 3 fps, computes EMA smoothing (`alpha=0.20`) to produce keyframe crops. | **Defective**: While dynamic keyframes are calculated, the renderer discards them and averages them into a single static `optimal_crop_x` (see Section 3.2). |
| `shorts_renderer.py` | Generates ASS subtitle file, builds FFmpeg filterchain (`crop`, `scale`, `pad`, `drawtext`, `subtitles`), executes FFmpeg with `h264_nvenc` or `libx264`. | **Defective**: Subtitle animation is crude pseudo-highlighting (only colors middle word), hook text can clip across boundaries, no safe-area margin validation, no face occlusion detection. |
| `llm_provider.py` | Interfaces with Google Gemini via `google-genai` SDK using `gemini-3.8-flash`. | Functional, with deterministic mock fallback. |

### 2.2 Storage & Persistence

Currently, state is purely ephemeral in-memory Python dictionaries inside `shorts_mvp_api.py`:
- `ingested_videos: Dict[str, Any] = {}`
- `discovered_clips: Dict[str, Any] = {}`

Any backend restart wipes all ingested videos and candidate clips. Rendered MP4s and uploaded videos remain on disk in `backend/storage/uploads/` and `backend/storage/renders/`, but metadata, prompt parameters, profile settings, and human ratings are not stored in any database or JSONL dataset.

---

## 3. Traced Defects & Root Causes

### 3.1 The 28.53-Second Duration Anomaly (Identified & Traced)

**Symptom:** In previous evaluations, all rendered clips were approximately 28.52 to 29.02 seconds in duration (e.g. `short_35e3536c.mp4` was 28.520s, `short_602f5d33.mp4` was 28.528s, `short_d1a12f9d.mp4` was 28.528s, `short_f187a68c.mp4` was 28.528s), failing the exact 31s or 45s editorial requirement.

**Root Cause Analysis:**
In `backend/app/services/clip_selector.py` (lines 34–63):
```python
target_dur = 31.0 if duration_mode == "31s" else 45.0
min_dur = 27.0 if duration_mode == "31s" else 40.0
max_dur = 35.0 if duration_mode == "31s" else 50.0

for i in range(len(cues)):
    start_t = cues[i]["start_sec"]
    span_text = []
    span_cues = []
    for j in range(i, len(cues)):
        end_t = cues[j]["end_sec"]
        dur = end_t - start_t
        span_text.append(cues[j]["text"])
        span_cues.append(cues[j])

        if min_dur <= dur <= max_dur:
            # Matches IMMEDIATELY on the very first cue exceeding 27.0s
            raw_candidates.append(...)
            break  # <--- ABORTS SEARCH FOR CLOSER FIT
```
Because typical spoken cues in YouTube transcripts are 2 to 4 seconds long, the cumulative duration jumps from ~25.5s to ~28.5s. As soon as `dur >= 27.0`, the loop matches and immediately breaks. The algorithm never optimizes for a target of 31.0s or 45.0s, nor does it look for sentence completion or speech pause boundaries near the target duration. Then, `ShortsRenderer` takes `duration = end_sec - start_sec` and cuts exactly that span, resulting in uniform ~28.5s clips.

### 3.2 Lost Dynamic Face Tracking (Static Crop Bug)

**Symptom:** In rendered clips, camera framing does not smoothly pan or follow the speaker across the screen.

**Root Cause Analysis:**
In `face_tracker.py`, `track_clip_faces()` produces a keyframe array:
```python
"keyframes": smooth_crops,  # Contains timestamp_sec and smooth_x
"optimal_crop_x": avg_crop_x,
```
However, in `shorts_renderer.py`:
```python
crop_x = crop_data.get("optimal_crop_x", 0)
vf_filters = [
    f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y}",
    ...
]
```
The renderer only applies a single static crop coordinate `optimal_crop_x` to the entire FFmpeg command. The smoothed pan trajectory calculated by the YuNet tracker is completely discarded.

### 3.3 Naive Subtitle Keyword Highlighting

**Symptom:** Kinetic subtitles do not reflect actual word emphasis or natural rhythm.

**Root Cause Analysis:**
In `shorts_renderer.py`:
```python
@staticmethod
def _highlight_keywords(text: str) -> str:
    words = text.split()
    if len(words) <= 2:
        return text
    mid = len(words) // 2
    words[mid] = f"{{\\c&H00D7FF&}}{words[mid]}{{\\r}}"
    return " ".join(words)
```
The highlighter simply calculates `mid = len(words) // 2` and highlights whatever word happens to sit in the middle of the phrase (often filler words like "the", "and", "that"). Furthermore, this is applied at the cue level rather than word-level kinetic highlighting.

### 3.4 Subtitle Safe-Area & Face Occlusion Risk

**Symptom:** Long subtitle phrases risk colliding with YouTube Shorts UI overlays (channel icon, title, bottom progress bar) or covering the speaker's mouth.

**Root Cause Analysis:**
The ASS stylesheet in `_create_ass_subtitles()` uses static `MarginV: {int(height * 0.22)}` with `Arial` font and no text measurement, no line wrapping verification, and no collision bounding-box checking against the speaker's detected face box.

### 3.5 Monolithic / Heuristic Clip Selection

**Symptom:** Clips are selected by keyword counts (e.g. counting words like "fatal", "insane", numbers) rather than genuine narrative comprehension, opening setup, and payoff delivery.

**Root Cause Analysis:**
The AI model (`gemini-3.8-flash`) was relegated to only generating 3 hook sentences on already-sliced spans. Content understanding, semantic boundary detection, context sufficiency, and payoff evaluation were missing entirely.

---

## 4. Missing Functionality (Gap Analysis vs Spec)

| Required Component (`00`–`05` Specs) | Status | Required Implementation |
|---|---|---|
| **Persistent Editorial Profile** | **Missing** | Centralized `EditorialProfile` model, local JSON/SQLite persistence, snapshotting per job, `GET/PUT /api/profile`. |
| **Intelligent Multi-Stage AI Pipeline** | **Missing** | Split into Content Understanding, Candidate Discovery, Ranking/Rejection, Hook Generation, and Payoff Validation. |
| **Hook Evaluation Checklist (21 Formulas)** | **Partial** | Hook scoring exists in `viral_clipper.py` but must be integrated into the selection pipeline with weakest-link weighting and promise-vs-payoff checking. |
| **Cinematic Kinetic Subtitle Engine** | **Partial** | Replace middle-word coloring with word-by-word dynamic highlighting, safe-area boundary enforcement, and style presets (`kinetic_editorial`). |
| **Dynamic Speaker Framing Filter** | **Partial** | Pass trajectory keyframes or smooth crop windows to FFmpeg or frame crop pipeline; implement safe headroom and fallback. |
| **Deterministic Quality Assurance (QA)** | **Missing** | Automated post-render checks: duration compliance (within ±0.5s of target), aspect ratio 9:16, audio sync, black frame detection, subtitle safe-area verification. |
| **Structured Feedback Dataset** | **Missing** | Storage for user ratings, rejection reasons, edited hooks/boundaries, rights/provenance metadata, and JSONL export (`references.jsonl`, `preferences.jsonl`). |

---

## 5. Evaluation Baseline on Reference Videos

The three reference videos in `backend/storage/uploads/` from previous runs were measured as the baseline:

| Source Video File | Duration | Format | Previous Render Output | Render Duration | Baseline Defects Observed |
|---|---|---|---|---|---|
| `yt_c3a708fa.mp4` | 90.00s | 1080p, 30fps | `short_4a710153.mp4` | **29.03s** | Under-duration (-1.97s from 31s target); static crop; middle-word highlight ("the"); hook badge truncated. |
| `yt_7bd36595.mp4` | 166.46s | 1080p, 23.98fps | `short_602f5d33.mp4` | **28.53s** | Under-duration (-2.47s from 31s target); speaker shifted during speech but crop remained static; no payoff check. |
| `yt_513a092e.mp4` | 279.00s | 720p, 25fps | `short_35e3536c.mp4` | **28.52s** | Under-duration (-2.48s from 31s target); 720p scaled to 1080p with black bars; arbitrary cut mid-thought. |

---

## 6. Implementation Plan & Order

In strict accordance with `02_MASTER_AGENT_INSTRUCTIONS.md`:
1. **Editorial Profile**: Implement persistent, snapshotted profile configuration.
2. **Intelligent Clip Selection**: Target exact 31s and 45s boundaries using sentence/pause detection and 6-parameter scoring.
3. **Hook Evaluation**: Full 21-formula integration with grounding evidence, risk flags, and weakest-link score.
4. **Cinematic Kinetic Subtitles**: Word-level ASS kinetic engine, safe-area margins, and keyword accenting.
5. **Speaker-Centered Framing**: Smooth camera pans via dynamic crop filters and headroom protection.
6. **Quality Assurance Engine**: Automated technical validation for video, audio, and subtitles.
7. **Structured Feedback Dataset**: Local storage and JSONL export for human ratings and editorial training data.
8. **Evaluation & Verification**: Re-render the 3 evaluation videos, measure improvements against baseline, and document diffs.

