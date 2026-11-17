# D2 + C4 authoring patterns

D2 reference for tiered C4 diagrams. D2 renders each `layers` entry to its own file:
`out/index.svg` (base), `out/<layer-key>.svg` (each layer). One `.d2` → all tiers.

## File skeleton

```d2
# {project} architecture — source of truth. Edit here; Mermaid/draw.io are generated.
# layout: elk  (switch to dagre if elk crowds this diagram)
vars: { d2-config: { layout-engine: elk } }

# Titles: `near: top-center` floats a titled box above the graph. That is expected.
# If it reads as disconnected, prefer a `top-left` title or drop the box and title the note instead.
title: {Project} — System Context {near: top-center}

# ---- BASE LAYER = High tier (Context + Container) ----
user: Rider { shape: person }
ext: Payments API { shape: rectangle; style.stroke-dash: 3 }   # external system

system: {Project} {
  # containers live here at the Container view
  web: Web App { shape: rectangle }        # tech in the label or a tooltip
  # NOTE: a label with a shape map on one line MUST be quoted, else D2 errors on the text.
  # For multi-line labels use a literal newline inside quotes, not \n.
  api: "API Service [Scala/Thrift]" { shape: rectangle }
  db: Postgres { shape: cylinder }
  queue: Kafka { shape: queue }
}

user -> system.web: uses (HTTPS)
system.web -> system.api: gRPC
system.api -> system.db: SQL
system.api -> system.queue: publishes events
system.api -> ext: fetches activities

# ---- DEEPER TIERS as layers ----
layers: {
  api-components: {   # Mid tier: zoom into the api container
    title: {Project} — API Service Components {near: top-center}
    ctrl: Controller { shape: rectangle }
    svc: Activity Service { shape: rectangle }
    repo: Repository { shape: rectangle }
    ctrl -> svc -> repo
    repo -> db: SQL
    db: Postgres { shape: cylinder }
  }
}
```

Render:
```bash
d2 --layout elk {project}-architecture.d2 out/diagram.svg
d2 --layout elk {project}-architecture.d2 out/diagram.png   # for vision verify
# produces out/index.svg (+.png) and out/api-components.svg (+.png)
```

## C4 element conventions in D2

| C4 element | D2 shape | Notes |
|------------|----------|-------|
| Person | `shape: person` | users, actors |
| Software System (external) | `shape: rectangle` + `style.stroke-dash: 3` | dashed = not ours / black-box |
| Container (app/service) | `shape: rectangle` | state technology in label: `"API [Scala]"` (quote labels that carry a shape map) |
| Data store | `shape: cylinder` | DBs, caches |
| Queue/topic | `shape: queue` | Kafka, SQS |
| Component | `shape: rectangle` (nested) | inside a container container |
| Boundary | a D2 container `system: { ... }` | groups containers; label it |

- **Technology on every container/component** — in the label (`\n[tech]`) or `tooltip`.
- **Label every edge** with protocol or purpose (`gRPC`, `publishes events`), directional.
- **Standalone title per layer** via `title: ... {near: top-center}`.
- Keep base layer to **~5-9 boxes**. More = push into a deeper layer.

## Layout engines

- `elk` — best for hierarchical/layered service graphs. Default here.
- `dagre` — D2's built-in default; try if elk over-spaces a small diagram.
- `tala` — best for architecture but a separate paid Terrastruct binary; not assumed installed. If available, `d2 --layout tala`.

## Layout defaults that avoid the wide-sprawl trap

Learned the hard way: `direction: right` **combined with** nested containers that hold
sibling detail boxes makes ELK sprawl into a 4:1+ ribbon that can't be scanned. Rules:

- **Default `direction: down`** for flow diagrams (client → service → store). Down-flow keeps aspect ratio near 1:1–2:1. Use `direction: right` only when there are ≤4 top-level nodes and little nesting.
- **Prefer flat nodes over deep nesting.** A container with 4+ sibling children forces the layout wide. Instead, collapse the group into one labeled node with its members in the label (`"Active (Rails)\ncontrollers + Reader/Updater/Upserter"`), or push members into a deeper layer.
- **Lead with the message, don't mirror a source's columns.** If the point is a *split* (hybrid path), fork the edges. If the point is *status* (built/todo/blocked), group by status, not by system. A layout that mechanically copies swimlanes usually buries the story.
- **Color edges by protocol** (`style.stroke`) when a diagram mixes REST/GQL/Thrift — the reader traces paths by color, not by reading every label.

## Titles: use markdown, not the bare box

Prefer a markdown title block — it renders as a clean titled header and lets you add a
one-line subtitle. The bare `title: text {near: top-center}` floats a box that wraps badly
on multi-word titles.

```d2
title: |md
  # {Project} — Container View
  One-line subtitle describing scope.
| { near: top-center }
```

## Zoom-in (Low tier) pattern

For a de-black-boxed slice, make a layer that expands two adjacent containers and drops the system boundary:

```d2
layers: {
  auth-flow: {
    title: {Project} — Auth Flow (zoom) {near: top-center}
    gw: API Gateway { shape: rectangle }
    authsvc: {
      verify: TokenVerifier
      refresh: RefreshHandler
    }
    redis: Session Cache { shape: cylinder }
    gw -> authsvc.verify: validate
    authsvc.verify -> redis: lookup
  }
}
```

## Anti-patterns (cause clutter)

- Showing container internals on the Context/Container view — black-box them.
- >9 boxes at one level — split into a deeper layer.
- Unlabeled edges — reader can't tell protocol from data flow.
- Same info repeated across two tiers — each tier must add new information, not restate.
- Missing technology tags — a box named "Service" with no tech is noise.
