#!/usr/bin/env python3
"""Slop gate: lint outward prose with slop-lint before it leaves the machine.

One script, three agents. Reads a hook payload (Claude Code / Codex shape) on stdin.

  PreToolUse  Bash              git commit / gh pr|issue create|edit|comment|review:
                                lint the message or body, deny the call if it fails.
  PostToolUse Write|Edit|...    markdown file written: lint the file, block with the
                                findings so the agent rewrites it.

Env:
  SPELLBOOK_SLOP_GATE=off       disable (set in your shell, not in the agent's command)
  SPELLBOOK_SLOP_MAX=3.0        max violations per 100 words
"""
import json
import os
import re
import shlex
import shutil
import subprocess
import sys

MAX_PER_100W = float(os.environ.get("SPELLBOOK_SLOP_MAX", "3.0"))
MD_SUFFIXES = (".md", ".mdx", ".markdown")
# Agent instructions, memory, and scratch files are not outward prose.
SKIP_NAMES = {"SKILL.md", "AGENTS.md", "CLAUDE.md", "GEMINI.md", "MEMORY.md"}
SKIP_DIRS = ("/.claude/", "/.codex/", "/.agents/", "/.config/", "/node_modules/",
             "/.git/", "/tmp/", "/private/tmp/", "/private/var/", "/memory/")

GIT_GLOBAL_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env", "--exec-path"}
STDIN_HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n(.*?)\n\1(?:\n|$)", re.S)
GATED_HINT = re.compile(r"\bgit\b.*\bcommit\b|\bgh\s+(pr|issue)\s+(create|edit|comment|review)\b", re.S)
HEREDOC = re.compile(r"^\$\(cat <<-?\s*['\"]?(\w+)['\"]?\n(.*)\n\1\n?\s*\)$", re.S)

# command -> {flag: kind}; kind is "text" (inline) or "file" (path to read)
GIT_COMMIT = {"-m": "text", "--message": "text", "-F": "file", "--file": "file"}
GH_TEXT = {"--title": "text", "-t": "text", "--body": "text", "-b": "text",
           "--body-file": "file", "-F": "file"}
GH_GATED = {("pr", "create"), ("pr", "edit"), ("pr", "comment"), ("pr", "review"),
            ("issue", "create"), ("issue", "edit"), ("issue", "comment")}


def unwrap(value: str) -> str:
    """Strip a $(cat <<'EOF' ... EOF) wrapper, the usual agent idiom for multi-line text."""
    m = HEREDOC.match(value.strip())
    return m.group(2) if m else value


def segments(command: str):
    """Split a shell command line into simple-command token lists."""
    lex = shlex.shlex(command, posix=True, punctuation_chars=";&|")
    lex.whitespace_split = True
    seg = []
    try:
        for tok in lex:
            if tok and set(tok) <= set(";&|"):
                if seg:
                    yield seg
                seg = []
            else:
                seg.append(tok)
    except ValueError:  # unbalanced quotes: let the shell report it
        return
    if seg:
        yield seg


def git_subcommand(seg):
    """Index of git's subcommand, skipping global options like -C <dir> and -c k=v."""
    i = 1
    while i < len(seg) and seg[i].startswith("-"):
        i += 2 if seg[i] in GIT_GLOBAL_WITH_VALUE else 1
    return i


def collect(tokens, flags, cwd, stdin_text=""):
    """Pull inline text and referenced files for the given flags out of argv tokens."""
    parts = []
    i = 0
    while i < len(tokens):
        tok, value, kind = tokens[i], None, None
        # combined short flags ending in m/F, e.g. git commit -am "msg"
        if re.fullmatch(r"-[a-zA-Z]+[mF]", tok) and tok[-1] in "mF" and len(tok) > 2 \
                and "-" + tok[-1] in flags and i + 1 < len(tokens):
            tok = "-" + tok[-1]
        for flag, k in flags.items():
            if tok == flag and i + 1 < len(tokens):
                value, kind = tokens[i + 1], k
                i += 1
                break
            if flag.startswith("--") and tok.startswith(flag + "="):
                value, kind = tok[len(flag) + 1:], k
                break
            if flag in ("-m", "-F") and tok.startswith(flag) and len(tok) > 2:
                value, kind = tok[2:], k
                break
        i += 1
        if value is None:
            continue
        if kind == "text":
            parts.append(unwrap(value))
        elif value == "-":
            parts.append(stdin_text)  # -F - / --body-file - fed by a heredoc
        else:
            path = value if os.path.isabs(value) else os.path.join(cwd, value)
            try:
                with open(os.path.expanduser(path)) as fh:
                    parts.append(fh.read())
            except OSError:
                pass
    return "\n\n".join(p for p in parts if p.strip())


