# Spellbook

One repository that sets up Claude Code, Codex, and opencode the same way on every machine. Clone it, run one command, and every agent gets the same skills, MCP servers, instructions, and hooks.

A new laptop used to cost me an afternoon of copying `SKILL.md` files between three hidden directories. Each agent also had its own idea of where those directories were. Now it costs one command and a coffee.

The rule that matters most: no agent publishes prose that fails [slopbliterator](https://github.com/MichelKazi/slopbliterator). A hook reads every commit message, PR body, issue comment, and markdown file before a [meat machine](https://en.wikipedia.org/wiki/Homo_sapiens) has to.

### What it installs

| Piece | Where it comes from | Where it goes |
|---|---|---|
| First-party skills | `skills/` in this repo | Symlinks in `~/.claude/skills` and `~/.agents/skills` |
| External skills | `Spellfile.toml` | `npx skills add`, linked into all three agents |
| MCP servers | `Spellfile.toml` | `claude mcp`, `codex mcp`, and `opencode.json` |
| Global instructions | `AGENTS.md` | A marked block in `CLAUDE.md` and each `AGENTS.md` |
| Slop gate | `hooks/slop-gate.py` | Claude Code and Codex hooks, plus an opencode plugin |
| Model routing (optional) | `routing/` | `~/.local/bin` and a Bifrost launch agent |

`Spellfile.toml` is the package list. It works like a Brewfile for agent tooling. Each entry names a group, a source, and the old skill it replaces, if any. [docs/SKILLS.md](docs/SKILLS.md) records the fate of every skill from the old setup.

### Install

```bash
git clone https://github.com/MichelKazi/spellbook.git ~/spellbook
cd ~/spellbook
./install.sh --dry-run          # read the plan first
./install.sh                    # core group only
```

On a personal machine, add the optional groups:

```bash
./install.sh --with routing,personal
```

| Group | Contents | Default |
|---|---|---|
| `core` | General engineering skills, slopbliterator, the slop gate, context7, rea | yes |
| `personal` | Steam Deck tools, Karoo extensions, session handoff, Supabase, Railway | no |
| `routing` | The Opus, DeepSeek, and GLM build pipeline, plus Bifrost | no |
| `lsp` | Claude Code language server plugins | no |

A work machine can have its own routing rules and its own MCP servers. Install `core` there and stop. Spellbook adds its block next to your existing instructions and does not replace them.

The installer needs Python 3.11 or newer, Node.js, and `pipx`. Run it again at any time. Each step checks the current state first, so a second run changes only what drifted.

### The slop gate

The gate catches outward text at the moment it leaves the agent:

- `git commit`, including `-m`, `-F`, heredocs, and `git -C <dir> commit`
- `gh pr create`, `gh pr edit`, `gh pr comment`, and `gh pr review`
- `gh issue create`, `gh issue edit`, and `gh issue comment`
- Markdown files that Claude Code writes, except agent instructions and memory

The gate pipes the text to `slop-lint`. It blocks the action above 3 violations per 100 words. A single banned phrase or em dash also blocks it. The agent gets the violations and the suggested replacements, rewrites the text, and tries again.

This is a real example from a test run. The agent tried to commit this message:

```diff
- This commit leverages a robust, seamless approach to delve into the pivotal file.
+ This commit uses a solid, reliable approach to look at the key file.
```

The gate blocked the first version at 38.46 violations per 100 words. The second version scored 0.00. Neither version says what the commit does, so the gate is not a substitute for judgment. It only removes the excuse.

Set `SPELLBOOK_SLOP_GATE=off` in your own shell to turn it off for a session. Set `SPELLBOOK_SLOP_MAX` to change the threshold. Run `tests/slop-gate.sh` to check the gate against 15 sample commands.

### Model routing

The `routing` group splits the work across three models:

1. Opus plans the change and writes a spec with expected behavior and edge cases.
2. DeepSeek V4.1 writes the tests, then the code, and repeats until the tests pass.
3. GLM reviews the diff against the spec and looks for bugs, regressions, and gaps.
4. Opus reads the review, runs the tests itself, and reports.

Start it with the `build` skill in Claude Code. `ai-pipeline` runs the loop, and `ai-agent` runs headless Claude Code against DeepSeek or GLM. Keys stay in `~/.config/llm-keys.env`, outside the repository. `routing/keys.sh` asks for them and never echoes them.

### Make it yours

- Add an external skill: add a `[[skill]]` entry to `Spellfile.toml` and run `./install.sh`.
- Add your own skill: create `skills/core/<name>/SKILL.md`. The symlink makes edits live in every agent.
- Add a global rule: edit `AGENTS.md`. The next install updates all three agents.
- Find new skills: run `npx skills find <topic>`.

### Ownership

Spellbook changes only what it owns:

- Symlinks that point into this repository
- The block between `spellbook:begin` and `spellbook:end` in each instructions file
- Hook entries whose command points into this repository

`bin/spellbook uninstall` removes all three. External skills, MCP servers, and tools stay installed. Remove them with `npx skills remove`, `claude mcp remove`, or `codex mcp remove`.

### Limits

- Codex skips the hook until you approve it. Run `/hooks` in Codex once after the first install.
- The opencode plugin is untested.
- The rea MCP server skips opencode. DeepSeek rejects a regex in one of its tool schemas, and the error fails every request.
- The gate checks commit and PR text and markdown files. It cannot see code comments. The rule in `AGENTS.md` covers those, so that check depends on the model.
- `slop-lint` measures form. It cannot tell you that a sentence is true or useful.

### Credit

The skills come from their authors, listed in `Spellfile.toml`. [obra/superpowers](https://github.com/obra/superpowers) supplies most of the engineering process. [vercel-labs/skills](https://github.com/vercel-labs/skills) does the cross-agent install work. Spellbook is the list, the glue, and the gate.
