"""Split transcript event streams into work segments.

"What is a session?" is open question 1 in the person-model spec; v0 answer is
30-minute-activity-gap splitting within each transcript file (one file is one
Claude Code session, but a session left open overnight is not one work segment).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from presence.pipeline.config import SESSION_GAP_MINUTES
from presence.pipeline.transcript_parser import TranscriptEvent


@dataclass
class Segment:
    """A contiguous stretch of work: the unit the extractor operates on."""

    session_id: str | None
    project_cwd: str | None
    t_start: datetime
    t_end: datetime
    events: list[TranscriptEvent] = field(default_factory=list)
    origin: str = "claude_code"  # which CaptureSource produced this

    @property
    def duration_minutes(self) -> float:
        return (self.t_end - self.t_start).total_seconds() / 60

    @property
    def human_prompt_count(self) -> int:
        return sum(1 for e in self.events if e.is_human_prompt)

    def __repr__(self) -> str:  # metadata only
        return (
            f"Segment(session={self.session_id!r}, start={self.t_start}, "
            f"minutes={self.duration_minutes:.0f}, events={len(self.events)}, "
            f"prompts={self.human_prompt_count})"
        )


def segment_events(
    events: list[TranscriptEvent], gap_minutes: int = SESSION_GAP_MINUTES
) -> list[Segment]:
    """Split one transcript's events into segments at activity gaps.

    Events without timestamps (snapshots, some system records) ride along with
    the current segment rather than breaking it.
    """
    gap = timedelta(minutes=gap_minutes)
    segments: list[Segment] = []
    current: Segment | None = None
    last_t: datetime | None = None

    for event in events:
        t = event.timestamp
        if t is not None and (current is None or (last_t and t - last_t > gap)):
            current = Segment(
                session_id=event.session_id,
                project_cwd=event.cwd,
                t_start=t,
                t_end=t,
            )
            segments.append(current)
        if current is None:
            # Timestampless events before the first timestamped one: drop; they
            # carry no work signal on their own.
            continue
        current.events.append(event)
        if t is not None:
            current.t_end = max(current.t_end, t)
            last_t = t

    return segments
