#!/usr/bin/env bash
# Write ~/.config/llm-keys.env interactively. Keys never touch the repo or shell history.
#   routing/keys.sh            prompt for missing keys
#   routing/keys.sh --force    prompt for every key
set -euo pipefail
file="$HOME/.config/llm-keys.env"
force="${1:-}"
mkdir -p "$(dirname "$file")"; touch "$file"; chmod 600 "$file"

current() { sed -nE "s/^export $1=(.*)$/\1/p" "$file" | tail -1; }

set_var() {
  local name="$1" value="$2" tmp
  tmp="$(mktemp)"
  grep -v "^export $name=" "$file" > "$tmp" || true
  printf 'export %s=%s\n' "$name" "$value" >> "$tmp"
  mv "$tmp" "$file"; chmod 600 "$file"
}

ask_secret() {
  local name="$1" prompt="$2" value
  if [[ -n "$(current "$name")" && "$force" != "--force" ]]; then echo "  $name already set"; return; fi
  read -rsp "  $prompt: " value; echo
  [[ -n "$value" ]] && set_var "$name" "$value" || echo "  skipped $name"
}

default() { [[ -n "$(current "$1")" ]] || set_var "$1" "$2"; }

echo "Writing $file"
ask_secret DEEPSEEK_API_KEY "DeepSeek API key (platform.deepseek.com)"
ask_secret GLM_API_KEY "GLM API key (z.ai)"
default DEEPSEEK_BASE_URL https://api.deepseek.com
default GLM_BASE_URL https://api.z.ai/api/anthropic
default GLM_MODEL glm-5.2

grep -q 'llm-keys.env' "$HOME/.zshenv" 2>/dev/null || {
  echo '[ -f ~/.config/llm-keys.env ] && source ~/.config/llm-keys.env' >> "$HOME/.zshenv"
  echo "  added a source line to ~/.zshenv"
}
echo "Done. Open a new shell, or run: source $file"
