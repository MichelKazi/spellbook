---
name: design
description: Master router and source of truth for any UI/UX design or design-review work — web, mobile, or component. Use when asked to design an interface, build/reshape UI, review or critique a design, choose layout/typography/color/motion, audit accessibility, or judge whether something looks like "AI slop". Routes to frontend-design, sosumi, and slopbliterator, and arbitrates every conflict through the Cognitive Priority Matrix below. This skill and its matrix override the sub-skills wherever they disagree.
---

# Design (router + source of truth)

This is the entry point for all design work. It does three things:

1. **Arbitrates** every design decision through the Cognitive Priority Matrix below — a strict tier hierarchy where informational clarity defeats decoration.
2. **Routes** to the specialist skills for execution detail.
3. **Overrides** the specialists wherever they conflict with the matrix. When a sub-skill's advice contradicts a higher tier here, this skill wins.

The matrix is grounded in cognitive psychology (cognitive load theory, Gestalt, Fitts, Treisman, Kahneman) and Anthropic's anti-slop guidance, not taste. Tiers are ranked: a higher tier is **never** compromised to serve a lower one.

## Routing

Load the specialist for execution, then apply the matrix to its output:

| Task | Route to | This skill governs |
|------|----------|--------------------|
| Web UI: aesthetic direction, hero, typography, palette, layout, motion | `frontend-design` (anthropics/skills) | Distinctiveness must not violate Tier 0–1. Boldness spent in one place. |
| Mobile (iOS/Android/React Native): platform conventions, touch targets, navigation, a11y | Platform HIG via `sosumi` (Apple) or Material docs | Platform minimums are Tier 0 floors, not suggestions. |
| Any written output: UI copy, labels, errors, commits, PRs, docs | `slopbliterator` | Always active. Label clarity is Tier 1 (information scent). |

Process skills (`brainstorming`, `systematic-debugging`) still run first when the task calls for them. For a multi-screen or greenfield design, brainstorm direction before invoking this matrix to build.

## The Cognitive Priority Matrix

A visual element earns its place or it is noise. Work top-down. Never trade a higher tier for a lower one.

### Tier 0 — Inviolable
Perceptual and motor access. If these fail, nothing else matters — the user literally cannot perceive or operate the interface. A Tier 0 failure blocks release.

- **Contrast floors:** body text ≥4.5:1 (WCAG AA), aim 7:1 (AAA) where feasible; UI components and focus indicators ≥3:1. Never lower contrast for aesthetic "softness".
- **Touch/click targets:** ≥44×44pt (Apple) / 48×48dp (Material), ≥8dp spacing. Account for the finger-pad floor — a 44pt target is smaller than the pad landing on it. Use screen edges/corners (infinite target depth) for high-frequency actions.
- **Clickability signifiers:** interactive elements must look interactive. This is the core flat-design failure — don't strip affordances for cleanliness.
- **Plain-language status and error feedback:** say what happened and how to fix it.
- **Don't encode meaning in color alone:** ~8% of men have color-vision deficiency; luminance contrast, not hue, drives legibility.

### Tier 1 — Structural clarity
How users parse and navigate. Compromise only with strong evidence (a test result, not a preference).

- **Information scent:** descriptive, differentiated labels. Never trade label clarity for cleverness or brevity. Vague/decorative labels destroy a user's ability to predict where a path leads.
- **Visual hierarchy:** exactly one clear primary action per view (Von Restorff). Meaningful figure-ground depth. No uniform shadows/gradients — when every element has the same shadow, the brain can't tell what's above what.
- **Gestalt grouping:** proximity, common region, similarity used to encode *real* relationships. Chunk navigation and forms by meaning.
- **Pre-attentive encoding:** carry the single most important distinction in ONE strong channel (color OR size OR position), never a conjunction — conjunctions force slow serial search.

### Tier 2 — Cognitive efficiency
Reducing load and decision friction. Negotiable, test-driven.

- **Minimize extraneous load; progressive disclosure:** hide complexity until needed.
- **Chunk by meaning** — not 7±2 dogma (see overrides).
- **Choice management:** apply Hick's Law to *unfamiliar* choice surfaces only; practiced/familiar choices bypass it. Provide smart defaults (the best-evidenced lever) and fast "good enough" paths — most users satisfice.
- **Peak-End design:** engineer an early onboarding win, end flows on a high, turn errors into recoveries.

### Tier 3 — Conditional delight (first to cut)
Aesthetics, motion, brand. Fully negotiable, only after Tiers 0–2 pass, and never to *mask* a usability defect.

