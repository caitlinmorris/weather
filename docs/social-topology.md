# Social Topology — Boards, Invites, and Coexisting Rooms

*Written 2026-07-09, before any second participant is onboarded, because these
decisions set the tool's social physics and are hard to retrofit. Design
principles doc governs; this extends it to the multi-person social layer.*

## 1. The fork: edges or places

Two possible grammars for "who sees whom":

- **Edges (contacts)**: pairwise mutual connections; my board renders the
  union of my edges. The familiar social-app grammar — friend requests,
  personal codes, follower lists.
- **Places (boards)**: a named, closed room; joining the board is the unit of
  consent; everyone in it sees the same weather and the same member list.

**Decision: places.** Two structural arguments, one of tone:

1. **Shared referent.** Social translucence depends on mutual awareness — I
   know that you see what I see; that's where accountability (Erickson &
   Kellogg's third term) comes from. Under the edge model every viewer's
   board is different: there is no "the room," only n private dashboards.
   A café works partly because everyone knows they're in the same café.
2. **Anonymity math.** The field view's unattributed weather protects people
   only if all viewers share the same k. Per-viewer boards over overlapping
   contact sets let mutual friends cross-reference their different
   aggregates and de-anonymize by subtraction. Symmetric boards make the
   k identical for every viewer by construction.
3. **Tone.** "My dashboard of my people" is the surveillance posture wearing
   a friendly UI. "Our room's weather" is not. The grammar itself carries
   the tone, independent of any privacy engineering underneath.

## 2. A new principle: audience loud, activity quiet

Principle 4 (revocation renders as ordinary absence) governs *activity*.
Membership is different: adding person #4 changes what "two people grinding"
reveals about the other three, so **who can see the board must always be
accurate and visible to everyone on it.** No silent additions, no silent
audience growth — ever.

> **Audience changes are always visible; activity changes are always quiet.**

Pausing, lunch, quitting for the day: indistinguishable from not working.
Joining, leaving the board, an open invite: a quiet line in the widget
("maya joined" / "invite open for maya, by caitlin") — visible to all
members, never a knock. Consent integrity requires the first; calm requires
the second; separated this way they don't conflict.

## 3. Invitations

- **Single-use, expiring invite codes, scoped to a board.** Not persistent
  personal codes: those leak, get forwarded, and import the unsolicited-add
  dynamic ("add me: XYZ") of social platforms. An invite is an intentional
  act between people who already know each other.
- **The invitee sees the full member list and the security model before
  accepting.** You always know your audience before your weather enters it.
- **Existing members see the invite exists** (audience-loud rule) before the
  newcomer activates. At friend scale, objection is a conversation, not a
  voting feature; the tool guarantees visibility, not governance.
- **No discovery, ever.** No search, no suggestions, no "people you may
  know." The tool assumes the relationship exists and rebuilds the room
  around it. (Anti-goals list, extended.)

### Identity and naming at redemption

Today's manual bootstrap requires the joiner to retype their person name
exactly as the token was minted — scaffolding, not design. The invite flow
deletes that step rather than forgiving it: the invite carries the identity;
redemption (`POST /join` with the code) registers the joiner's locally
generated token hash under it. Nobody types an identity; mismatch becomes
structurally impossible, and the bearer token never leaves the joiner's
machine.

Who names you — layered, per the audience-loud principle:

- **The inviter proposes the name.** Members must see "invite open for
  maya" *before* she joins; the board consents to a person, and a person
  needs a name at consent time. Pure self-naming at redemption would make
  the audience list accurate but illegible ("who is 'shadowfax'?").
- **The joiner owns the display form.** Stable identity is an opaque id
  bound at redemption; the display name is a self-editable label
  ("daniel" → "dan"), with changes visible to the board like any
  audience-adjacent event. Identity is consented to; spelling is
  self-determined. Renames never break history.

## 4. Board size

The relay doesn't care; the limit is semantic. Two curves cross:

- **Anonymity** improves with size: the weather line's k≥2 suppression is
  thin at N=2–3 and starts genuinely working around 5+.
- **Meaning** decays with size: ambient value requires caring about the
  room's inhabitants — a gist from a stranger is noise, and past the
  sympathy-group scale (~12–15) the room stops being "my people."

Sweet spot: **5–12, a dinner party, not an office floor.** Encode as a soft
cap. The pressure valve beyond it is *more boards*, not bigger ones. (The
field view scales with N far better than the dots strip did — an unplanned
argument for the weather pivot.)

## 5. Coexisting boards (partner / builder friends / colleagues)

The realistic adult social world is several disjoint rooms. Three models for
how one person's view handles that:

- **Workspace switching (the Slack model): rejected.** Ambient displays
  cannot require switching; a peripheral object must be one glanceable
  surface. Channels are foreground attention units — the moment you "check"
  boards one at a time, this is an app, not weather.
- **One widget per board**: honest (each board keeps its own referent), and
  fine at 2 boards, but it's screen clutter that scales linearly and dies
  at 3+.
- **Composite view: one field, several sources — the recommended model.**

The distinction that makes the composite safe, and the sentence this
document exists for:

> **The board is the unit of sharing; the widget is the unit of attention.**

Sharing topology and display layout are different layers. Each board remains
a symmetric room — its members all see that same data, its k is intact, its
audience list is loud. The *composite* exists only in one viewer's eyes:
standing in a doorway between two rooms doesn't create a third mega-room,
and neither room's occupants gain or lose any visibility because of how I
arrange my own windows. The edge-model problems don't return, because:

- no data crosses between boards (compositing is viewer-side rendering);
- each blob's audience is still exactly its board's membership;
- what breaks in the edge model — per-viewer *aggregates over sets only the
  viewer knows* — is avoided by keeping aggregate lines per-board (or
  omitting them in composite view), never computing weather across boards.

Rendering sketch (v2, decide with real use): blend all boards into one
field, with provenance on hover ("via studio board"); or subtle per-board
lanes/regions — weather-map "fronts." Blending is calmer; regions are more
legible. Prototype both, pick by feel.

### Per-board consent tiers — the big consequence

Once boards coexist, the signal dial stops being global: **you share at a
tier per board.** Topic+ with a partner, topic with builder friends,
presence-only with colleagues — same pipeline, different wire payload per
board. This is "resolution is the privacy policy" growing its natural
second axis: resolution *per audience*. Architecturally: board-scoped
tokens, per-board tier filtering at push time (client-side `to_wire(state,
tier)` + server-side per-board whitelist, same both-halves pattern as now).

### Soft guidance: boards are heavy

Boards should feel like studios, not group chats — you inhabit a few, you
don't spawn one per topic. If board management ever needs its own UI screen,
the tone has already been lost. Two or three boards is the imagined normal.

## 6. Open questions (parked deliberately)

1. Overlapping membership: if dan and I share two boards, does he render
   once (deduped) or per-room in my composite? Leaning: dedup to the
   highest-tier instance; revisit with real overlap.
2. Composite weather line: per-board lines stacked, rotating, or none?
3. Does the *relay* multiplex boards (board-scoped tokens on one app) or is
   a board just… its own tiny relay? One-relay-per-board is radically
   simpler operationally (it's ~free) and makes boards structurally
   incapable of leaking into each other. Genuinely tempting; decide when
   board #2 exists.
4. Whether "invite open" should show before or only after the invitee's
   first acceptance step (pre-visibility is stricter; may be socially
   awkward). Try strict first.
