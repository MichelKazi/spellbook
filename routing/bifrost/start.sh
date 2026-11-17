#!/bin/bash
# (Re)start the Bifrost gateway under launchd and wait for it to answer.
plist=$(ls ~/Library/LaunchAgents/com.{spellbook,mkazi}.bifrost.plist 2>/dev/null | head -1)
[ -n "$plist" ] || { echo "no bifrost launch agent; run: spellbook install --with routing" >&2; exit 1; }
launchctl unload "$plist" 2>/dev/null || true
launchctl load -w "$plist"
for _ in $(seq 1 30); do
  curl -sf -m 1 http://127.0.0.1:8080/health -o /dev/null && break
  sleep 1
done
echo "Bifrost: http://127.0.0.1:8080"
