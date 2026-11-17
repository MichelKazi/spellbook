---
name: deck-input
description: Drive the Steam Deck's mouse, keyboard, and gamepad from the Mac over SSH on the KDE/Wayland desktop session, by injecting events into the Deck's /dev/uinput. Use to act on the Deck for E2E testing — walk menus, click, type, press gamepad buttons — the counterpart to deck-screencap (which lets you SEE the Deck). Injects below the Wayland compositor so it works where xdotool cannot. Pairs with fleet-orchestrate.
---

# Deck Input

One command from the Mac to move the Deck's mouse, press keys, or drive a
virtual gamepad on the Steam Deck's KDE/Wayland desktop session, then confirm
with `deck-shot`. Built for Selene / stream-client E2E (Deck runs Plasma 6 /
KWin 6.4 / Wayland in desktop mode).

## ⚠️ Read this first — injection is DESTRUCTIVE if aimed wrong

Injected events go to **whatever window is focused**, and a virtual gamepad is
seen **globally by SDL**. Sending `key`/`type`/`pad` while **Selene or Moonlight
is running navigates inside it** — this has already **deleted a host pairing**
(a stray `ctrl+a` + `delete` landed on a focused Selene). Rules, non-negotiable:

1. **Never inject while Selene/Moonlight is running or focused.** The tool
   enforces this: injecting subcommands **refuse with exit 4** if `moonlight` is
   running. Quit it first: `deck-input --raw 'pkill -f moonlight'` (or ask the
   owner) before any test.
2. **Test into a scratch window you spawned** (kate/kwrite), not a real app.
3. **Confirm the target is focused via `deck-shot` BEFORE injecting.** Activate
   it with the KWin trick (below), shot it, verify the caption, *then* send.
4. **Gamepad: only with Selene NOT running.** SDL sees the virtual pad globally;
   in Selene it navigates/deletes. Verify pad events with `jstest`/`evtest`
   reading the event node, not by driving a real app.
5. **No blind `ctrl+a` / `delete` / clicks.** Move to a known coordinate (center
   of your scratch window) and type known strings.

## The commands

```
deck-input mouse-move X Y              # absolute pixel on the 1280x800 panel
deck-input mouse-click [left|right|middle]
deck-input mouse-down|mouse-up [button]
deck-input scroll DELTA                # +up / -down wheel clicks
deck-input key NAME [NAME...]          # chord, e.g. `key ctrl a`, `key enter`
deck-input type "text"                 # type a literal string
deck-input pad BUTTON                  # a b x y up down left right
                                       #   start select guide lb rb l3 r3
deck-input pad-down|pad-up BUTTON      # hold / release a gamepad button
deck-input ping                        # daemon health (always allowed)
deck-input stop                        # kill daemon, DROP the virtual devices
```

`deck-input` is at `~/.local/bin/deck-input` (on PATH). Injecting commands
refuse while Selene/Moonlight runs; override with `DECK_INPUT_FORCE=1` only when
you are certain Selene is not focused.

## Safe test recipe (copy this)

```
# 0. guard: bail if Selene is up
ssh -o IdentityFile=~/.ssh/fleet deck@192.168.0.24 'pgrep -f moonlight && echo SELENE-UP'
#    if SELENE-UP -> STOP, ask the owner. Do not test.

# 1. spawn a scratch window and raise it above everything
ssh -o IdentityFile=~/.ssh/fleet deck@192.168.0.24 '
  export XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 \
         DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
  pgrep -x kwrite >/dev/null || (nohup kwrite >/dev/null 2>&1 & disown); sleep 2
  S=$(mktemp /tmp/act.js); cat > "$S" <<EOF
const cs = workspace.windowList ? workspace.windowList() : workspace.clientList();
for (const c of cs) if (/kwrite/i.test(c.resourceClass)) {
  c.minimized=false; c.fullScreen=false; c.keepAbove=true; workspace.activeWindow=c;
}
EOF
  id=$(qdbus org.kde.KWin /Scripting org.kde.kwin.Scripting.loadScript "$S")
  qdbus org.kde.KWin /Scripting/Script$id org.kde.kwin.Script.run
  qdbus org.kde.KWin /Scripting/Script$id org.kde.kwin.Script.stop; rm -f "$S"'

# 2. CONFIRM kwrite is focused before injecting
deck-shot --app kwrite   # Read it — caption must be KWrite, not Selene/Konsole

# 3. inject into the center of the scratch window
deck-input mouse-move 640 400 && deck-input mouse-click
deck-input type "hello from the Mac" && deck-input key enter

# 4. confirm it landed
deck-shot --app kwrite   # Read it
```