def outward_text(command: str, cwd: str):
    """Return (label, text) for gated commands in a shell command line, else None."""
    # Lift stdin heredoc bodies out before tokenizing; an apostrophe in one breaks shlex.
    # Heredocs inside $(cat ...) stay put: they are part of a quoted -m/--body value.
    bodies = []

    def lift(m):
        if command[:m.start()].rstrip().endswith("$(cat"):
            return m.group(0)
        bodies.append(m.group(2))
        return "<<HEREDOC\n"
    command = STDIN_HEREDOC.sub(lift, command)
    stdin_text = "\n\n".join(bodies)
    segs = list(segments(command))
    if not segs and GATED_HINT.search(command):
        return "unparsed", None
    for seg in segs:
        while seg and (seg[0] == "rtk" or "=" in seg[0] and not seg[0].startswith("-")):
            seg = seg[1:]  # drop wrappers and VAR=value prefixes
        if seg and seg[0] == "git":
            sub = git_subcommand(seg)
            if sub < len(seg) and seg[sub] == "commit":
                text = collect(seg[sub:], GIT_COMMIT, cwd, stdin_text)
                if text:
                    return "commit message", text
        if len(seg) >= 3 and seg[0] == "gh" and (seg[1], seg[2]) in GH_GATED:
            text = collect(seg, GH_TEXT, cwd, stdin_text)
            if text:
                return f"gh {seg[1]} {seg[2]} text", text
    return None


def strip_code(text: str) -> str:
    """Remove fenced and inline code so identifiers don't count as prose."""
    text = re.sub(r"^(```|~~~).*?^\1", "", text, flags=re.S | re.M)
    return re.sub(r"`[^`\n]+`", "CODE", text)


def lint(text: str):
    """Run slop-lint; return a findings string, or None when the text passes."""
    exe = shutil.which("slop-lint")
    if not exe:
        return None  # not installed: fail open, the install step reports it
    out = subprocess.run([exe], input=strip_code(text), capture_output=True, text=True, timeout=20)
    try:
        r = json.loads(out.stdout)
    except json.JSONDecodeError:
        return None
    banned = r.get("sample_banned", [])
    dashes = r.get("em_dash(slop-marker)", 0)
    score = r.get("total_per100w", 0.0)
    if score <= MAX_PER_100W and not banned and not dashes:
        return None
    hits = [f"{k}={v}" for k, v in r.get("violations", {}).items() if v]
    lines = [f"score {score} violations/100 words (max {MAX_PER_100W})"]
    if hits:
        lines.append("violations: " + ", ".join(hits))
    if dashes:
        lines.append(f"em dashes: {dashes} (use a comma, period, or colon)")
    if r.get("sample_marketing"):
        lines.append("marketing words: " + ", ".join(r["sample_marketing"]))
    lines += [f"  {s}" for s in r.get("suggestions", [])]
    return "\n".join(lines)


def main():
    if os.environ.get("SPELLBOOK_SLOP_GATE", "").lower() in ("off", "0", "false"):
        return
    payload = json.load(sys.stdin)
    event = payload.get("hook_event_name", "")
    tool = payload.get("tool_name", "")
    args = payload.get("tool_input") or {}
    cwd = payload.get("cwd") or os.getcwd()

    if event == "PreToolUse" and tool in ("Bash", "bash", "shell"):
        found = outward_text(args.get("command", ""), cwd)
        if not found:
            return
        label, text = found
        if text is None:
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason":
                    "slop gate: could not parse this command to lint its message. Write the "
                    "message to a file, lint it with slop-lint, and pass it with -F <file> "
                    "(git) or --body-file <file> (gh).",
            }}))
            return
        findings = lint(text)
        if findings:
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason":
                    f"slop gate: the {label} failed slop-lint. Rewrite it with the "
                    f"slopbliterator rules and run the command again.\n{findings}",
            }}))
        return

    if event == "PostToolUse":
        path = args.get("file_path") or args.get("filePath") or ""
        name = os.path.basename(path)
        if not path.endswith(MD_SUFFIXES) or name in SKIP_NAMES:
            return
        real = os.path.realpath(path)
        if any(d in real + "/" for d in SKIP_DIRS) or real.startswith(os.path.realpath(os.path.expanduser("~")) + "/."):
            return
        try:
            with open(real) as fh:
                text = fh.read()
        except OSError:
            return
        findings = lint(text)
        if findings:
            print(json.dumps({"decision": "block", "reason":
                f"slop gate: {path} failed slop-lint. Rewrite the prose with the "
                f"slopbliterator rules (code blocks are ignored).\n{findings}"}))


if __name__ == "__main__":
    main()
