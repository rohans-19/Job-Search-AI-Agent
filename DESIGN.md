# Design System: Job Search AI

A premium, India-focused career platform. This file is the single source of truth
for the visual language — applied to the Streamlit app via [ui_common.py](ui_common.py)
and [.streamlit/config.toml](.streamlit/config.toml), and usable as a prompt for
generating new screens (e.g. in Google Stitch).

## 1. Visual Theme & Atmosphere
Restrained and confident — a "daily app" density (4/10) with offset, asymmetric
accents (variance 7/10) and fluid spring-physics motion (6/10). The feel is a
well-lit recruiting studio: calm zinc neutrals, generous breathing room, and a
single decisive emerald that signals progress and "go". Numbers are treated as
data — set in mono — so scores and salaries read as instruments, not decoration.

## 2. Color Palette & Roles
- **Zinc Canvas** (#FAFAFA) — primary page background.
- **Pure Surface** (#FFFFFF) — cards, panels, inputs.
- **Charcoal Ink** (#18181B / zinc-900) — primary text and dark hero base. Never pure black.
- **Muted Steel** (#71717A / zinc-500) — secondary text, metadata, captions.
- **Whisper Border** (#E4E4E7 / zinc-200) — 1px structural lines and card edges.
- **Signal Emerald** (#059669 / emerald-600) — the single accent: CTAs, active states, focus rings, progress, score-positive.
- **Emerald Deep** (#047857) — hover/pressed accent and accent-on-light text.
- **Emerald Mist** (#ECFDF5) — soft accent fills (matched-skill chips, salary tags).

Constraints: max one accent, saturation < 80%. The AI purple/blue neon aesthetic
is BANNED — no purple button glows, no neon gradients. The hero uses a charcoal →
deep-teal → emerald gradient only.

## 3. Typography Rules
- **Display:** `Outfit` (700–800), `tracking-tight`, weight-driven hierarchy — headings never scream.
- **Body:** `Plus Jakarta Sans` (400–600), relaxed leading, ~65ch measure, Muted Steel for secondary copy.
- **Mono:** `JetBrains Mono` for all numbers — scores, salaries (LPA), counts, timestamps, ranks.
- **Banned:** `Inter`, generic system fonts, and all serif fonts (this is a software dashboard).

## 4. Component Stylings
- **Buttons:** Flat Signal Emerald fill, 11px radius, soft tinted shadow (no outer glow). Tactile `translateY(1px) scale(.99)` on `:active`. Dark-ink secondary action ("View role").
- **Cards:** White, 18–22px radius, 1px Whisper Border + 3px emerald left-rule, soft diffusion shadow (`0 14px 30px -22px rgba(24,24,27,.22)`). Lift `-2px` on hover. Used only where elevation conveys hierarchy.
- **Tiles:** Borderless-feel metric blocks in a CSS grid (no 3-equal-card cliché for content — tiles are data, grouped by grid + negative space).
- **Chips:** Fully-rounded skill pills from a muted six-tone palette; matched skills in Emerald Mist.
- **Status pills:** Saved (zinc), Applied (blue), Interview (amber), Offer (emerald), Rejected (red) — desaturated.
- **Inputs:** Label above, 11px radius, emerald focus ring (`0 0 0 3px rgba(5,150,105,.14)`). Error text below.
- **Loading:** Streamlit spinner with a descriptive task message; results stream into cards.
- **Empty states:** Centered glyph + one-line guidance pointing to the next action — never a bare "No data".
- **Error states:** Inline, human-readable messages mapped from exceptions (timeout / offline / auth / rate-limit).

## 5. Layout Principles
- Max content width centered; cards and grids over flexbox percentage math.
- Metrics in `repeat(N, 1fr)` CSS grids; logic grouped by space and 1px dividers, not nested boxes.
- Hero is a full-width banner with an off-axis emerald radial glow (asymmetric, not centered chrome).
- Single-column collapse on narrow viewports (Streamlit columns stack natively).

## 6. Motion & Interaction
- Easing `cubic-bezier(.16,1,.3,1)` for hover/transition; transform + opacity only (hardware-accelerated).
- Cards lift on hover; buttons depress on active for tactile feedback.
- No continuous CPU-heavy loops in this Streamlit context (server-rendered) — motion stays in CSS transitions.

## 7. Anti-Patterns (Banned)
- No `Inter`, no serif fonts, no pure black (#000000).
- No AI purple/blue, no neon or outer-glow shadows, no gradient-filled headline text.
- No 3-equal-card feature rows for content; no flexbox `calc()` hacks.
- No custom mouse cursors, no fake round numbers, no generic placeholder names.
- No AI copywriting clichés ("Elevate", "Seamless", "Unleash", "Next-Gen").

> Note on emojis: the stitch/anti-slop default bans emojis. This app keeps a small
> set of **functional** glyphs for Streamlit's filename-based page navigation only;
> in-content hierarchy is carried by typography, color, and space — not emoji.
