---
name: FinGuard
description: Multi-modal AI deepfake forensic gateway and SEBI regulatory intelligence engine
colors:
  primary: "#173f35"
  primary-hover: "#102d26"
  secondary: "#2e6653"
  secondary-lift: "#3c7f68"
  accent: "#c8a96b"
  accent-wash: "#faf4e8"
  neutral-bg: "#f3ebdd"
  neutral-surface: "#ffffff"
  neutral-muted: "#565d56"
  ink: "#282b28"
  ink-soft: "#454b45"
  border: "#ded3c1"
  border-subtle: "#eae1d0"
  status-safe: "#2e6653"
  status-warn: "#c8a96b"
  status-risk: "#b33a2b"
  status-crit: "#8a1f14"
typography:
  display:
    fontFamily: "'Outfit', 'Plus Jakarta Sans', sans-serif"
    fontSize: "clamp(2rem, 5vw, 3.25rem)"
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "'Outfit', 'Plus Jakarta Sans', sans-serif"
    fontSize: "clamp(1.4rem, 2.5vw, 2rem)"
    fontWeight: 600
    lineHeight: 1.25
  title:
    fontFamily: "'Plus Jakarta Sans', sans-serif"
    fontSize: "1.125rem"
    fontWeight: 600
    lineHeight: 1.4
  body:
    fontFamily: "'Plus Jakarta Sans', -apple-system, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.65
  label:
    fontFamily: "'IBM Plex Mono', monospace"
    fontSize: "0.8125rem"
    fontWeight: 500
    letterSpacing: "0.04em"
rounded:
  sm: "6px"
  md: "10px"
  lg: "16px"
  full: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.neutral-surface}"
    rounded: "{rounded.sm}"
    padding: "12px 24px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
  badge-verified:
    backgroundColor: "{colors.accent-wash}"
    textColor: "{colors.primary}"
    rounded: "{rounded.full}"
    padding: "4px 10px"
---

# Design System

## Overview

### Creative North Star: The Heritage Ledger & Forensic Scalpel
FinGuard embodies the trusted authority of an established regulatory audit institution paired with the precision of a modern forensic laboratory. It deliberately rejects cliché "AI-generated" dark-mode aesthetics—no gratuitous purple/cyan neon glows, no vibrating saturated gradient borders, and no vacuous minimalism that conceals critical data.

Instead, the system is grounded in a warm, tactile light palette inspired by historical central bank registries, parchment ledger paper, and rich forest green ink. The design maintains high informational density, rendering complex 9-stage ML pipeline outputs, facial landmark coordinates, acoustic spectral timelines, and SEBI statutory citations with effortless legibility.

### Core Typographic Rule
> **The machine speaks in mono. The product speaks in sans.**
- All pipeline artifacts, telemetry, confidence percentages, registration numbers, timestamps, and model names are rendered in **IBM Plex Mono**.
- FinGuard's direct voice, instructional copy, navigation, and editorial explanations are rendered in **Plus Jakarta Sans** and **Outfit**.

---

## Colors

The palette is derived from classic financial institutions: deep forest green, warm brass seals, parchment cream canvas, and sharp charcoal ink.

### Primary & Accent Roles
* **Primary (`--forest`, `#173f35`)**: Anchor color for primary action buttons, main headers, brand marks, and prominent navigation titles.
* **Secondary (`--green`, `#2e6653`)**: Interactive highlights, step indicators, verified status indicators, and secondary buttons.
* **Accent (`--brass`, `#c8a96b`)**: Warm metallic brass used for official certification seals, caution alerts, attention eyebrows, and verification stamps.
* **Accent Wash (`--yellow-bg`, `#faf4e8`)**: Soft cream tint used as background for highlights, badges, and warning contexts.

### Ground & Neutral Surfaces
* **Canvas (`--paper`, `#f3ebdd`)**: Warm cream page background providing a soft, non-glaring environment for intensive reading and audit sessions.
* **Surface (`--surface`, `#ffffff`)**: Crisp, elevated card surfaces for analysis tools, modals, form panels, and tables.
* **Border Lines (`--line`, `#ded3c1`)**: Gentle warm lines separating data grids and sections without harsh visual breaks.

### Ink & Content
* **Primary Ink (`--ink`, `#282b28`)**: Deep charcoal with high contrast for optimal reading clarity.
* **Secondary Ink (`--muted`, `#565d56`)**: Muted sage/charcoal for metadata labels, captions, and secondary descriptions.

### Forensic Status System
* **Safe / Verified (`#2e6653`)**: Clean emerald green denoting active SEBI registration, authentic media, or verified broker domains.
* **Caution / Advisory (`#c8a96b`)**: Brass amber denoting ambiguous claims, unlicensed finfluencers, or moderate acoustic anomalies.
* **High Risk / Deepfake (`#b33a2b`)**: Deep terracotta crimson denoting synthetic voice clones, face-swap manipulation, or phishing links.
* **Severe / Malicious (`#8a1f14`)**: Dark wine red reserved for malicious APK decompilation findings or counterfeit banking domains.

---

## Typography

