# Self-Hosting we.ather — own your board, route through no one

*The guide for someone (say, Matt) who wants their own we.ather entirely
under their own control — their board, their data paths, their costs, no
dependence on whoever sent them this. You don't need to share a board
with the person who introduced you to it.*

## The sovereignty model, in one paragraph

A **board** is a room of 2–12 people who see each other's work-weather.
Every board has a **host** — a member of that room who runs its tiny
relay server. The relay sees only low-resolution shared states (never
anyone's chats); everything rich stays on each member's laptop. As a
self-hoster, YOU are the host: your board runs on your free Cloudflare
account, your members' tokens are minted on your machine, and no third
person — including whoever gave you this software — can see your room or
its existence. Operator disclosure still applies *inside* the room: your
members know you host it.

## Whose keys are whose (read this — it confuses everyone once)

Two completely separate credentials:

1. **Relay tokens** (per member, per board): access passes to a board.
   Minted by the host, handed to members privately. Free.
2. **An Anthropic API key** (per person): powers the *extraction* — the
   small model calls that turn your own AI-session transcripts into your
   shareable state, on your own machine. Each self-hosted person uses
   THEIR OWN key from console.anthropic.com. Typical cost: pennies per
   workday, a few dollars a month. (In Caitlin's hosted pilots she
   provides capped study keys — that's the pilot exception, not the
   model. Excerpts of your prompts go to Anthropic for extraction; if
   your AI tool isn't Claude, that's a party that wouldn't otherwise see
   your work narration. Consent point, stated plainly.)

## Costs, complete list

| Thing | Cost |
|---|---|
| Board relay (Cloudflare Workers free tier) | $0, no card |
| Your extraction (your Anthropic key) | ~pennies/workday |
| The software | free, source included |

## Setup (host, ~20 minutes)

1. Get the repo (clone or the zip you were sent). You need: macOS,
   Python 3.12+ (`brew install python@3.13`), node (`brew install node`),
   a free Cloudflare account (no card; wrangler opens a browser login).
2. Install your own client: `./install.sh` (it walks you through your
   API key and — the important moment — WHICH project folders it may
   observe; nothing outside your picks is ever read).
3. Create your board (this mints member tokens too — agree on lowercase
   short names with your members first):
   ```
   ./presence/relay/make_board_cf.sh <board-name> <you> <colleague>
   ```
4. Put YOUR token + the printed URL in your `.env` (the script shows the
   exact lines); send your colleague theirs privately.
5. `python -m presence.pipeline.selftest` — all green means live.
6. Daily: `python -m presence.render.app` (or generate the Dock app:
   `python -m presence.render.make_app`).

Your colleague does steps 1–2 and 4–6 with the token you send them —
they never touch Cloudflare. Read `docs/pilot-kit.md` for the widget
tour and `docs/security-model.md` (one page) for exactly what leaves a
machine and what a relay compromise could and couldn't expose.

## Notes for hosts

- **One deployment = one board.** A second room = run the script again
  with a new name. Boards are deliberately heavy-ish: rooms, not chats.
- Adding a member later: mint their token (`python -m
  presence.relay.mktoken <name>`), add the hash to the RELAY_TOKENS
  secret (`npx wrangler secret put RELAY_TOKENS --config
  presence/relay/worker/wrangler.<board>.toml` with the full updated
  JSON), tell your room — membership changes are always visible, never
  silent.
- The Fly.io relay (`make_board.sh`) is the same contract on a paid-tiny
  VM; the two host types are interchangeable and members can't tell the
  difference. `selftest` is the parity check.
- Leaving/pausing is every member's own right: `python -m
  presence.pipeline.pause` purges them from your relay within a cycle,
  and pausing is indistinguishable from simply not working.
