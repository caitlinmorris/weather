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

## Provider mode — someone else pays for your extraction

For small circles (~10-15 people), a provider (e.g. Caitlin) can carry
the API costs without touching your data: they mint you a personal,
spend-capped key in THEIR Anthropic Console and bake it into your kit
(`make_kit.sh` builds one per person). Two properties to understand:

- **Billing is theirs; the data path is not.** Your extraction traffic
  goes directly from your machine to Anthropic under your personal key —
  the provider is never a middleman and cannot see your transcripts.
  (A shared key behind a provider-hosted proxy would centralize content,
  not just billing — rejected on principle.)
- The provider can see your usage COSTS per key and can revoke the key;
  that's the whole visibility they get.

Kit recipients' setup collapses to: unzip → `./install.sh` (one
question: which folders may be observed — consent is never pre-baked) →
run. Board hosting is a separate choice: your own Cloudflare account
(sovereign, below), or ask the provider to host your board on theirs
(easy-mode; they then operate your room's relay, disclosed to its
members, seeing only the low-resolution shared states).

## Setup (host, ~20 minutes)

1. Get the repo (clone or the zip you were sent). You need: macOS,
   Python 3.12+ (`brew install python@3.13`), node (`brew install node`),
   a free Cloudflare account (no card; wrangler opens a browser login).
2. Install your own client: `./install.sh` (it walks you through your
   API key and — the important moment — WHICH project folders it may
   observe; nothing outside your picks is ever read). When it asks for
   a relay URL, **leave it empty** — your board doesn't exist yet; step
   3 creates it and step 4 adds its lines to `.env`.
3. Create your board — name it after the ROOM, not a person ("studio",
   "thesis", "homies"): the name is config plumbing; displays show rooms
   as "with <members>". This also mints member tokens (agree lowercase
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

## Worked example: Matt's board (provider keys + sovereign hosting)

Matt wants a board with three friends; Caitlin pays for extraction but
has no part in his room. The credential rule that makes this make sense:
**API keys follow people; relay tokens follow (person, board).**

- **Caitlin (provider, ~20 min once):** creates ONE Console workspace
  ("matt-circle", one spend cap), mints FOUR keys inside it (per-person
  revocation and usage visibility; a leaked kit identifies itself), runs
  `./make_kit.sh <person>` four times (no board argument), sends each
  person their kit privately. That is the entirety of her involvement —
  she cannot see the board, its members, or its existence.
- **Matt (host, ~20 min once):** gets his kit, `./install.sh`, then
  creates the room on his own free Cloudflare account:
  `./presence/relay/make_board_cf.sh <board> matt ana ben cara`
  — this mints the four relay tokens and prints each member's four .env
  lines. He sends each friend their token + lines privately.
- **Each member (~10 min):** unzip kit → `./install.sh` (one question:
  which folders may be observed) → append the four board lines from Matt
  to `.env` → restart → `python -m presence.pipeline.selftest` → all
  green → `python -m presence.render.app`.

Everyone receives exactly two private messages: a kit from the provider,
board lines from the host. If a member later wants a second board, they
need a new TOKEN (from that board's host) but not a new key.

## Inviting someone later

Hosts don't recreate anything. In the app: settings gear → your room →
"invite to '<room>'…" — type their short name, and it mints the token,
registers it with your relay, and shows the exact message to send them
privately (shown once, never stored). Same thing from the terminal:
`python -m presence.relay.invite <board> <person>`. Works for both
backends; the invite button appears only under rooms this machine hosts.

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
