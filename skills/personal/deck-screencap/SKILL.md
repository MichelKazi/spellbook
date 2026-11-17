---
name: deck-screencap
description: Screenshot a specific running app's window (e.g. Selene / Moonlight) on the Steam Deck's KDE/Wayland desktop session, from the Mac over SSH, and pull the PNG back to Read. Use whenever you need to see Selene UI on the Deck — it forces the target window active via KWin scripting and grabs ONLY that window (no Konsole/desktop clutter). Pairs with fleet-orchestrate.
---

# Deck Screencap

One command from the Mac to get a clean PNG of a running app's window on the
Steam Deck, then Read it. Built for Selene UI dev (Deck runs Plasma 6 / KWin
6.4 / Wayland in desktop mode).

## The one command

```
deck-shot                              # shot the Selene/Moonlight window
```
Prints `/tmp/deck-shot.png`. Read that path. Shots are **throwaway** — the same
`/tmp` path is overwritten every run, so nothing accumulates. Don't `--out` into
the repo or notes dirs. If you must keep one shot (e.g. a fleet-done proof),
copy it out yourself; otherwise leave it in `/tmp`.

Options:
```
deck-shot --app 'konsole'              # any caption|resourceClass regex
deck-shot --out /tmp/foo.png           # explicit Mac output (keep it /tmp)
deck-shot --launch '/home/deck/bin/Selene.AppImage'   # launch on Deck if not running
```

`deck-shot` is at `~/.local/bin/deck-shot` (on PATH). If PATH misses it, use the
full path.

## Why this exists (footguns it solves)
- `spectacle -a` grabs the **active** window — usually Konsole, not Selene. This
  tool forces the target active FIRST via KWin scripting, then grabs `-a`.
- `spectacle -f` grabs the whole desktop incl. Konsole/Steam clutter. Avoid.
- The KWin `/ScriptN` D-Bus index increments on every `loadScript` and was
  hand-guessed each time. **Fixed:** `loadScript` returns an int id, so the
  script object is `/Scripting/Script<id>` — the deck script captures the return
  value, no guessing.
- SSH sessions have no Wayland env. The deck script exports
  `XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0` +
  `DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus` so qdbus/spectacle
  reach the compositor.

## How it works
1. Mac wrapper `~/.local/bin/deck-shot` SSHes the Deck (`~/.ssh/fleet` key,
   `deck@192.168.0.24`), runs the deck script, scps the PNG back, prints the path.
2. Deck script `/home/deck/selene/scripts/deck-shot.sh`:
   - matches caption/resourceClass regex (default `selene|moonlight`),
   - loads a KWin script that sets `workspace.activeWindow = c` + unminimizes,
   - captures with `spectacle -b -n -a -o <path>` (background, no notify, active only),
   - prints the Deck-side PNG path.

## Scope / limits
- Desktop (KDE) mode only. **Game mode = Gamescope**, no KWin scripting — this
  tool won't work there; Selene UI dev runs in desktop mode so that's fine.
- Matches the FIRST window hitting the regex. Narrow `--app` if multiple match.
- Don't touch the Deck's stream-from-pc wrapper / Moonlight.conf — unrelated.

## Verify
```
p=$(deck-shot) && echo "$p"   # then Read "$p"
```
Confirm the shot is just the app window (title bar caption = the app), not the
desktop or Konsole.
