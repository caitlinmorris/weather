# Self-Hosting we.ather — own your own board

*The guide for someone who wants their own we.ather entirely
under their own control — their board, their data paths, etc.. You don't need to share a board
with the person who introduced you to it (e.g. Caitlin).*

## The sovereignty model

A **board** is a room of 2–12 people who see each other's work-weather.
Every board has a **host** — a member of that room who runs its tiny
relay server. The relay sees only low-resolution shared states (never
anyone's chats); everything rich stays on each member's laptop. As a
self-hoster, YOU are the host: your board runs on your free Cloudflare
account, your members' tokens are minted on your machine, and no third
person — including whoever gave you this software — can see your room or
its existence. Operator disclosure still applies *inside* the room: your
members know you host it.

## Whose keys are whose

There are two completely separate credentials:

1. **Relay tokens** (per member, per board): access passes to a board.
   Minted by the host, handed to members privately. Free.
2. **Extraction billing** (per person): the small model calls (Haiku) that turn
   your own AI-session transcripts into your shareable state — they run
   from your own machine, and you choose at install (changeable any time
   in settings) how they're billed:
   - **Your own Anthropic API key** (console.anthropic.com) — works for
     everyone. Typical cost: pennies per workday, a few dollars a month.
   - **Your Claude subscription** — if you use Claude Code on a paid
     plan, extraction can ride your existing Claude Code login: no API
     key at all. It draws (lightly) on your plan's usage limits rather
     than costing extra money.

   Either way, excerpts of your prompts go to Anthropic for extraction;
   if your AI tool isn't Claude, that's a party that wouldn't otherwise
   see your work narration.

## Costs Transparency

| Thing                                        | Cost |
| -------------------------------------------- |---|
| Board relay (Cloudflare Workers free tier)   | $0, no card |
| Your extraction (API-key option)             | ~pennies/workday |
| Your extraction (Claude-subscription option) | $0 extra; uses plan limits |
| The software                                 | free, source included |

For reference: Caitlin (we.ather dev) has been running this for most of a workday at 5x usage ("dev mode" = extracts every 60 seconds; default is 5 minutes) and running a total of about 80 cents on API for heavy coding days.

## Setup (host, ~20 minutes)

1. Get the repo (clone or the zip you were sent). You need: macOS,
   Python 3.12+ (`brew install python@3.13`), node (`brew install node`)
2. Make a free Cloudflare account (no card; wrangler opens a browser login).
3. Install your own client: `./install.sh` (it walks you through how
   extraction is billed — API key, or your Claude subscription if you
   use Claude Code — and, the important moment, WHICH project folders it
   may observe; nothing outside your picks is ever read). When it asks
   for a relay URL, **leave it empty** — your board doesn't exist yet;
   step 4 creates it and step 5 adds its lines to `.env`.
4. Create your board — name it after the ROOM of who you'll share it with, not your name ("family",
   "labmates", "homies"): the name is config plumbing; displays show rooms
   as "with <members>". This also mints member tokens (agree lowercase
   short names with your members first):
   ```
   ./presence/relay/make_board_cf.sh <board-name> <you> [others...]
   ```
   Starting solo is fine — make the board with just yourself, watch your
   own weather for a while, and invite people whenever you're ready
   (settings gear → your room → invite).
5. Put YOUR token + the printed URL in your `.env` (the script shows the
   exact lines); send your colleague theirs privately.
6. `python -m presence.pipeline.selftest` — all green means live.
7. Daily: `python -m presence.render.app`. Or make it Dock-launchable
   (one time): `python -m presence.render.make_app` creates
   **we.ather.app** in `~/Applications` — open it once, then right-click
   its Dock icon → Options → **Keep in Dock** (and **Open at Login** if
   you want it always-on). Rerun that command if you move this folder.

Your colleague does steps 1, 3, and 5–7 with the token you send them —
they never touch Cloudflare (step 2 is yours alone). Read `docs/pilot-kit.md` for the widget
tour and `docs/security-model.md` (one page) for exactly what leaves a
machine and what a relay compromise could and couldn't expose.

## Worked example: Matt's board

Hypothetical friend Matt wants a board with three friends. 

- **Matt (host, ~20 min once):** downloads the package, `./install.sh`
  (his own billing choice + folder consent), then creates the room on
  his own free Cloudflare account:
  `./presence/relay/make_board_cf.sh <board> matt ana ben cara`
  — this mints the four relay tokens and prints each member's exact
  `.env` lines. He sends each friend their token + lines privately.
- **Each member (~10 min):** download → `./install.sh` (their own
  billing choice + folder consent; relay URL from Matt's message) →
  `python -m presence.pipeline.selftest` → all green →
  `python -m presence.render.app`.

Everyone receives exactly one private message: their invite from the
host. If a member later wants a second board, they need a new TOKEN
(from that board's host) but no new billing setup.

## Inviting someone later

Hosts don't recreate anything. In the app: settings gear → your room →
"invite to '<room>'…" — type their short name, and it mints the token,
registers it with your relay, and shows the exact message to send them
privately (shown once, never stored). Same thing from the terminal:
`python -m presence.relay.invite <board> <person>`. Works for both
backends; the invite button appears only under rooms this machine hosts.

## Starting from the app instead of the terminal

If you already run we.ather, the settings gear covers most of this doc:

- **Joining a room someone invited you to:** settings gear → "add a
  room…" → paste the room name, relay URL and token from their invite
  message → save. That's it — no `.env` editing, no terminal.
- **Inviting someone to a room you host:** the invite button under that
  room (previous section).
- **Creating a brand-new room** is the one step that still needs the
  terminal: `./presence/relay/make_board_cf.sh <room> <you> <friend...>`
  (steps 4–5 above). After that one command, everything else — including
  all future invites — happens in the app. GUI room creation is on the
  roadmap (it needs the Cloudflare API instead of wrangler).

## Notes for hosts

- **One deployment = one board.** A second room = run the script again
  with a new name. Boards are deliberately heavy-ish: rooms, not chats.
- **Multiple boards.** You can run multiple boards simultaneously without overlapping participants - for example, one board with your family members, another with your colleagues, separately. When you have multiple boards, you'll see an option in the GUI to stack them vertically or visually fuse them into a single view (for you only — again, the members of different boards won't see each other.)
  In `.env` terms: each board gets its own `RELAY_URL_<NAME>` /
  `RELAY_TOKEN_<NAME>` / `PRESENCE_TIER_<NAME>` lines, and
  `PRESENCE_BOARDS` is the comma-separated roster — joining a second
  board means appending `,<name>` to that one line (or just use
  settings gear → "add a room…", which does it for you).
- **Adding a member later:** use the invite button (settings gear →
  your room) or `python -m presence.relay.invite <board> <person>` —
  either one mints the token, registers it with your relay, and hands
  you the message to send privately. Then tell your room — membership
  changes are always visible, never silent.
- **Leaving/pausing** is every member's own right: `python -m
  presence.pipeline.pause` purges them from your relay within a cycle,
  and pausing is indistinguishable from simply not working.
