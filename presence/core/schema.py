"""Typed state layer, from docs/person-model-spec-v0.md.

V0.1 draft by Claude (reference implementation, per docs/v0.1-plan.md decision 2);
to be rewritten by hand after the demo ships.

Two tiers of object: SessionObservation is private and rich; PersonState is the
only thing that crosses the personal boundary, filtered per-field by visibility
tier. GroupState is what renderers consume.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum, IntEnum
from uuid import uuid4

from pydantic import BaseModel, Field

# --- enums ------------------------------------------------------------------
# Every enum includes UNKNOWN, and the extractor is rewarded for using it:
# an awareness system that hallucinates states is worse than one that abstains.


class Source(str, Enum):
    CLAUDE_CHAT = "claude_chat"
    CLAUDE_CODE = "claude_code"
    WARP = "warp"
    OTHER = "other"


class Phase(str, Enum):
    EXPLORING = "exploring"
    SHAPING = "shaping"
    BUILDING = "building"
    DEBUGGING = "debugging"
    POLISHING = "polishing"
    # "writing", not "writing up": prose can BE the work (essays, papers,
    # docs), not only documentation of it. Includes documenting.
    WRITING = "writing"
    UNKNOWN = "unknown"


class Momentum(str, Enum):
    FLOWING = "flowing"
    STEADY = "steady"
    GRINDING = "grinding"
    STUCK = "stuck"
    UNKNOWN = "unknown"


class Stance(str, Enum):
    """v1.0 axis: the person's relationship to the AI in this window.
    (v0's human-expertise axis was degenerate — κ=0.00; see
    person-model-spec-v1.md.)"""

    LEARNING = "learning"
    COLLABORATING = "collaborating"
    DIRECTING = "directing"
    UNKNOWN = "unknown"


# Openness was KILLED in v1.0: construct-invalid (the labeler couldn't
# answer her own question), anti-calibrated, no colleague-facing consumer.


class PresenceLevel(str, Enum):
    ACTIVE = "active"
    RECENTLY_ACTIVE = "recently_active"
    # AWAY is deliberately identical for opted-out, revoked, and actually-away.
    AWAY = "away"


class Tier(IntEnum):
    """Visibility tiers. Lower = more private. See person-model-spec-v0 §tiers."""

    T0_PRIVATE = 0
    T1_AGGREGATE_ONLY = 1
    T2_AMBIENT = 2
    T3_EVENT_ELIGIBLE = 3


# --- private tier: SessionObservation ----------------------------------------


class Topic(BaseModel):
    tags: list[str] = Field(default_factory=list, max_length=7)
    # The gist is WRITTEN TO BE SHARED: the extractor authors it as the person's
    # own colleague-appropriate status line, never as a chat summary.
    gist: str = ""
    # The micro_gist is the rung below: a 2-5 word activity handle
    # ("visualizing map overlays") for roster/statusline rendering — conveys
    # "what" without the gist's level of detail.
    micro_gist: str = ""
    domain: str = ""


class SessionObservation(BaseModel):
    """Extracted per session segment. Never leaves the personal boundary."""

    observation_id: str = Field(default_factory=lambda: str(uuid4()))
    person_id: str
    t_start: datetime
    t_end: datetime
    source: Source = Source.CLAUDE_CODE
    extractor_version: str = "none"

    topic: Topic = Field(default_factory=Topic)
    phase: Phase = Phase.UNKNOWN
    momentum: Momentum = Momentum.UNKNOWN
    stance: Stance = Stance.UNKNOWN
    trajectory_note: str = ""

    confidence: dict[str, float] = Field(default_factory=dict)
    # Extractor's justification per field. T0 forever: exists for debugging and
    # eval labeling, never for display.
    evidence: dict[str, str] = Field(default_factory=dict)

    embedding: list[float] | None = None
    embedding_model: str | None = None


# --- published tier: PersonState ----------------------------------------------


class TrajectoryPoint(BaseModel):
    embedding: list[float] | None = None
    phase: Phase = Phase.UNKNOWN
    t: datetime


class PersonState(BaseModel):
    """The only object that crosses the personal boundary, and only the fields
    at or below the person's consented tier (filtering happens at publish time,
    in rollup)."""

    person_id: str
    updated_at: datetime
    presence: PresenceLevel = PresenceLevel.AWAY

    topic_gist: str = ""
    topic_micro: str = ""
    topic_tags: list[str] = Field(default_factory=list)
    phase: Phase = Phase.UNKNOWN
    stance: Stance = Stance.UNKNOWN
    momentum: Momentum = Momentum.UNKNOWN

    # Raw sequence is T0: only the watcher consumes it, and only its conclusions
    # (a candidate event + rationale) ever surface, at T3.
    trajectory: list[TrajectoryPoint] = Field(default_factory=list)
    staleness_hours: float = 0.0
    # Fast-path presence: newest transcript activity, from timestamps only
    # (never content) per the spec. Set client-side at push time; lets the
    # display show aliveness without waiting for semantic extraction.
    last_active: datetime | None = None


# Default visibility tier per published field (spec §tiers). Individuals may opt
# fields UP a tier; the system never does so automatically.
FIELD_TIERS: dict[str, Tier] = {
    "presence": Tier.T2_AMBIENT,
    "topic_gist": Tier.T2_AMBIENT,
    "topic_micro": Tier.T2_AMBIENT,
    "topic_tags": Tier.T2_AMBIENT,
    "phase": Tier.T2_AMBIENT,
    "stance": Tier.T1_AGGREGATE_ONLY,
    "momentum": Tier.T1_AGGREGATE_ONLY,  # the sensitive field; weather only
    "trajectory": Tier.T0_PRIVATE,
    "staleness_hours": Tier.T2_AMBIENT,
    "last_active": Tier.T2_AMBIENT,  # timestamps only, same tier as presence
}


# --- group tier: GroupState -----------------------------------------------------


class Cluster(BaseModel):
    label: str
    member_count: int  # only clusters of size >= 2 are ever rendered


class GroupState(BaseModel):
    generated_at: datetime
    active_count: int = 0
    recently_active_count: int = 0
    # LLM-written from T1+T2 fields only, k>=2 rule enforced by post-check.
    weather: str = ""
    clusters: list[Cluster] = Field(default_factory=list)
    per_person: list[PersonState] = Field(default_factory=list)
