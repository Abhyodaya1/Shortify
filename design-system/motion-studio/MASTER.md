# Design System Master File — Motion Studio (Swiss Minimalism)

> **LOGIC:** Master design system for Motion Studio following Swiss Style & Minimalism principles.
> Overridden with the requested 60/30/10 palette, strict 8-ratio spacing, and Open Sans typography.

---

**Project:** Motion Studio  
**Design Direction:** Swiss Style & Minimalism (Generous whitespace, flat surfaces, 1px subtle borders, zero decorative gradients, single focal point)

---

## Global Rules

### 60 / 30 / 10 Minimalist Color Palette

| Role | Hex | CSS Custom Property | Ratio | Usage |
|------|-----|----------------------|-------|-------|
| Dominant Canvas | `#FAF7F2` | `--color-dominant` | 60% | Page background, canvas, main viewport |
| Surface / Card | `#F4F0EA` | `--color-surface` | 60% | Cards, containers, sidebars, modals |
| Surface Alt | `#EDE7DE` | `--color-surface-alt` | 60% | Table rows, input backgrounds, active pills |
| Secondary Text | `#3E2723` | `--color-secondary` | 30% | Primary headings, button labels, core text |
| Emphasis Text | `#2C221E` | `--color-emphasis` | 30% | High-contrast titles, hero text |
| Muted Text | `#795548` | `--color-muted` | 30% | Subtitles, helper text, labels |
| Subtle Text | `#A1887F` | `--color-subtle` | 30% | Metadata, timestamps, breadcrumbs |
| Border | `#E6DFD5` | `--color-border` | — | 1px clean minimal structural borders |
| Accent (Theme) | `#81E1DA` | `--color-accent` | 10% | Primary CTAs, active indicators, focus rings |
| Accent Hover | `#3DB8AE` | `--color-accent-hover` | 10% | Hover state for accent buttons |
| Accent Active | `#52C5BC` | `--color-accent-active` | 10% | Pressed state for accent buttons |
| Accent Tint | `#EAF9F8` | `--color-accent-tint` | 10% | Active pill background, selected states |

### Typography

- **Font Family:** `--font-sans: 'Open Sans', system-ui, sans-serif;`
- **Import:** `@import url('https://fonts.googleapis.com/css2?family=Open+Sans:ital,wght@0,300..800;1,300..800&display=swap');`
- **Scale (Fluid with clamp):**
  - `--font-size-xs: clamp(0.6875rem, 0.65rem + 0.15vw, 0.75rem);` (11-12px)
  - `--font-size-sm: clamp(0.8125rem, 0.78rem + 0.15vw, 0.875rem);` (13-14px)
  - `--font-size-base: clamp(0.9375rem, 0.9rem + 0.2vw, 1rem);` (15-16px)
  - `--font-size-lg: clamp(1.125rem, 1.05rem + 0.35vw, 1.25rem);` (18-20px)
  - `--font-size-xl: clamp(1.375rem, 1.25rem + 0.5vw, 1.625rem);` (22-26px)
  - `--font-size-2xl: clamp(1.75rem, 1.5rem + 1vw, 2.25rem);` (28-36px)
- **Line Length:** 60–75 characters for readable body prose.
- **Letter Spacing:** Tightened (`-0.02em`) on large headings; normal on body.

### Spacing Variables (Strict 8 Ratio)

| Token | CSS Custom Property | rem | px | Usage |
|-------|---------------------|-----|----|-------|
| `--space-1` | `var(--space-1)` | `0.5rem` | `8px` | Icon gaps, tight padding, inline tags |
| `--space-2` | `var(--space-2)` | `1rem` | `16px` | Standard padding, button padding, field gap |
| `--space-3` | `var(--space-3)` | `1.5rem` | `24px` | Card internal padding, intermediate gap |
| `--space-4` | `var(--space-4)` | `2rem` | `32px` | Section vertical rhythm, container padding |
| `--space-6` | `var(--space-6)` | `3rem` | `48px` | Major section gap, modal margins |
| `--space-8` | `var(--space-8)` | `4rem` | `64px` | Hero padding, page margins |
| `--space-12` | `var(--space-12)` | `6rem` | `96px` | Maximum structural spacing |

### Radii, Borders & Elevation

- `--radius-sm: 0.25rem;` (4px)
- `--radius-md: 0.5rem;` (8px)
- `--radius-lg: 0.75rem;` (12px)
- `--radius-xl: 1rem;` (16px)
- `--radius-full: 9999px;`
- `--border-width: 1px;`
- `--shadow-sm: 0 1px 2px rgba(44, 34, 30, 0.04);`
- `--shadow-md: 0 4px 12px rgba(44, 34, 30, 0.06);`
- `--shadow-lg: 0 8px 24px rgba(44, 34, 30, 0.08);`

### Motion Tokens

- `--duration-fast: 150ms;`
- `--duration-normal: 200ms;`
- `--duration-slow: 250ms;`
- `--ease-out: cubic-bezier(0.16, 1, 0.3, 1);`
- `--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);`

### Breakpoint Tokens

- `--bp-mobile: 375px;`
- `--bp-tablet: 768px;`
- `--bp-desktop: 1024px;`
- `--bp-wide: 1440px;`

---

## Anti-Pattern Checklist (Minimalism / Swiss Style)

1. No gradients or decorative colored glow blobs.
2. No neon text colors or inconsistent font mixes.
3. No arbitrary padding/margins outside `--space-1` through `--space-12`.
4. No competing primary buttons per screen.
5. Touch targets minimum 44px (`min-h-[44px]` / `min-w-[44px]`).
6. Full support for `@media (prefers-reduced-motion: reduce)`.
