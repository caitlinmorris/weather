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

The installer asks four things: your short name (**must exactly match the
name your token was registered under** — the self-test's identity line
confirms or corrects you), how extraction is billed, the relay URL + token
from your invite, and — the important one — **which project folders
we.ather may observe**. That list is your consent boundary; nothing
outside it is ever read. The self-test checks every layer without making
paid model calls.

The app's **first launch builds its own page**: it extracts your existing
history first, which takes a few minutes and costs a dollar or two (or a
slice of your plan's usage). Later launches are instant.

## Checking and changing what's observed

The settings gear (⚙ in the widget) shows your consent list as
checkboxes — tick or untick folders and save; the app relaunches itself
with the change applied. The same is available from the terminal:

```
python -m presence.pipeline.projects status   # safety check: what's observed
python -m presence.pipeline.projects          # review newly appeared folders
python -m presence.pipeline.projects all      # revisit everything, incl. past declines
```

New folders never join silently — the app just prints a one-line notice at
launch and waits for you to review.

## Daily use

```
.venv/bin/python -m presence.render.app
```

One small window, designed for the corner of your screen. Hue = kind of
work, right edge = now, the last 4 hours trail off to the left. The field
itself attributes nothing to anyone. Hovering an outlined block is the
deliberate act — like glancing up from your desk: it shows who it is and
a short phrase of what they're into; the `signal` button controls how
much "what" comes with it. If you're in more than one room, each shows as
its own strip, and a button cycles stacked / single-room / fused views —
your rooms never see each other.

Most settings live behind the gear (⚙) and apply themselves. If you ever
edit `.env` by hand instead, restart the app afterward.

## Stepping away, pausing, quitting

- Closing the window stops everything; you fade to "away" within hours.
- `python -m presence.pipeline.pause` — immediately purges your state from
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
- This is an early beta: expect an occasional feedback question from your
  host or from Caitlin. That's the whole measurement burden.

## Who runs this room

Every board (room) has a **host** — a member of the room who operates its
relay server (free-tier Cloudflare, on their own account). You will always
be told who hosts your room; the host is never someone outside it. Hosts
can see what the relay sees (the low-resolution shared states — never your
raw chats), plus server logs.
