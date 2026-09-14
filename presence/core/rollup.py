"""Roll-up: private SessionObservations -> published PersonState.

This is THE boundary crossing. It is the only module in the codebase permitted
to open the public store with writer=True (tests/test_boundary.py enforces).
What it declines to publish is as much the point as what it publishes: any
field whose tier in FIELD_TIERS is below the publish tier stays at its schema
default (unknown/empty) in the published object — momentum and stance never
appear per-person, only (later) in aggregates.

V0.1 draft by Claude (reference implementation, per docs/v0.1-plan.md
decision 2). Rules are deliberately dumb per the spec: recency-weighted mode
for enums, most-recent gist, revise with data.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from presence.core.schema import (
    FIELD_TIERS,
    PersonState,
    Phase,
    PresenceLevel,
    SessionObservation,
    Tier,
)

WINDOW_HOURS = 4  # roll-up window from the spec


def _recency_weighted_mode(values: list):
    """Mode over the window, weighting later values more (weight = 1-based
    position). unknown only wins if nothing else appears at all."""
    scores: dict = {}
    for i, v in enumerate(values):
        scores[v] = scores.get(v, 0) + (i + 1)
    known = {v: s for v, s in scores.items() if getattr(v, "value", v) != "unknown"}
    pool = known or scores
    return max(pool, key=pool.get)


def rollup_window(
    observations: list[SessionObservation],
    publish_tier: Tier = Tier.T2_AMBIENT,
) -> PersonState:
    """Publishable state from a chronological window of observations
    (the caller guarantees ordering; the last one is the newest)."""
    assert observations, "rollup needs at least one observation"
    newest = observations[-1]

    def allowed(field: str) -> bool:
        return FIELD_TIERS[field] >= publish_tier

    state = PersonState(
        person_id=newest.person_id,
        updated_at=newest.t_end,
        presence=PresenceLevel.AWAY,  # derived from staleness at render time
    )
    if allowed("topic_gist"):
        state.topic_gist = newest.topic.gist
    if allowed("topic_micro"):
        state.topic_micro = newest.topic.micro_gist
    if allowed("topic_tags"):
        state.topic_tags = list(newest.topic.tags)
    if allowed("phase"):
        # The color is the in-the-moment state, not an average of the day
        # (Caitlin ruling, 2026-09-14): each published window carries its
        # OWN phase, matching the topic fields above. The 4h-mode
        # smoothing was dots-era; on a building-heavy day it published a
        # writing window as building — flattening exactly the
        # transitions the field is designed to make legible. Day-level
        # texture already has its aggregate home: the weather phrase's
        # "mostly …" suffix.
        # One prior rule survives (from the mode era): unknown never
        # beats a known value — if the newest window ABSTAINED, fall
        # back to the most recent known phase rather than erasing it.
        state.phase = next(
            (o.phase for o in reversed(observations)
             if o.phase != Phase.UNKNOWN),
            Phase.UNKNOWN,
        )
    if allowed("stance"):  # T1: stays UNKNOWN at ambient tier
        state.stance = _recency_weighted_mode([o.stance for o in observations])
    if allowed("momentum"):  # T1: stays UNKNOWN at ambient tier
        state.momentum = _recency_weighted_mode([o.momentum for o in observations])
    return state


def publish_history(private_store, public_store, person_id: str) -> int:
    """Replay a person's whole observation history into a published PersonState
    timeline: one state per observation, each rolled up over the preceding
    4-hour window. Returns the number of states published."""
    all_obs = private_store.window(person_id, since=datetime.min)
    count = 0
    for i, obs in enumerate(all_obs):
        window_start = obs.t_end - timedelta(hours=WINDOW_HOURS)
        window = [o for o in all_obs[: i + 1] if o.t_end >= window_start]
        public_store.publish(rollup_window(window))
        count += 1
    return count


def open_public_writer(path):
    """The sanctioned way to obtain public write access (writer=True lives
    here and nowhere else)."""
    from presence.pipeline.store import PublicStore

    return PublicStore(path, writer=True)
