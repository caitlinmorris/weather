# we.ather — Member Guide

*You're joining an early beta of an ambient awareness experiment:
a small always-on-top widget showing your room's work as slowly drifting
weather — never message content. Read
[security-model.md](security-model.md) first (one page): it shows the exact
JSON that ever leaves your machine.*

## What you need

- macOS, and you do real work in **Claude Code** and/or **Warp**.
- An **invite from your room's host** — one private message containing
  your room's relay URL and your personal token.
- A way to bill the small AI model that summarizes your work (~pennies
  per workday): your own Anthropic API key, **or** — if you use Claude
  Code on a paid plan — your existing Claude subscription, no key needed.
  You'll pick during install; changeable later in settings.

**Warp users, what's read:** only your typed AI prompts and command exit
codes, from the folders you allowlist — filtered in the database query, so
nothing outside your chosen folders is ever read at all. Warp doesn't store
the assistant's replies locally, so we never see those; your credits/usage
metadata is never read either. One consent point to know: excerpts of your
own prompts are sent to the Anthropic API (under your own key or login) to
produce your state — for a Warp user, that's a party that wouldn't
otherwise see your work narration.

## Install

```
unzip the package you were sent (or clone the repo)
cd we.ather
./install.sh
```

(If macOS complains the script isn't executable after a zip transfer:
`chmod +x install.sh` first.)

The installer walks you through four things, in order:

1. **Your short name** — must exactly match the name your token was
   registered under (the self-test's identity line confirms or corrects
   you).
2. **How extraction is billed** — your own API key, or your Claude
   subscription if you use Claude Code on a paid plan.
3. **Your room** — the relay URL, room name, and your token, all copied
   from the invite you were sent.
4. **Which project folders we.ather may observe** — the important one.
   This list is your consent boundary; nothing outside it is ever read.

It finishes by running a self-test that checks every layer, without
making any paid model calls.

**Your weather starts at install.** Nothing from before you installed is
ever analyzed — the first launch opens an honest, empty field ("still
air"), and your weather appears as you work. Consent starts the clock.

## Checking and changing what's observed

The settings gear (⚙ in the widget) shows your consent list as
checkboxes — tick or untick folders and save; the app relaunches itself
with the change applied. The same is available from the terminal:

```
.venv/bin/python -m presence.pipeline.projects status   # safety check: what's observed
.venv/bin/python -m presence.pipeline.projects          # review newly appeared folders
.venv/bin/python -m presence.pipeline.projects all      # revisit everything, incl. past declines
```

New folders never join silently — the app just prints a one-line notice at
launch and waits for you to review.

## How to run

Once installed, this is the whole action: open Terminal, `cd` into your
we.ather folder, and run

```
./weather
```

The widget window appears, and that's we.ather running — leave it in a
corner of your screen while you work. (`./weather` is a tiny launcher
that always uses the right Python — if you ever see "No module named
..." errors, a bare `python` was used instead.)

**Type it in Terminal — don't double-click `weather` in Finder.** macOS
blocks downloaded unsigned files opened from Finder ("cannot be
verified", with no override offered). Terminal isn't gated the same way,
and the Dock app below is built on your own machine, so Finder launches
it without complaint. If you hit that popup: click Done (not Move to
Trash!) and use Terminal or the Dock app instead.

**Prefer a Dock icon?** One-time setup:

```
.venv/bin/python -m presence.render.make_app
```

That creates **we.ather.app** in your `~/Applications` folder. Open it
once, then right-click its Dock icon → Options → **Keep in Dock** (add
**Open at Login** if you want it always-on). If you ever move the
we.ather folder, rerun that command.

Reading the window: hue = kind of
work, right edge = now, the last 4 hours trail off to the left. The field
itself attributes nothing to anyone. Hovering an outlined block is the
deliberate act — like glancing up from your desk: it shows who it is and
a short phrase of what they're into; the `signal` button controls how
much "what" comes with it. If you're in more than one room, each shows as
its own strip, and a button cycles stacked / single-room / fused views —
your rooms never see each other.

Most settings live behind the gear (⚙) and apply themselves. If you ever
edit `.env` by hand instead, restart the app afterward.

## Updating

During the beta you'll occasionally get a new zip. Your settings and
history live in your install folder (`.env` and `data/`) — keep them:

1. Unzip the new version somewhere temporary.
2. Copy everything from it into your existing we.ather folder,
   replacing what's there — **except** don't touch your `.env` or
   `data/`. (`.env` isn't in the zip, so a straight copy-over is safe;
   just don't delete the folder and start over.)
3. `./install.sh` again (it keeps your existing `.env` untouched and
   refreshes dependencies), then relaunch.

## Stepping away, pausing, quitting

- Closing the window stops everything; you fade to "away" within hours.
- `./weather pause` — immediately purges your state from
  the relay and stops all capture until you `pause resume`. Nobody is
  notified; pausing looks identical to simply not working.
- Quitting entirely: run pause, delete the folder, tell your host to drop
  your token. Everything about you is gone from the relay within minutes;
  nothing about you was ever stored anywhere else.

## Cost & honesty notes

- Extraction runs on your own billing choice: a heavy workday is pennies
  on an API key, or a light draw on your Claude plan's usage limits.
- The extractor will sometimes be wrong or clumsy. A screenshot of a bad or
  over-sharing gist is *wanted data* — send it to whoever invited you;
  don't be polite about it.
- This is an early beta: feel free to reach out to your board host or
  Caitlin with any questions, issues, comments, or ideas. Thanks for
  trying it out!

## Who runs this room

Every board (room) has a **host** — a member of the room who operates its
relay server (free-tier Cloudflare, on their own account). You will always
be told who hosts your room; the host is never someone outside it. Hosts
can see what the relay sees (the low-resolution shared states — never your
raw chats), plus server logs.
