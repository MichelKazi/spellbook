---
name: load-session
description: "Invoke at the START of a new session to restore context from a previous handoff. Run vault_search for the most recent session handoff note, read it, and brief the user on where things stand before doing anything else. Triggers on: /load-session, 'resume last session', 'what were we doing', 'pick up where we left off'."
triggers:
  - /load-session
  - /resume
---

# Load Session Skill

When invoked:

1. Call memory_search("session handoff", scope="personal") -- get the most recent entry
2. Call vault_search("session-handoff", scope="personal") -- find recent handoff notes
3. Read the most recent handoff note via vault_read
4. Print a crisp briefing:
   - What the last session was doing
   - What's in progress
   - What the next step is
   - Any blockers to be aware of
5. Ask: "Ready to continue with [next step], or do you want to load a different session?"
6. Run any "Context to Load" tool calls from the handoff note

Do not start any work until the user confirms they want to proceed.
