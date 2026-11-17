---
name: build
description: Plan → spec → delegated implementation → independent review. Opus (you) plans and writes a markdown spec; DeepSeek implements with tests and iterates until they pass; GLM reviews against the spec and hunts bugs. Use for any non-trivial feature, fix, or refactor in a git repo, or when the user says /build.
---

# /build — Opus plans, DeepSeek builds, GLM reviews

You are the planner and final judge. You do not write the implementation yourself.

## 1. Plan (you)

Explore the repo enough to design the change: entry points, existing patterns, test framework and how tests are run. Resolve real ambiguity with the user now; it is the cheapest point to ask.

## 2. Write the spec (you)

Write `specs/<slug>/spec.md` at the repo root. The implementer and reviewer are fresh agents with no access to this conversation, so the spec must stand alone. Use this structure:

```markdown
# <Title>

Test command: `<exact command that runs the relevant tests, from repo root>`

## Goal
One paragraph: what changes for the user/caller and why.

## Plan
Ordered steps, naming the files/functions to touch and the patterns to follow (cite existing code by path).

## Interfaces
Signatures, types, CLI flags, schemas, error types: whatever callers depend on.

## Expected behavior
Numbered, testable statements. "Given X, when Y, then Z."

## Edge cases
Numbered: empty/huge inputs, invalid data, concurrency, failure of dependencies, boundary values, backward compatibility.

## Out of scope
What must not change.
```

The `Test command:` line is required and parsed by the pipeline, so keep it on one line in backticks. It should be fast and scoped to the change, plus whatever existing suite guards against regressions.

## 3. Delegate (pipeline)

From the repo root, run in the background (it can take a while):

```bash
ai-pipeline specs/<slug> 3
```

Each round, DeepSeek writes tests and code until the test command passes. The pipeline then runs the tests itself, and GLM reviews read-only, ending with `VERDICT: PASS|FAIL`. A FAIL feeds the review back to DeepSeek for the next round. Failing tests always force FAIL. Artifacts in `specs/<slug>/`: `impl-notes.md`, `impl-N.log`, `test-N.log`, `review-N.md`, `status`.

Tell the user it's running; don't poll it.

## 4. Judge (you)

When it finishes, read `status`, the last `review-N.md`, and `git diff $(cat specs/<slug>/base)`. Run the test command yourself. Treat the reviewer's verdict as a claim to check, not a ruling:
- PASS: spot-check the diff against the spec's expected behavior and edge cases, especially anything the review didn't mention.
- FAIL after all rounds: decide whether the remaining findings are real. If the spec was wrong or unclear, fix the spec and re-run `ai-pipeline` (it resumes against the same base). Make small final fixes yourself only when another round would cost more.

Report to the user: what was built, test status, open reviewer findings you agree with, and anything you overrode and why. Don't commit unless asked.

## Config

- Backends: `~/bin/ai-agent deepseek|glm`, headless Claude Code in `--bare` mode against each provider's Anthropic-compatible API, keys from `~/.config/llm-keys.env`.
- Implementer model: `DEEPSEEK_MODEL` env (default `deepseek-flash`, which is DeepSeek V4.1). Reviewer: `GLM_MODEL` in llm-keys.env.
