---
name: Motion Studio
description: Autonomous Video Agent & AI Shorts Studio
colors:
  primary: "#183746"
  accent: "#81E1DA"
  accent-light: "#EAF9F8"
  accent-dark: "#52C5BC"
  neutral-bg: "#F6F6F6"
  surface: "#FFFFFF"
  border: "#E5E7EB"
typography:
  headings:
    fontFamily: "Merriweather, Georgia, serif"
    fontWeight: 700
  body:
    fontFamily: "Merriweather, Georgia, serif"
    fontWeight: 400
rounded:
  sm: "8px"
  md: "12px"
  lg: "16px"
spacing:
  xs: "8px"
  sm: "16px"
  md: "24px"
  lg: "32px"
  xl: "48px"
---

# Design System

## Overview

Motion Studio is an autonomous video repurposing workstation. The interface balances high-density operational controls (transcription review, multi-track timeline framing, virality vector breakdown) with clear, low-friction focal points.

## Colors

- **Primary Canvas**: `#F6F6F6` (light neutral background)
- **Primary Text & Solids**: `#183746` (Navy)
- **Accent**: `#81E1DA` (Mint) with `#EAF9F8` for subtle tint highlights
- **Surfaces**: `#FFFFFF` with 1px borders of `#E5E7EB`

## Typography

- **Headings & Display**: Merriweather bold/black (`font-bold`, `font-black`) with tight letter spacing.
- **Body & Inputs**: Merriweather regular (`font-normal`, line-height 1.65).

## Layout

- Desktop sidebar navigation with responsive collapsible mobile drawer.
- 8px ratio grid layout across margins, paddings, and gaps.
- Responsive container with fluid max-width constraints.

## Elevation & Depth

- Flat, minimal surfaces with 1px subtle borders (`#E5E7EB`).
- Soft layered shadows (`shadow-xs` / `shadow-sm`) only for elevation cues.

## Shapes

- Outer containers: `rounded-xl` (16px)
- Buttons and inputs: `rounded-lg` (8px / 12px)
- Pills and badges: `rounded-full`

## Components

- Primary CTA: Solid `#183746` with `#81E1DA` accent iconography.
- Secondary Actions: Outlined or tinted neutral `#EAF9F8` buttons with 1px borders.
- Modal Dialogs: Backdrop-blurred overlays with centered 12-column layout cards.

## Do's and Don'ts

- **Do** maintain a single primary focal CTA per screen.
- **Do** enforce 100% functional parity on all buttons, forms, and handlers.
- **Don't** use multi-color gradients, neon glow effects, or arbitrary padding.
