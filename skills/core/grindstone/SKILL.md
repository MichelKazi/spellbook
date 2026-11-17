---
name: grindstone
description: Sharpen the entire bug-prevention stack — review agents, write-time self-checks, hooks, plan templates, repo conventions, memory feedback, and lint rules — by feeding them a bug-fixing PR, testing whether existing tooling would detect the bug on pre-fix code, diagnosing the gap, and prescribing fixes at the cheapest effective leverage point. Triggers on "grindstone", "sharpen reviews", "why didn't we catch this", "improve review agents", or when a bug-fix PR reveals a gap in coverage.
---

# Grindstone

Red-team your bug-prevention stack with real bugs, then patch the gaps at the cheapest layer that catches them.

## Philosophy

Bugs slip past multiple layers before shipping. Review agents are the last line of defense: slow and expensive. Earlier layers are cheaper but rely on different mechanisms. Grindstone's job is to identify the cheapest layer that *could* have caught the bug and patch it there. Catch a bug at plan-time and the cost is zero. Catch it at review-time and the cost is a round-trip.

## Leverage Points (cheapest → most thorough)

| # | Layer | Mechanism | When it fires | Best for |
|---|-------|-----------|---------------|----------|
| 1 | **Plan/spec template** (`build` spec, superpowers `writing-plans`) | Questions the plan must answer | Before code is written | Design-stage decisions: data shapes, contracts, naming |
| 2 | **Repo AGENTS.md / CLAUDE.md** | Rules loaded at session start in the repo | Every session in that repo | Project-specific invariants (e.g. "all timestamps are UTC") |
| 3 | **Memory feedback** | Feedback files in auto-memory | Every session for this user | Personal preferences, cross-project habits |
| 4 | **Global AGENTS.md** (Spellbook) | Managed block in every agent's global instructions | Every session, every agent | Rules true for all of this user's code |
| 5 | **Hook** (Spellbook `hooks/`) | PreToolUse/PostToolUse enforcement in Claude Code and Codex, plugin in opencode | On every matching tool call | Enforcing a check the model would skip |
| 6 | **Lint rule** | Tooling failure on commit / CI | Always | Mechanical syntactic patterns provable by AST |
| 7 | **Reviewer prompt** (`ai-pipeline` GLM review, superpowers `requesting-code-review`) | Independent reviewer agent | After implementation | Bugs that need several files to see |
| 8 | **`/code-review`** (Claude Code built-in) | Multi-pass review at a chosen effort | On request | Last line of defense before merge |

The taxonomy is roughly: design → habit → enforce → review. Each later layer is more expensive and runs less often. Always prefer the leftmost layer that catches the bug class without false positives.

## When to Use

- A bug-fix PR lands and you think "we should have caught this in review"
- You want to verify a review skill or write-time check would detect a known bug class
- After improving a skill, to confirm the fix actually works
- A bug pattern has slipped through multiple times — escalate to a stronger layer (hook, lint)

## Input

One of:
- A PR URL that fixes a bug
- A bug description + the affected files/code
- A PR URL + explicit bug class to test for

## Process

### Phase 1: Understand the Bug

1. Fetch the PR diff and description
2. Identify the bug class — categorize what went wrong (see registry below). If the bug doesn't fit an existing class, name a new one and add it.
3. Identify the pre-fix state: what code looked like before the fix
4. **Identify the bug's earliest detectable point**: when in the development lifecycle could this first have been caught?
   - At spec/plan time? (data shape decision, contract definition)
   - At write time? (visible in the diff as the author writes it)
   - At commit time? (mechanically detectable by lint)
   - At review time? (requires reading + understanding several files)

### Phase 2: Reproduce the Blind Spot

5. Check out or read the pre-fix code (`git show <main>:<file>` or the base branch).
6. For each leverage point at or after the bug's earliest detectable point, ask: would the *current* configuration of this layer catch it?

   **Layer-by-layer simulation:**

   - **Plan/spec template**: would the `build` skill's spec template (Expected behavior, Edge cases) or superpowers `writing-plans` / `brainstorming` have surfaced the right questions at design time?
   - **Repo AGENTS.md**: read the repo's AGENTS.md or CLAUDE.md. Does it state an invariant the bug violates?
   - **Memory feedback**: read the agent's memory feedback files. Any rule that would have primed against this?
   - **Global AGENTS.md**: read Spellbook's `AGENTS.md`. Any rule that covers this?
   - **Hooks**: read the installed hooks (`~/.claude/settings.json`, `~/.codex/hooks.json`). Would one fire on the relevant command or file?
   - **Lint**: is there a rule (or could there be) that mechanically catches this? Check the project's linter configs.
   - **Reviewer prompt**: read `review_prompt()` in `ai-pipeline` and superpowers `requesting-code-review`. Would a reviewer following them flag this?
   - **/code-review**: run Claude Code's built-in `/code-review` on the pre-fix diff. Does it flag the bug?

   For each layer, record: would-catch | wouldn't-catch | not-applicable.

7. Optionally, when accuracy matters, launch the simulation as background agents in parallel with prompts like:
   ```
   You are testing whether [layer name] would catch a known bug.
   
   Here is the code as it existed before the fix:
   [pre-fix code]
   
   Here is the context: [migration name, what's being ramped, what consumers exist]
   
   Using ONLY the guidance in [prompt/config file path], analyze this code.
   Do you flag a bug? If yes, what severity? If no, why not?
   ```

### Phase 3: Diagnose the Gap