### Font Hierarchy
* **Display & Section Headers**: `Outfit` (weights: 600, 700, 800) – Modern, geometric, authoritative character.
* **Body & UI Elements**: `Plus Jakarta Sans` (weights: 400, 500, 600) – Highly legible humanist grotesque optimized for readability at small and medium sizes.
* **Forensic Machine Data**: `IBM Plex Mono` (weights: 400, 500, 600) – Technical monospace providing tabular alignment for numbers, IDs, and code-mixed Hindi/English transcripts.

### Typographic Scale
* **Display 1 (Hero)**: `clamp(2rem, 5vw, 3.25rem)` / line-height `1.15` / tracking `-0.02em`
* **Headline 2 (Section Title)**: `clamp(1.4rem, 2.5vw, 2rem)` / line-height `1.25` / weight `600`
* **Title 3 (Card Header)**: `1.125rem` / line-height `1.4` / weight `600`
* **Body**: `1rem` (16px) / line-height `1.65` / weight `400`
* **Small / Caption**: `0.875rem` (14px) / line-height `1.5`
* **Forensic Mono**: `0.8125rem` (13px) / line-height `1.45` / letter-spacing `0.04em`

---

## Layout

### Container & Grids
* **Max Content Width**: `min(1180px, calc(100% - 48px))` centered with `margin: auto`.
* **Section Rhythm**: Generous vertical whitespace (`padding: 80px 0` desktop, `48px 0` mobile) between major thematic zones.
* **Tool Carousel**: Horizontal card track with clear slide-count indicator (`01 / 05`) and tactile next/prev arrow triggers.
* **Modal Workspace (`.tool-dialog`)**: Full-featured diagnostic overlay with fixed header, status badge, and isolated scroll area.

### Density Principles
* **Executive Mode**: Generous spacing, clear summary cards, and plain-language risk breakdowns for retail users.
* **Forensic Audit Mode**: Compact data density, side-by-side video/audio spectral scrubbers, and tabular evidence lists for B2B compliance auditors.

---

## Elevation & Depth

* **Natural Tactility Over Fake Shadows**: Avoid heavy dark dropshadows or glossy glass-blur stacks.
* **Subtle Institutional Elevation**:
  * `--shadow-card`: `0 18px 48px rgba(23, 63, 53, 0.09)`
  * `--shadow-button`: `0 3px 0 var(--blue-shadow)` (tactile physical press effect)
* **Hairline Framing**: Surfaces are bounded by `1px solid var(--line)` or `1px solid rgba(23, 63, 53, 0.12)`.

---

## Shapes

* **Corner Radii**:
  * **Interactive Controls (Buttons, Inputs)**: `6px` (`--r-sm`) – crisp and functional.
  * **Cards & Containers**: `10px`–`16px` (`--r-md`, `--r-lg`) – structured and balanced.
  * **Tags & Status Badges**: `9999px` (`--r-full`) – classic pill geometry.
* **Verification Stamps**: Circular or bordered rectangular stamps with dotted or double-rule borders evoking official administrative seals.

---

## Components

### 1. Primary Action Button (`.button-blue`)
* Background: Forest green (`#173f35`).
* Text: Pure white (`#ffffff`), font weight 600.
* Padding: `12px 24px`.
* Hover: Darkens to `#102d26` with slight forward arrow motion.

### 2. Status Badges & Stamps
* Live SEBI Verified: Brass background (`#faf4e8`), Forest text (`#173f35`), pulsing emerald indicator dot (`#2e6653`).
* Risk Warning Tags: Terracotta wash (`#fbf0ee`) with crisp dark red text.

### 3. Forensic Diagnostic Modal (`.tool-dialog`)
* Semi-transparent backdrop (`rgba(23, 63, 53, 0.4)`).
* Pure white dialog card with rounded corners (`16px`).
* Dedicated sticky header displaying the active tool name and pipeline heartbeat.

### 4. Search & Verification Input
* Clean white field bounded by warm border (`#ded3c1`), focusing to Forest green (`#173f35`).
* Inline quick-filter chips for instant test queries.

---

## Do's and Don'ts

### Do's
* **DO** use light-mode warm parchment and white cards as the primary interface.
* **DO** use `IBM Plex Mono` for every single numerical metric, confidence percentage, timestamp, and regulation code.
* **DO** preserve complete feature visibility—never tuck critical forensic parameters away under unnecessary clicks.
* **DO** cite exact SEBI regulations (PFUTP 2003, IA 2013, RA 2014, Aug 2024 Circular) next to compliance violations.
* **DO** ensure high contrast that passes WCAG 2.1 AA across all text and warning badges.

### Don'ts
* **DON'T** use purple/cyan glowing borders, neon gradients, or dark-mode synthwave tropes typical of generic AI demos.
* **DON'T** hide technical evidence behind vague one-word scores without expandable forensic logs.
* **DON'T** use generic system sans-serif for numbers or pipeline telemetry.
* **DON'T** introduce heavy drop shadows, over-blurred glassmorphism, or distracting ambient particle effects.
* **DON'T** compromise density when presenting evidence tables to compliance officers.
