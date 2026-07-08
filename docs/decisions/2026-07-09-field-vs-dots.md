# Decision memo — field rendering vs. dots (surveillance grammar)

**Trigger:** After ~1 day of living with the sticky widget, the per-person
dot + brightness reads as the Slack/Teams presence idiom — identity ×
current-status — which is culturally legible as "is this person working
right now." The form itself carries surveillance connotation regardless of
the data minimization beneath it.

**Decision:** Add a "field" view: an unattributed, pixelated weather field.
Right edge = now, cells drift left (24h window), hue = phase, vertical lane
seeded by topic (recurring work recurs at the same height), sparse seeded
noise for texture, older columns fading out. Fresh events (topic change /
return after gap) crystallize as larger outlined blocks — the only hover
targets — and dissolve into ordinary weather within ~2h. Hover reveals
micro-gist per the signal dial; a person's NAME appears only at topic+.

**Structural meaning:** This moves the ambient layer from T2 (per-person
ambient) to T1 (aggregate) and makes "is X working right now" unanswerable
by glance — position encodes when, not who. Trades the coordination reading
and person-warmth for café-grade room-tone; the licensed opener survives
via event-block hover.

**Instrumentation, not adjudication:** Shipped as a persisted view toggle
next to the signal dial, not a fork. Which view people settle in (and at
which dial level) is pilot data. Deprivation-test question sharpens to:
which *view* do people miss?

**Known limits:** At N=2 anonymity is inference-thin ("colors that aren't
mine are yours"). Field view reduces passive attribution only.
