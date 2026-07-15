# we.ather — Pilot Participant Kit

*You're joining a tiny (2–3 person) pilot of an ambient awareness experiment:
a small always-on-top widget showing the group's work as slowly drifting
weather — never message content. Read
[security-model.md](security-model.md) first (one page): it shows the exact
JSON that ever leaves your machine.*

## What you need

- macOS, and you use **Claude Code** for real work.
- ~10 minutes on a call with Caitlin (she brings your API key + relay token).

## Install

```
git clone <repo-url>      # or unzip the folder Caitlin sends
cd <the folder that created>   # its name depends on the repo / zip
./install.sh
```

(If macOS complains the script isn't executable after a zip transfer:
`chmod +x install.sh` first.)

The installer asks four things: your short name (**must exactly match the
name your relay token was registered under** — the self-test's "relay
identity" line confirms or corrects you), the API key, the relay URL +
token, and — the important one — **which project folders we.ather may
observe**. That list is your consent boundary; nothing outside it is ever
read. The self-test checks every layer without making paid API calls.

The app's **first launch builds its own page**: it extracts your existing
history first, which takes a few minutes and costs a dollar or two on the
study key. Later launches are instant.

## Checking and changing what's observed

```
python -m presence.pipeline.projects status   # safety check: what's observed
python -m presence.pipeline.projects          # review newly appeared folders
python -m presence.pipeline.projects all      # revisit everything, incl. past declines
```

New folders never join silently — the app just prints a one-line notice at
launch and waits for you to review. To STOP observing a folder, remove it
from `PRESENCE_ALLOWLIST` in `.env`. After any change, restart the app.

## Daily use

```
.venv/bin/python -m presence.render.app
```

One small window, designed for the corner of your screen. Hue = kind of work,
right edge = now, the last 4 hours trail off to the left. Nothing in the
default view is attributed to a person. Hover an outlined block to see a
short activity phrase; the `signal` button controls how much a hover reveals
— including whether names ever appear. Set it wherever feels right; where
you leave it is part of what the pilot measures.

Settings live in `.env`; if you ever edit it, **restart the app afterward** —
settings are read once at launch.

## Stepping away, pausing, quitting

- Closing the window stops everything; you fade to "away" within hours.
- `python -m presence.pipeline.pause` — immediately purges your state from
  the relay and stops all capture until you `pause resume`. Nobody is
  notified; pausing looks identical to simply not working.
- Quitting the pilot: run pause, delete the folder, tell Caitlin to drop
  your token. Everything about you is gone from the relay within minutes;
  nothing about you was ever stored anywhere else.

## Cost & honesty notes

- API cost runs on the study key (spend-capped); a heavy workday is pennies.
- The extractor will sometimes be wrong or clumsy. A screenshot of a bad or
  over-sharing gist is *wanted data* — send it, don't be polite about it.
- During the pilot you'll get one two-question ping per day ("did you glance?
  did it change anything?"). That's the whole measurement burden.

## Who runs this room

Every board (room) has a **host** — a member of the room who operates its
relay server and pays its few dollars a month. You will always be told who
hosts your room; the host is never someone outside it. Hosts can see what
the relay sees (the low-resolution shared states — never your raw chats),
plus server logs.
