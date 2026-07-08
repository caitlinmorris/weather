# Friend Pilot Plan — the first other dot (N=2–3)

*Written 2026-07-06. The lightweight social test, frontloaded: one close
friend on the display before the formal cohort pilot. This document is the
plan to execute when ready — not a build instruction for today. It slots into
docs/next-steps.md as a Stage 6-lite that can run in parallel with Stages 3–5
once the go-gates below are met.*

## What this tests (that self-dogfooding can't)

- The **glance-outcome spectrum** with a real relationship: does knowing a
  friend is "deep in map overlays" produce café-feeling, warmer regard, or an
  actual "tell me more?" message. With N=2 every rung is observable directly.
- **Micro-gist legibility without context**: your gists are self-labeled by
  someone who knows the work. A friend reading "refining figure styling"
  cold is the first honest test of authored-for-audience extraction.
- **Consent UX under trust**: a close friend will tell you when a toggle
  feels wrong in a way pilot strangers won't.

## Transport: the decision is already made — reaffirmed for N=2

The ~150-line relay from capture-overlay-architecture-v1, unchanged and
deliberately not simplified further:

- **FastAPI app, three endpoints**: `POST /state` (client pushes PersonState
  at consented tiers), `GET /group` (returns GroupState), `DELETE
  /state/{person}` (revocation → immediate, indistinguishable "away").
- **Hosting**: Fly.io small instance (or any $5 VPS). TLS terminated by the
  platform. Per-person bearer token; the group is a closed list in config.
- **The relay is a low-value target by construction**: it holds only current
  PersonStates plus a short ring buffer. Raw chat, SessionObservations,
  evidence — none of it ever leaves either laptop. Compromise of the relay
  leaks exactly what the display already shows.
- Rejected again for the record: synced files/Dropbox (revocation semantics
  are terrible — deletion propagates on sync schedules, and file history
  lingers), and P2P/Tailscale (better privacy story, too much setup friction
  to ask of a friend; revisit if the relay ever feels wrong).

## The build list — STATUS 2026-07-08: items 1–3 built and tested

Built with Fable: person-identity config (GROUP_MODE/PERSON_ID + db
migration helper; default still "projects" so nothing changes until the
pilot flips it), the relay (hashed tokens, wire-whitelist tier enforcement,
TTL ring buffer, 8 security tests mapped to docs/security-model.md), the
RelayClient + watch-loop push/pull with group-cache rendering and local
fallback, and Fly deploy scaffolding (fly.toml + Dockerfile — needs only a
Fly account + `fly launch` + token secrets). Verified end-to-end against a
live local relay: two people over the wire, page rendered from the relay's
group view, revocation purging within one fetch.

**Update 2026-07-08:** item 4 built — config is now .env-driven (identity,
group mode, allowlist), `install.sh` (interactive, with allowlist picker as
the consent-layer-(a) step), `pause`/`resume`/`status` consent switch wired
into the watch loop, `migrate_identity` for the projects→person flip,
`selftest` (zero-API-cost end-to-end check), and docs/pilot-kit.md (friend-
facing instructions). Remaining: Fly deploy (Caitlin's account), friend API
key (Console, spend-capped), cold test of install.sh on a fresh macOS user
account, and the go/no-go gates before the actual invite.

0. **CaptureSource interface** (if the friend doesn't use Claude Code): see
   docs/multi-tool-capture.md — verified adapters exist to be written for
   Codex (~0.5–1d), Hermes (~0.5d), Warp (~1–2d). Do together with item 1;
   they touch the same files. Skip if the friend is on Claude Code.
1. **Person-identity refactor — the hidden prerequisite.** Today
   `person_id` = project directory (the pseudo-people demo trick). Multi-person
   mode needs one dot per *human*: a `PERSON_ID` in config; all allowlisted
   projects roll up into that one person. Spec's open question 2
   (multi-thread people) goes live here — v0 answer: most recent active
   project wins the gist; log when that feels wrong. Keep the
   projects-as-people mode behind a flag; it's still the demo/replay mode.
2. **Relay** per the architecture doc. Includes the closed-list auth config
   and a smoke test that revocation renders as away within one poll cycle.
3. **Client push/pull**: watch loop POSTs PersonState after each rollup;
   build_page (and the live widget) render GroupState fetched from the relay,
   falling back to the local cache when offline ("stale group," never blank).
4. **Install script + pause/uninstall**: clone, venv, .env, allowlist picker
   (the friend chooses which project dirs — this IS consent layer (a)),
   relay token, synthetic end-to-end self-test. Target: 15 minutes on a
   video call. `presence pause` = one command, renders as ordinary absence.
5. **Friend's API key**: provision a scoped key from your Console org with a
   hard spend cap (~$5/mo covers heavy use several times over) so the friend
   installs nothing but the repo and a token. They can swap in their own key
   later; don't make key-creation part of onboarding friction.

## Onboarding (the call itself)

- Walk the three consent layers against the actual config file, not
  abstractly: (a) which projects are modeled, (b) whether their state joins
  the display, (c) events — off entirely for this pilot; the watcher doesn't
  exist yet.
- Say the boundary contract out loud: raw chat never leaves your machine;
  what crosses is the typed state at your tier; here is the exact JSON that
  will be sent (show them a real one from the self-test).
- Set expectations for honesty failures: the extractor will sometimes be
  wrong or clumsy; screenshots of bad gists are wanted data, not bug reports
  to be embarrassed about.

## What to measure (lightweight, two people, ~1–2 weeks)

- Daily two-question ping (shared note or DM, 30 seconds): "Did you glance
  today? Did it change anything you did or felt?" — answers map onto the
  glance-outcome spectrum (nothing / thought of you differently / reached out).
- Count the licensed openers: messages either of you sends *because of* the
  display ("saw you're deep in X…"). Even 2–3 in two weeks is a real result.
- Dial positions: where each of you leaves signal level and theme.
- End with a 20-minute debrief: privacy comfort, what they wished it showed,
  what felt like too much, would they keep running it. If the run went long
  enough, end with the unannounced turn-off and see if they mention it.

## Go / no-go gates before inviting anyone

1. **Stage 2 eval numbers exist** and are sane — you know the extractor's
   per-field accuracy before publishing a friend's state.
2. **A full week of self-watching** where every micro-gist passed your own
   "would I share this" bar (Stage 0 notes are the evidence).
3. **Install script tested cold** on a second machine or fresh user account —
   not first debugged live on the friend's laptop.
4. The friend uses a tool with a supported or buildable capture adapter
   (Claude Code today; Codex/Hermes/Warp per docs/multi-tool-capture.md), or
   accepts batch-import staleness honestly rendered. Non-Claude tools add a
   consent sentence: excerpts go to the Anthropic API for extraction.

## Risks specific to N=2

- **A two-person display is intimate**: "quiet" means *your friend* isn't
  working, identifiable by definition. The k≥2 aggregate rules don't protect
  anyone at N=2 — mitigation is informed consent and friendship, and that's
  a finding about minimum viable group size worth writing down.
- **Time-zone / rhythm mismatch** makes staleness decay feel wrong (their
  whole workday happens while yours is dark). Tune half-life with real data.
- **Extraction asymmetry**: if their work is chat-primary or non-code, the
  behavioral channel goes quiet and momentum leans semantic-only — render
  honestly, log the quality difference.
