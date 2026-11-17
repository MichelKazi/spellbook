#!/usr/bin/env bash
# Synthetic hook payloads through the slop gate. Each case prints PASS or BLOCK.
G=(python3 "$(cd "$(dirname "$0")/.." && pwd)/hooks/slop-gate.py"); T=$(mktemp -d "$HOME/spellbook-gate-test.XXXX")
show(){ python3 -c 'import sys,json; d=sys.stdin.read().strip()
if not d: print("  PASS"); sys.exit()
j=json.loads(d); r=j.get("hookSpecificOutput",{}).get("permissionDecisionReason") or j["reason"]; print("  BLOCK:", " | ".join(r.split("\n")[:3])[:260])'; }
run(){ printf '%s' "$1" | "${G[@]}" | show; }
mk(){ python3 -c 'import json,sys; print(json.dumps({"hook_event_name":sys.argv[1],"tool_name":sys.argv[2],"tool_input":json.loads(sys.argv[3]),"cwd":sys.argv[4]}))' "$@"; }
c1=$'git add -A && git commit -m "$(cat <<\'EOF\'\nLeverage a robust, seamless retry layer \xe2\x80\x94 it is important to note this.\nEOF\n)"'
echo "1 heredoc slop:"; run "$(mk PreToolUse Bash "$(jq -nc --arg c "$c1" '{command:$c}')" "$T")"
c2=$'git commit -m "$(cat <<\'EOF\'\nAdd a retry to the upload client\n\nThe client retries a failed upload three times.\nEOF\n)"'
echo "2 heredoc clean:"; run "$(mk PreToolUse Bash "$(jq -nc --arg c "$c2" '{command:$c}')" "$T")"
printf 'This PR delves into a pivotal, comprehensive overhaul.\n' > "$T/body.md"
echo "3 gh body-file:"; run "$(mk PreToolUse Bash '{"command":"gh pr create --title \"Fix upload\" --body-file body.md"}' "$T")"
echo "4 unrelated bash:"; run "$(mk PreToolUse Bash '{"command":"git status && ls"}' "$T")"
echo "5 -am inline clean:"; run "$(mk PreToolUse Bash '{"command":"git commit -am \"Fix typo in parser\""}' "$T")"
echo "5c -am slop:"; run "$(mk PreToolUse Bash '{"command":"git commit -am \"Delve into a pivotal, seamless fix\""}' "$T")"
echo "5b -m= slop:"; run "$(mk PreToolUse Bash '{"command":"cd x; git commit --message=\"Seamlessly leverage robust synergy\""}' "$T")"
printf '# Notes\n\nOur seamless, robust platform empowers teams.\n\n```py\nleverage = robust()\n```\n' > "$T/README.md"
echo "6 md write slop:"; run "$(mk PostToolUse Write "{\"file_path\":\"$T/README.md\"}" "$T")"
printf '# Notes\n\nThe parser reads one line at a time.\n\n```py\nleverage = robust_seamless()\n```\n' > "$T/README.md"
echo "7 md clean w/ code:"; run "$(mk PostToolUse Write "{\"file_path\":\"$T/README.md\"}" "$T")"
cp "$T/body.md" "$T/SKILL.md"; echo "8 SKILL.md skipped:"; run "$(mk PostToolUse Edit "{\"file_path\":\"$T/SKILL.md\"}" "$T")"
echo "9 off switch:"; printf '%s' "$(mk PreToolUse Bash '{"command":"gh pr create --title x --body-file body.md"}' "$T")" | SPELLBOOK_SLOP_GATE=off "${G[@]}" | show
rm -rf "$T"
T=$(mktemp -d "$HOME/spellbook-gate-test.XXXX")
c=$'git -C /some/dir commit -m "We leverage a robust, seamless pivotal fix."'
echo "10 git -C slop:"; run "$(mk PreToolUse Bash "$(jq -nc --arg c "$c" '{command:$c}')" "$T")"
c=$'git commit -F - <<\'EOF\'\nDon\'t leverage robust seamless synergy here.\nEOF'
echo "11 -F - heredoc w/ apostrophe slop:"; run "$(mk PreToolUse Bash "$(jq -nc --arg c "$c" '{command:$c}')" "$T")"
c=$'git commit -F - <<\'EOF\'\nAdd a retry to the upload client\nEOF'
echo "12 -F - heredoc clean:"; run "$(mk PreToolUse Bash "$(jq -nc --arg c "$c" '{command:$c}')" "$T")"
c=$'git commit -m "unbalanced'
echo "13 unparseable:"; run "$(mk PreToolUse Bash "$(jq -nc --arg c "$c" '{command:$c}')" "$T")"
c=$'gh pr create --title "Fix upload" --body "$(cat <<\'EOF\'\nThis PR delves into a pivotal overhaul.\nEOF\n)"'
echo "14 gh body heredoc slop:"; run "$(mk PreToolUse Bash "$(jq -nc --arg c "$c" '{command:$c}')" "$T")"
rm -rf "$T"
