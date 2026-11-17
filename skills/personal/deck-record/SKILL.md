---
name: deck-record
description: Record a short video (mp4) of the Steam Deck's screen from the Mac over SSH, headless. Use when you need to SEE what the Deck was doing over time (Selene UI animation, a stream playing, a transition) rather than a single still — e.g. verifying HeliOS/Selene behavior during unattended fleet tests. Companion to deck-screencap (still) and deck-input (control). Frame-burst, not smooth video — a few fps.
---

# Deck Record

One command from the Mac to capture a short mp4 of the Steam Deck screen, pull it
back, and inspect it. Built for the same headless KDE-over-SSH setup as deck-shot.

## The one command

```
deck-record --duration 5 --fps 5
```
Prints `/tmp/deck-record.mp4`. You can't Read an mp4 directly — verify it with:
```
ffprobe -v error -show_entries format=duration:stream=width,height,nb_frames \
  -of default=noprint_wrappers=1 /tmp/deck-record.mp4
ffmpeg -y -i /tmp/deck-record.mp4 -vf "select=eq(n\,8)" -vframes 1 /tmp/frame.png
```
then Read `/tmp/frame.png`. Clips are **throwaway** — the same `/tmp` path is
overwritten each run. Don't `--out` into the repo or notes dirs.

Options:
```
deck-record --app 'selene'          # caption|resourceClass regex (default: selene|moonlight)
deck-record --duration 8            # seconds (default 5)
deck-record --fps 10                # target fps + mp4 playback rate (default 5)
deck-record --launch '/home/deck/bin/Selene.AppImage'   # launch on Deck if not running
```

`deck-record` is at `~/.local/bin/deck-record` (on PATH).

## When to use
- Verify Deck UI **motion** over time (animation, transition, stream playback).
- Prove during an unattended fleet test what the Deck screen was actually doing.
- For a single still, use `deck-shot` (deck-screencap skill) — it's faster.

## Footguns (this tool exists because of these)
- **No true video path on this rig.** KWin `ScreenShot2` DBus is authorization-
  gated (only spectacle is allow-listed; our own callers get `NoAuthorized`).
  `spectacle -R screen` (real KWin screencast) dies headless AND wedges the single
  screencast slot — it broke capture fleet-wide once. Do NOT use it. This tool
  records a **frame burst** via the authorized `spectacle` still path instead.
- **fps ceiling ~3-5.** Each frame is a spectacle process spawn (~150-250ms when
  uncontended). Ask for `--fps 20` and you still get a few fps; the mp4 just
  plays at the rate you asked. It's a flipbook, not smooth video. Owner OK'd this.
- **Session type varies.** The Deck boots into gaming mode; a reboot +
  `steamos-session-select plasma` may bring KDE up as **Wayland** (kwin_wayland,
  `wayland-0` socket) OR **X11** (kwin_x11, `DISPLAY=:0`). The tool auto-detects:
  Wayland → activate window + `spectacle -a`; X11 → `spectacle -f` fullscreen
  with `DISPLAY=:0` + `XAUTHORITY=$(ls /run/user/1000/xauth_*)` (the xauth file
  name is dynamic — glob it, don't hardcode).
- **Single capture slot.** Concurrent captures break KWin (`write() Broken
  pipe`). `deck-record` re-execs under `deck-lock` (the shared Deck mutex
  deck-shot/deck-input use) so it auto-serializes. Never hold capture idle.
- **Cleanup.** Deck-side frames + mp4 are per-run temps, deleted after transfer.
  Delete `/tmp/deck-record*.mp4` + extracted frames on the Mac when done.

## How it works
1. Mac wrapper `~/.local/bin/deck-record` re-execs under `deck-lock`, SSHes the
   Deck, runs the deck script, scps the mp4 back, prints the path.
2. Deck script `/home/deck/selene/scripts/deck-record.sh`: detects X11 vs Wayland,
   loops `spectacle` stills into numbered PNGs for `--duration` secs, then
   `ffmpeg -framerate <fps> ... -c:v libx264` muxes them to mp4.

## Verify
```
p=$(deck-record --duration 5) && ffprobe "$p" && \
  ffmpeg -y -i "$p" -vf "select=eq(n\,8)" -vframes 1 /tmp/frame.png
# then Read /tmp/frame.png — confirm it's the real Deck screen, not black.
```