8. For each layer that *should* have caught the bug but didn't, identify WHY:
   - **Missing heuristic**: the prompt/config doesn't mention this pattern
   - **Wrong scope**: looks for the right thing but in the wrong place
   - **Missing data source**: can't access the info needed (e.g., DB values)
   - **Insufficient cross-referencing**: checks A and B separately but doesn't compare them
   - **Skill exists but wasn't invoked**: trigger description doesn't match this PR type, or hook didn't fire
   - **No layer covers this**: need to create coverage at a new layer

9. Choose the cheapest layer that catches the bug class without false positives. Defaults:
   - Pattern is design-stage → patch the plan/spec template (Layer 1)
   - Pattern is a repo-specific invariant → patch the repo's AGENTS.md (Layer 2)
   - Pattern is universally true for this user → patch memory feedback (Layer 3)
   - Pattern applies to all of this user's code in every agent → patch the global AGENTS.md (Layer 4)
   - Pattern slips because the model forgets to run a check → add a hook (Layer 5)
   - Pattern is mechanically provable → add a lint rule (Layer 6)
   - Pattern requires reading multiple files → patch the reviewer prompt (Layer 7)

   Apply at the cheapest viable layer first. If the pattern slips through multiple times after that, escalate to a stronger layer (e.g. add a hook to enforce the skill, or a lint rule on top of the convention).

### Phase 4: Prescribe and Apply the Fix

    - **Plan/spec template**: add a question or section to the spec template in the `build` skill, or to superpowers `writing-plans`
    - **Repo AGENTS.md**: append a rule to `<repo>/AGENTS.md` (or `CLAUDE.md` if that's what the repo uses). Be explicit and short.
    - **Memory feedback**: write a new file in the agent's memory directory and link it from its index. Follow the agent's memory format.
    - **Global AGENTS.md**: add a rule to Spellbook's `AGENTS.md` and re-run `spellbook install`, so Claude Code, Codex, and opencode all get it
    - **Hook**: add or extend a script in Spellbook's `hooks/` and register it in the manifest, so it installs for every agent
    - **Lint**: add a rule to the project's linter config
    - **Reviewer prompt**: extend `review_prompt()` in `ai-pipeline`, or the review checklist in superpowers `requesting-code-review`

11. Apply the change. Often multiple layers benefit — apply at the cheapest layer first, but if the bug class is high-stakes also patch later layers as a safety net.

### Phase 5: Verify

12. Re-run Phase 2 against the pre-fix code with the updated configuration.
13. Confirm the layer now catches the bug with appropriate severity.
14. Check for false positive risk: would this new guidance flag correct code as buggy? Walk through 2-3 nearby correct examples.
15. If the fix was a hook: smoke-test the hook script with a synthetic event payload and verify it emits the expected `additionalContext`.
16. If the fix was a CLAUDE.md or memory entry: verify it loads (start a fresh session in the relevant directory and check the system prompt).

## Output

After all phases, report:

```
## Grindstone Report

### Bug Class
[name]: [one-line description]

### Earliest Detectable Point
[plan | write | commit | review]

### Layer-by-Layer Coverage Audit
| Layer | Would-catch? | Gap reason |
|-------|--------------|------------|
| 1. Plan/spec template | no | no shape-decision section |
| 2. Repo AGENTS.md | no | invariant not stated |
| 3. Memory feedback | no | not primed |
| 4. Global AGENTS.md | n/a | repo-specific |
| 5. Hook | n/a | nothing to trigger |
| 6. Lint | n/a | not mechanically expressible without AST |
| 7. Reviewer prompt | no | review prompt silent on this |
| 8. /code-review | no | not flagged at this effort |

### Fix Applied
- Layer chosen: [N — name]
- File(s): [path(s)]
- Change: [summary]
- Also patched (safety net): [list, or "none"]

### Verification
- Pre-fix detection: [PASS/FAIL] — layer now flags with [severity/visibility]
- False positive risk: [LOW/MEDIUM/HIGH] — [why]
- Hook smoke test (if applicable): [output]
```

## Bug Class Registry

When a new bug class is identified that isn't in the list below, add it. Over time this becomes a taxonomy of review blind spots.

- **Silent fallback**: catch-all/default masking data errors
- **Hydration gap**: new code path doesn't populate all fields old path did
- **Enum parity**: enum values exist in source but not modeled in consumer
- **Cross-boundary format**: value mapped to symbol/format downstream doesn't support
- **Contract drift**: service response evolved but consumer wasn't updated
- **Missing field consumption**: thrift/proto field exists but consumer never reads it
- **Sibling field type drift**: within a struct, fields representing the same conceptual value (timestamps, durations, IDs, money) use different physical types — especially when introduced in the same diff

## Guidelines

- **Choose the cheapest layer that works.** Plan-time fixes are free. Hook fixes are uncompromisable. Don't reach for a reviewer-prompt patch when an AGENTS.md line would do.
- **Don't over-fit.** The fix should catch the BUG CLASS, not just this specific instance.
- **Test for false positives.** Walk through 2-3 similar-but-correct examples and verify they wouldn't trip the new guidance.
- **Prefer enriching existing prompts over creating new sub-agents.** Skill graph complexity has a cost.
- **Layer in safety nets when stakes are high.** A high-impact bug class can be patched at 3+ layers (e.g. plan template + self-check + hook trigger). Lower-stakes patterns get one layer.
- **Hook-enforced > model-disciplined.** If a check matters and the model keeps skipping it, escalate from "skill exists" to "hook fires the skill."
- **Lint > hook > skill** for mechanical patterns. If a regex can catch it, don't make a model do the work.
- **Record the improvement where the next session will see it.** The repo's AGENTS.md/CLAUDE.md for project-specific lessons; auto-memory feedback files for personal habits.