Gamepad verification (Selene down), watch events instead of driving an app:
```
ssh ... deck@... 'jstest --event /dev/input/js2'   # or: evtest /dev/input/eventN
# in another shell:  deck-input pad a ; deck-input pad up
# assert BTN_SOUTH / ABS_HAT0Y events appear in jstest output.
```

## How it works
1. Mac wrapper `~/.local/bin/deck-input` SSHes the Deck (`~/.ssh/fleet` key,
   `deck@192.168.0.24`) and runs the deck script with the subcommand.
2. Deck wrapper `/home/deck/selene/scripts/deck-input.sh` sets
   `XDG_RUNTIME_DIR` (SSH shells lack it — decides the daemon socket path),
   runs the Selene/Moonlight **guard**, then calls the Python tool.
3. Deck tool `/home/deck/selene/scripts/deck-input.py` starts (once) a detached
   daemon holding three `/dev/uinput` devices — mouse, keyboard, and an Xbox 360
   pad — behind a unix socket, and forwards each command to it.

**Why uinput (not xdotool):** Wayland blocks X11-style synthetic input. uinput
injects at the kernel evdev layer, *below* the compositor, so KWin/libinput/SDL
see a real device. It also gives a real virtual **gamepad** SDL enumerates —
essential for Selene, which is controller-first.

**Why a persistent daemon:** libinput/SDL enumerate each evdev node once. A
persistent daemon means no per-command re-enumeration delay and, critically, the
gamepad stays present for SDL apps. `stop` drops the devices.

## Permissions / persistence (no setup needed)
- `/dev/uinput` is writable by the `deck` user **out of the box** — SteamOS ships
  a Steam Input udev rule (`TAG+="uaccess"` in
  `/usr/lib/udev/rules.d/70-steam-jupiter-input.rules`) that grants it. No sudo,
  no custom udev rule.
- Because it is **Steam's own rule**, it **survives reboot and SteamOS updates**
  (updates would only wipe a rule *we* added under `/etc/udev/rules.d/` — we
  added none). `python-evdev` is preinstalled on SteamOS.
- If a future SteamOS ever revokes it: `ls -l /dev/uinput` should show
  `user:deck:rw-` in `getfacl`; if not, re-add
  `KERNEL=="uinput", MODE="0660", TAG+="uaccess"` under `/etc/udev/rules.d/` and
  reload — but note that custom rule would NOT survive an OS update.

## Scope / limits
- Desktop (KDE) mode only. **Game mode = Gamescope** — no KWin scripting, and
  window focus works differently; the mouse/kbd recipe won't activate windows
  there. uinput itself still injects, but you can't safely aim it.
- Absolute mouse maps to a fixed **1280x800** panel. Override with
  `DECK_INPUT_W`/`DECK_INPUT_H` env if the resolution changes.
- `type` handles printable ASCII + common punctuation; no Unicode/IME.
- Don't touch the Deck's stream-from-pc wrapper / Moonlight.conf — unrelated.

## Autonomous E2E: `selene-e2e-test`

`~/.local/bin/selene-e2e-test` composes deck-input + deck-shot into a full
Selene <-> HeliOS stream test the fleet runs with no owner at the Deck. It
launches Selene, gamepad-selects the paired host, launches the Desktop stream,
drives inputs, quits, and confirms return to the host list — saving a numbered
proof PNG per step (`/tmp/e2e-NN-*.png`) to Read afterward.

```
selene-e2e-test            # refuses if Selene already up (owner may be using it)
selene-e2e-test --quit     # also close Selene at the end
selene-e2e-test --host 'Michels-MacBook-Pro'
```

Run it **only when the owner confirms the Deck is free** — it launches Selene
and streams for real. The `pgrep -f moonlight` preflight gate refuses otherwise;
`--force` quits an existing session first.

Confirmed flow specifics baked in:
- On launch, gamepad focus is already on the single host tile → `pad a` selects
  it directly, no navigation.
- Host → app grid; Desktop is the focused tile → second `pad a` launches it.
- Quit uses **Ctrl+Alt+Shift+Q** (Moonlight default). Selene's gamepad quit
  combo RB+LB+Select+Start is **currently broken** (task #6) — do not rely on it.
  Fallback: KWin-closes the stream window.
- It doubles as the **T5 display-restore re-test**: it dumps the Mac display
  arrangement (`helios-display-restore --dump`) before the stream and diffs it
  after quit, catching a restore that left physicals collapsed/mirrored. Needs
  the HeliOS build present under `~/projects/helios/helios/build*/`.

## Verify
```
deck-input ping                        # -> OK pong  (daemon alive)
```
Then run the safe test recipe above and Read the before/after `deck-shot`s.
