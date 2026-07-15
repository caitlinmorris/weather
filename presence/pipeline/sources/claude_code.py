"""Claude Code capture source — the reference CaptureSource.

Moved behind the interface with zero behavior change: local JSONL
transcripts under ~/.claude/projects, allowlisted by encoded project-dir
prefix (PRESENCE_ALLOWLIST), segmented on 30-minute gaps.
"""

from __future__ import annotations

from datetime import datetime, timezone

from presence.pipeline.config import (
    allowed_transcripts,
    allowed_project_dirs,
    person_for_project,
)
from presence.pipeline.segmenter import Segment, segment_events
from presence.pipeline.transcript_parser import parse_transcript


class ClaudeCodeSource:
    name = "claude_code"

    def available(self) -> bool:
        return bool(allowed_project_dirs())

    def segments(self, min_minutes: int) -> list[tuple[str, Segment]]:
        pairs = []
        for project in allowed_project_dirs():
            person = person_for_project(project.name)
            for f in sorted(project.glob("*.jsonl")):
                for seg in segment_events(list(parse_transcript(f))):
                    if seg.duration_minutes >= min_minutes:
                        seg.origin = self.name
                        pairs.append((person, seg))
        return pairs

    def last_activity(self) -> datetime | None:
        mtimes = [f.stat().st_mtime for f in allowed_transcripts()]
        if not mtimes:
            return None
        return datetime.fromtimestamp(max(mtimes), tz=timezone.utc)
