# we.ather — Pilot Participant Kit

*You're joining a tiny (2–3 person) pilot of an ambient awareness experiment:
a small always-on-top widget showing the group's work as slowly drifting
weather — never message content, never a productivity score. Read
[security-model.md](security-model.md) first (one page): it shows the exact
JSON that ever leaves your machine.*

## What you need

- macOS, and you use **Claude Code** for real work.
- ~10 minutes on a call with Caitlin (she brings your API key + relay token).

## Install

```
git clone <repo>          # or unzip the folder Caitlin sends
cd Translucency
./install.sh
```

The installer asks four things: your short name, the API key, the relay
URL + token, and — the important one — **which project folders we.ather may
observe**. That list is your consent boundary; nothing outside it is ever
read. It ends with a self-test that checks every layer without making any
paid API calls.

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
