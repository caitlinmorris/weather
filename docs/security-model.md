# Security Model — What Leaves Your Machine

*Read this before installing if you'd like to understand the details of
what gets shared and how security is implemented. If the code and this
doc ever disagree, that's a bug — tell Caitlin
([caitlinmorris.net](https://caitlinmorris.net)).*

## The one object that crosses the boundary

Everything the system shares about you is contained in this JSON object,
pushed from your laptop to the relay every few minutes while you work:

```json
{
  "person_id": "dan",
  "updated_at": "2026-07-08T14:20:00Z",
  "topic_gist": "",
  "topic_micro": "debugging auth tests",
  "topic_tags": ["auth", "testing", "time-mocking"],
  "phase": "debugging",
  "staleness_hours": 0.1,
  "last_active": "2026-07-08T14:20:00Z"
}
```

(`last_active` is a presence heartbeat derived from transcript file
*timestamps* only — when your tool last wrote anything, never what.)

What the topic fields carry depends on that room's **tier**, chosen
per board and visible to all its members:

- **presence** — no "what" at all: topic fields empty, phase withheld.
- **topic** (default) — the ≤5-word micro-phrase and tags, as above.
- **verbose** (opt-in rooms only) — `topic_gist` additionally carries a
  fuller ≤15-word description of the work.

That's the complete list. There is no message content, no file names, no
code, no error text, no momentum/stuckness field (that tier is not currently
shared at all), no evidence or reasoning. The relay **rejects** any payload
containing fields beyond these — enforcement is server-side, not client
courtesy.

## What stays on your laptop

- Raw AI-session transcripts (created by your coding tool, not by us).
- SessionObservations — the richer extracted states, including the
  extractor's reasoning. These live in a local SQLite file and have no
  network path; the code that could publish them is a single audited module,
  and a test suite fails if any other code acquires write access.

## What the relay stores (and what a full compromise yields)

Current state plus a short ring buffer (max ~40 entries, pruned after 7
days) of the JSON above, per person, in memory. No accounts, no emails, no
long-term archive. An attacker with complete control of the relay learns
exactly what the widget already shows the group, for the trailing week.
Access tokens are stored only as SHA-256 hashes, so relay compromise does
not yield usable credentials.

## Transport and auth

TLS for every request. Per-person bearer tokens (32 random bytes), generated
locally, shared out-of-band. Your token can write and delete only your own
state. The group is a closed list baked into the relay's secrets; there is
no signup surface.

## The extraction path (the one real data flow off-device)

To produce the state object, transcript excerpts are sent over TLS to
Anthropic — under your own API key, or via your own Claude Code login if
you chose subscription billing; either way, directly from your machine,
with no one in between. If you use Claude Code, this adds no new reader —
the same party already processes your sessions. If you use another tool
(Codex, Hermes, Warp), this is a party that wouldn't otherwise see your
work narration: opting in means accepting that. API-tier data is not used
for model training under Anthropic's commercial terms.

## Revocation

`presence pause` (or deleting your state via the relay) takes effect within
one poll cycle (~minutes): your relay state is purged, ring buffer included,
and you render as ordinary "away" — indistinguishable from simply not
working. Nobody is notified. Local capture stops until you resume.

## What this design does NOT protect against — read before opting in

1. **The extractor being too honest.** The most realistic failure is a
   generated gist that says more than you'd want — the model is instructed
   and evaluated on discretion, and every field is length-capped, but this
   is a model-behavior risk, not a solved problem. Screenshots of bad gists
   are wanted data and grounds for tightening.
2. **Small-group inference.** In a group of two or three, "quiet" identifies
   who isn't working, and presence rhythms reveal when you work. No
   cryptography fixes this; it's mitigated only by consent, the visible
   signal-level dial, and bounded retention.
3. **Your own machine.** The pipeline runs with your user privileges and
   reads only the project directories you explicitly allowlist — but anyone
   who controls your laptop already controls your transcripts, with or
   without this system.
