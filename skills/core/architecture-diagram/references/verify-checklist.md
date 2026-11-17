# Visual verification checklist

After rendering a tier to PNG, **Read the image** and check each item. This catches layout
defects auto-layout can't prevent. Max 2 fix-and-re-render iterations per tier; if still failing,
report the defect rather than looping.

## Layout defects (fix in D2, re-render)

- **Edge crossings** — many lines crossing = wrong grouping. Try `dagre` vs `elk`, or reorder/group nodes into boundaries.
- **Overlapping labels or boxes** — text unreadable. Shorten labels, or the tier has too many nodes (split into a deeper layer).
- **Orphan nodes** — a box with no edges usually means a missing relationship or it belongs on another tier.
- **Overcrowding (>9 boxes)** — the tier is doing too much. Black-box a group into one box and expand it in a child layer.
- **Aspect ratio** — check the rendered pixel dims (`sips -g pixelWidth -g pixelHeight file.png`). Flag anything past ~3:1 either way; past 4:1 is a fail. Fix by switching `direction: right` → `direction: down` and/or collapsing nested sibling boxes into single labeled nodes. This is the most common defect — check it every render, don't eyeball it.
- **Long edge labels colliding** — shorten to protocol only (`gRPC`, not "makes a gRPC call to fetch").

## Content defects (fix the model, not just layout)

- **Missing technology tag** on a container/component.
- **Missing edge label** — every edge states protocol or purpose.
- **Missing/weak title** — each tier must read standalone.
- **Redundancy across tiers** — if the Mid tier restates the High tier instead of adding internals, it adds no value. Each tier must reveal new information.
- **Detail at the wrong tier** — class-level detail on a Container view; black-box it and push down.
- **Invented elements** — every box must trace to real code/config/graph. Do not fabricate services.

## Pass criteria

A tier passes when: readable at a glance, ≤9 primary boxes, every edge labeled, every element typed + teched, title standalone, and it adds information the tier above does not.
