# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Content creators, video podcasters, educators, and social media managers repurposing long-form YouTube/Twitch/Drive video footage into high-retention 9:16 vertical Shorts, Reels, and TikToks.

## Product Purpose

Motion (The General Video Agent) is an autonomous video repurposing studio that ingests long-form video footage, transcribes speech with Whisper-Large, analyzes retention and 4-vector virality (Hook, Engagement, Value, Shareability), crops and reframes speakers with smooth EMA centering, composits multi-layer layouts (gameplay split-screen, social post headers, superchat badges), burns kinetic styled captions, and publishes on schedule to YouTube Channels.

## Positioning

High-performance, unwatermarked 1080p 60fps vertical clip generation with automated multi-track framing, AI voiceover hooks, and direct YouTube channel auto-scheduling from a unified browser workspace.

## Operating Context

Desktop and mobile responsive web application. The creator enters video URLs or uploads files, reviews candidate clips scored by virality metrics, adjusts framing/captions, and schedules release times.

## Capabilities and Constraints

- Next.js 15 frontend with Tailwind CSS and CSS custom properties.
- FastAPI backend with FFmpeg composition, OpenCV YuNet face tracking, and SQLite scheduling queue.
- Hard constraint: Zero functional regression on all existing buttons, modal dialogs, and API endpoints.

## Brand Commitments

- Product Name: Motion (Motion Video Studio)
- Accent Color: `#81E1DA` (Mint Accent with `#52C5BC` pressed / `#3DB8AE` hover)
- Visual Style: Minimalist / Swiss Style (generous whitespace, 1px subtle borders, warm cream canvas `#FAF7F2` and `#F4F0EA`, deep espresso text `#3E2723`, and single focal point).

## Product Principles

1. One clear focal point per screen with minimal visual clutter.
2. Fast, predictable feedback for transcription, clipping, and rendering operations.
3. Accessible and resilient across all device form factors (mobile to wide desktop).
