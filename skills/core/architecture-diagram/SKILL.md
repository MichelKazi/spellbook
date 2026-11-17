---
name: architecture-diagram
description: >
  Create clean, tiered C4-style service/architecture diagrams for a project or subsystem.
  Trigger when the user asks to diagram, map, or visualize a system's architecture, services,
  components, or dependencies; wants a "high/mid/low level" or "C4" or "context/container/component"
  diagram; says "architecture diagram", "system map", "service map", "diagram this service",
  "zoom in/out" on an existing diagram, or wants to go deeper/higher-level on one. Also trigger
  when producing architecture docs for a repo. Authors D2 (source of truth), renders to SVG/PNG,
  visually verifies layout, mirrors to Mermaid for inline viewing, and persists the note.
---

# Architecture Diagram — Tiered C4 System Maps

Author tiered architecture diagrams in **D2** (source of truth, best auto-layout), render to
SVG/PNG, **visually verify** the rendered image, mirror to **Mermaid** for native
Obsidian/GitHub viewing, and persist the note. draw.io export on demand only.

## Core rules

- **D2 is the only maintained file.** Mermaid and draw.io are generated artifacts — never hand-edit them; edit the `.d2` and re-render.
- **One `.d2` per project**, tiers as D2 `layers` (see [C4 tiers](#c4-tiers)). `d2` renders each layer to its own SVG/PNG (`out/index.svg` = top tier, `out/<layer>.svg` = deeper tiers).
- **Black-box high, zoom low.** Only expand containers/components that carry complexity or risk. Redundant detail at a high tier is the #1 clutter cause — resist it.
- **Every element states its type and technology; every diagram has a standalone title.** A diagram a viewer can't read without the surrounding note has failed.

## Workflow

### 1. Scope
Ask (or infer) two things: **which project/service or subsystem**, and **which tier(s)**. Default to High + Mid; add Low only for a named complex subsystem. Derive `{project}` from the repo directory name.

### 2. Gather structure (capture enough, not everything)
Pull the real structure — do not invent services. Use what exists:

- **graphify** — `graphify explain "X"` / `graphify query "..."` / `graphify affected "X"` against the project's `graphify-out/graph.json`. This is the primary source when a graph exists. See the `graphify` skill.
- **Contracts** — dependency edges from proto/GraphQL/OpenAPI schemas, event topics, and client libraries.
- Fallback: read the repo directly (entry points, config, service definitions, deploy manifests) if no graph exists.

Decide per tier what to black-box vs expand using [what-goes-where](#what-goes-at-each-tier).

### 3. Author D2
Write `{project}-architecture.d2` with one layer per tier. Follow `references/d2-c4-patterns.md` for the C4 element conventions, layer structure, and the ELK layout config. Keep the top layer to ~5-9 boxes; push detail down a tier rather than cramming.

### 4. Render + visually verify (the loop)
```bash
d2 --layout elk {project}-architecture.d2 out/diagram.svg   # renders index.svg + one svg per layer
d2 --layout elk {project}-architecture.d2 out/diagram.png   # PNG for vision check
```
Then **check pixel dims** (`sips -g pixelWidth -g pixelHeight out/diagram.png`) and **Read the PNG** (each tier). Critique against the checklist in `references/verify-checklist.md`: aspect ratio past ~3:1 (most common defect — switch to `direction: down` and flatten nested boxes), edge crossings, overlapping labels, orphan nodes, a box with >9 children (should be a deeper tier), unreadable density. If it fails, change **one axis** (layout engine, direction, or which box expands), edit the D2, and re-render — don't change three things then re-read and guess which helped. **Max 2 iterations** — if still bad after 2, report what's off rather than looping.

Use `--layout dagre` if ELK produces worse results for a given diagram; note which engine in the D2 header.

### 5. Emit Mermaid mirror
For each tier, generate the equivalent Mermaid and validate/render it via the **mcp-mermaid** MCP (tool: render/validate; export `file` mode to PNG) or local `mmdc -i tier.mmd -o tier.svg`. Embed the Mermaid **code block** in the note (inline-editable, renders natively in Obsidian/GitHub). This is a mirror of the D2 — regenerate it whenever the D2 changes.

C4 in Mermaid uses `C4Context` / `C4Container` / `C4Component` blocks (flagged experimental) or plain `graph TD` for robustness. Prefer `graph TD` when the C4 blocks render poorly.

### 6. Persist
Write the note where the user's instructions say notes go (global or repo AGENTS.md/CLAUDE.md). If they say nothing, ask once, then default to `docs/architecture/` in the repo.

Note structure: title, one-paragraph scope, then per tier: `![[<tier>.svg]]` (D2 render) + a collapsible Mermaid mirror block. Keep the `.d2` and rendered SVGs alongside.

### 7. draw.io (on demand only)
Only when the user asks for a GUI-editable copy: hand the D2's structure to the `drawio` skill to emit an editable `.drawio`. Not part of the normal render.

## C4 tiers

Map the user's High/Mid/Low to C4 levels. You do **not** need all levels — Context+Container cover most needs.

| User tier | C4 level(s) | Shows | Black-box |
|-----------|-------------|-------|-----------|
| **High** | Context + Container | The system among users & external systems; then deployable apps/services/data stores + tech | Everything inside a container |
| **Mid** | Component | Inside one container: its major components/modules + responsibilities | Class-level code |
| **Low** | Code, or a zoomed subsystem | Inside one component, or a focused slice of the system with less black-boxing | Nothing — this is the zoom-in |

### What goes at each tier
- **High/Context**: 1 system box + users (people) + external systems it talks to. No internals. Answers "what is this and who/what does it touch."
- **High/Container**: the deployable units — services, web apps, mobile apps, databases, queues — each with its technology. Edges labeled with protocol/purpose. This is usually the most valuable single diagram.
- **Mid/Component**: pick ONE container, show its internal components and their responsibilities. Only draw this for containers with real internal complexity.
- **Low/Code or zoom**: pick ONE component (or one risky flow) and show class/function-level structure, or a de-black-boxed slice spanning a couple containers. Draw rarely, on request.

See `references/` for D2 patterns, C4 conventions, and the verification checklist.