- **Aesthetic-Usability Effect** justifies real visual quality — beauty earns trust — but it can also hide defects in testing. If a change improves aesthetic ratings but degrades task metrics, revert.
- **Motion** only when it communicates state, guides attention, or confirms an action (≤~0.3s), and only on low-load screens. One orchestrated page-load beats scattered micro-interactions. On a high-load screen, animation frustrates rather than delights.
- **Distinctiveness** comes from restraint and intentional, consistent choices — not piled-on gradients, parallax, and custom cursors. Linear/Stripe/Notion are distinctive through quiet baselines.

## The five-test gate

An element earns its place if it passes at least one. It is noise if it fails all five.

1. **Perception** — improves legibility, target acquisition, or figure-ground? (Tier 0)
2. **Grouping/scent** — encodes a real relationship or improves path prediction? (Tier 1)
3. **Load** — reduces extraneous load, or at minimum adds none? (Tier 2)
4. **Communication (motion)** — can you name the specific state-change it shows? If not, it doesn't move.
5. **Distinctiveness** — one of a *small* number of emphases? If everything is distinctive, nothing is.

Canonical noise: uniform cards on homogeneous content, decorative gradients, identical shadows everywhere, ambient animation. These exist only to look "modern" and carry zero information.

## AI slop = hierarchy failure (not just bad taste)

Slop is measurable: it flattens hierarchy and adds extraneous load. The fix is the matrix, not "more polish".

- **Distributional convergence** — without direction, output samples the high-probability center. Banned default cluster: Inter/Roboto/system fonts, purple-on-white gradients, identical card grids, predictable layouts. (`frontend-design` carries the full avoid-list; `slopbliterator` carries the prose equivalent.)
- **Card overuse** de-emphasizes ranking and is less scannable than a list. Use lists for homogeneous, ranked content; reserve cards for genuinely independent objects.
- **Over-correction is also slop.** Escaping generic by adding complexity is just noise with more steps. Distinction needs a quiet baseline (Prägnanz, Von Restorff).

## Overrides — where this skill corrects folklore

Apply these even if a sub-skill, a brief, or training instinct says otherwise:

- **7±2 is a myth for on-screen options.** It governs items held *in working memory*, not items *visible* on screen. Don't cap menus/options at 7. Real working-memory limit is ~3–5 chunks. Broad, link-rich pages can beat sparse ones. Keep the valid part: chunk related items so each group reads as one unit.
- **Paradox of Choice is conditional, not a law.** Meta-analysis across 50 experiments: mean effect ≈ zero. It only bites when options are comparable, undifferentiated, stakes feel high, and users lack expertise. Treat "fewer options" as a hypothesis to A/B test, not a rule. The robust lever is smart **defaults**.
- **Beauty is subordinate to clarity.** The Aesthetic-Usability Effect is real but double-edged — it can mask defects. Never let Tier 3 outrank Tier 0–2.
- **The laws are heuristics with boundaries.** Hick's fails for practiced responses; Fitts assumes a known input modality but touch grip is unpredictable. Validate in context; don't cite exact millisecond/conversion figures as benchmarks without verifying them.

## Process

1. **Audit Tier 0 first.** Contrast, target sizes + spacing, clickability signifiers, plain-language errors, no color-only meaning. Any failure blocks everything else.
2. **Fix structural clarity (Tier 1).** One primary action per view; lists vs cards by content homogeneity; remove flattening shadows/gradients; labels pass the scent test; one pre-attentive channel for the key distinction.
3. **Tune efficiency (Tier 2), test-driven.** Progressive disclosure on complex flows; group form fields; sensible defaults; A/B test option-set size rather than assuming less is more.
4. **Invest in delight last (Tier 3), within constraints.** Distinctive type/color/motion only after 0–2 pass; justify every animation by the state it communicates; keep emphasis scarce. Revert anything that improves looks but hurts task metrics.

**Governance for any design system:** encode *negative* constraints (the banned default cluster), require the full set of interaction states (focus/disabled/error/empty/loading), and tokenize depth/elevation so polish can't drift into slop.

**When iterating on a live design, change one axis per round and show the rendered result** (screenshot/preview — `ff-shot` for staging routes), not a described intent. End each round by naming the tunable knob and the file it lives in, so the next tweak is one word ("tighter → `--space-2` in tokens.css, currently 8px"). New feedback surfacing a new symptom means re-diagnose, not retry the last fix (see global CLAUDE.md Operating Instructions).

## Quick floors

- Contrast: text 4.5:1, large text 3:1, components/focus 3:1.
- Touch targets: 44pt (iOS) / 48dp (Android), ≥8dp apart.
- Feedback: touch response <100ms; motion ≤~0.3s; animations 60fps; show a loader past ~1s.
- One primary action per screen.
