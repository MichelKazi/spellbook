#!/bin/sh
# Bootstrap: find Python 3.11+ (for tomllib), then hand off to bin/spellbook.
#   ./install.sh                         core only (safe on a work machine)
#   ./install.sh --with routing,personal everything on a personal machine
#   ./install.sh --dry-run               show what would change
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

for py in python3.14 python3.13 python3.12 python3.11 python3; do
  if command -v "$py" >/dev/null 2>&1 && "$py" -c 'import sys; sys.exit(sys.version_info < (3, 11))' 2>/dev/null; then
    exec "$py" "$root/bin/spellbook" install "$@"
  fi
done
echo "spellbook needs Python 3.11 or newer (brew install python)" >&2
exit 1
