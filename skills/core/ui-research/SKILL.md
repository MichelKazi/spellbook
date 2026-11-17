---
name: ui-research
description: Scout how similar/competitor apps solve a UI/UX problem before designing. Use when asked to research competitors, gather design inspiration, "look at how X does Y", collect UI patterns/screenshots, or benchmark an interface against the market. Captures real UI (browser automation), text patterns (WebFetch), or user-supplied screenshots, then produces a per-app teardown scored against the design skill's Cognitive Priority Matrix and ends with concrete direction for what to build.
---

# UI Research

Scout how other products solve the same problem, then turn it into direction. Output is opinionated: what works, what fails, what we do better — not a screenshot dump.

This skill feeds the `design` skill. Score every observation against that skill's **Cognitive Priority Matrix** (Tier 0 access → Tier 1 clarity → Tier 2 efficiency → Tier 3 delight). A pattern that looks slick but fails a high tier is a thing to *beat*, not copy. Invoke `design` for the matrix definitions; don't restate them here.

## 1. Scope the research (before capturing anything)

Pin these down — ask the user only if unclear:

- **The job:** the one screen/flow/problem under study (onboarding, empty state, settings, data table, checkout). Research one job at a time.
- **The set:** 3–5 reference apps. Direct competitors plus 1–2 best-in-class outsiders (the ones known for nailing this exact pattern). More than 5 dilutes; fewer than 3 isn't a sample.
- **Platform:** web vs iOS vs Android — determines which `design` sub-skill the findings route into and which conventions count as table stakes.

## 2. Capture — use what's available, fall back gracefully

Try in this order. The goal is the richest signal obtainable without blocking on setup.

**a. User screenshots (highest signal, zero setup).** If the user can paste screenshots of the apps that matter, ask for them — Claude reads images natively and this beats any scrape. Always offer this path; prefer it for the 2–3 apps that matter most.

**b. Browser automation (real live UI).** When screenshots aren't supplied and visuals matter, drive a real browser:
- Playwright MCP if connected (search tools for `playwright`/`browser`), or
- the `agent-browser` skill (Vercel CLI — `command -v agent-browser`; install: `npm install -g agent-browser && agent-browser install`).
Navigate to the app/marketing site, screenshot the target flow, capture the accessibility snapshot for structure. Public marketing pages and docs are fair game; don't attempt auth-walled flows without the user's credentials and explicit go-ahead.

**c. WebFetch (text patterns, always available).** Search tools for `WebFetch`. Pull design teardowns, pattern-library entries (Mobbin, Page Flows, Refactoring UI, NN/g case studies), app-store screenshots + copy, changelog/redesign writeups. Yields described patterns and rationale even when you can't see the live pixels.

State which method produced each finding so confidence is legible. If only (c) was possible, say the teardown is description-based, not visual. Never describe a screenshot you didn't actually capture or an app UI you couldn't reach — a confident visual teardown of pixels you never saw is the most dangerous inferred claim, because it doesn't read as one. Name the capture gap and move on (see global CLAUDE.md Operating Instructions).

## 3. Teardown — per app

For each reference app, on the target job only:

- **Pattern:** what they actually do (layout, hierarchy, the primary action, motion, the key interaction). One tight paragraph or labeled shots.
- **Works:** what's genuinely good and *why*, mapped to a tier — e.g. "one unambiguous primary action (Tier 1)", "44pt targets with real spacing (Tier 0)", "progressive disclosure keeps the first screen calm (Tier 2)".
- **Fails:** where it breaks a tier — e.g. "color-only state, fails Tier 0", "uniform cards flatten ranking, Tier 1", "decorative motion on a dense screen, Tier 2/3", or matches the AI-slop default cluster.
- **Steal / beat:** copy the pattern, or name the specific improvement.

Skip the symmetric "pros and cons for every app" reflex — call the verdict. If a pattern is the right answer, say so and move on.

## 4. Synthesis — the payoff

Close with direction, not a recap:

- **Convergent patterns:** what (nearly) everyone does — usually table stakes from Jakob's Law (users expect what they've seen elsewhere); deviate only with reason.
- **The gap:** what they all do badly or skip — the opening to be better.
- **Recommendation:** the concrete direction for *our* build — primary action, hierarchy, the one signature move, what to deliberately leave out. This is the handoff into `design`.

Keep emphasis scarce: pick the few patterns that matter. A research doc where everything is highlighted has the same Von Restorff failure as a UI where everything is bold.

## Output destination

Default: inline teardown + synthesis. For a standalone reference doc, write it where the user's instructions say notes go (global or repo AGENTS.md/CLAUDE.md); if they say nothing, ask once. Note real screenshots can't embed in markdown; reference them by app/flow and keep image files alongside the doc if saved.
