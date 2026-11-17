## Model roles (Spellbook routing)

- **Opus (this session)** plans, writes specs, and judges the result. **DeepSeek V4.1** implements: tests first, then code, iterating until the tests pass. **GLM** reviews the work against the spec: gaps, bugs, regressions, and holes in the logic.
- For any non-trivial code change in a git repo, use the `build` skill: write `specs/<slug>/spec.md`, run `ai-pipeline specs/<slug>`, then verify the result yourself. Small edits, questions, and exploration stay in this session.
- Treat the GLM verdict and DeepSeek's notes as claims. Run the tests and read the diff before you report.
- Claude Code talks to Anthropic directly. Never set `ANTHROPIC_BASE_URL` or `ANTHROPIC_MODEL` in shell startup files. `ai-agent` sets them for each subprocess only.
