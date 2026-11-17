#!/bin/bash
# Stop the Bifrost gateway.
for plist in ~/Library/LaunchAgents/com.{spellbook,mkazi}.bifrost.plist; do
  [ -f "$plist" ] && launchctl unload "$plist" 2>/dev/null
done
echo "Bifrost stopped"
