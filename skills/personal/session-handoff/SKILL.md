---
name: session-handoff
description: "Invoke at the end of any session or before switching tools (Claude Code ↔ OpenCode). Compacts the current session context into a structured handoff doc, writes it to the vault, and stores a memory so any new session can resume instantly with full context. Triggers on: /session-handoff, 'compact this session', 'save session', 'switching to opencode', 'switching to claude'."
triggers:
  - /session-handoff
  - /handoff
  - /compact
---

# Session Handoff Skill

When invoked, perform all of the following steps in order without asking for confirmation.

## Step 1: Compile session summary

Produce a structured summary of the current session with these exact sections:

### 🎯 Session Goal
One sentence: what we were trying to accomplish.

### 🌿 Git + Gate State
Branch, and per repo touched: what's committed (with hash), what's pushed, what's still dirty and why. The test/build baseline as of now — pass/fail counts read from the gate's real output, names of any failures — so the next session diffs against a real number, not a memory. This anchors everything below; a handoff without it can't be trusted (see global CLAUDE.md Operating Instructions).

### ✅ Completed
Bullet list of everything finished, with file paths where relevant. Anchor open work with file:line so a cold session jumps straight to it.

### 🔄 In Progress
Bullet list of work started but not finished, with exact state (e.g. "wrote Phase 1, Phase 2 not started").

### 🧠 Key Decisions
Bullet list of any architectural, tooling, or design decisions made with brief rationale.

### ⚠️ Blockers / Gotchas
Anything that caused friction, failed, or needs attention next session.

### 📁 Files Touched
List every file created, modified, or deleted this session with its path.

### ▶️ Next Steps
Exact next actions in priority order -- specific enough that a cold session can resume without re-reading anything.

### 🔌 Context to Load
List any vault notes, memory queries, or brain_get_context calls the next session should run on startup to get up to speed. Format as ready-to-run tool calls.

---

## Step 2: Write to vault

Call vault_write with:
- path: personal/sessions/YYYY-MM-DD-HH-MM-{slug}.md
  (slug = 2-3 word kebab-case summary of the session goal)
- frontmatter:
  title: Session Handoff -- {slug}
  date: {today}
  tags: [session-handoff, {tool: claude-code or opencode}, {project tag if identifiable}]
  note_type: session
  scope: personal
- content: the full summary from Step 1

---

## Step 3: Write to memory

Call memory_write with:
- content: "Session handoff {date}: {one-line goal}. Status: {in-progress items}. Resume from: personal/sessions/{filename}.md. Next: {top next step}."
- type: decision
- level: 3
- scope: personal
- project: whatever project this session was working on

---

## Step 4: Print a resume prompt

Print this exact block at the end so the user can paste it into any new Claude Code or OpenCode session to instantly resume:

---
/load-session

Resume from vault note: personal/sessions/{filename}.md

Run on startup:
- vault_read("personal/sessions/{filename}.md")
- memory_search("session handoff {project}", scope="personal")
- brain_get_context("{project}")

Context to restore: {paste the Context to Load section here}
---
