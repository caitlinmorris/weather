"""Batch-extract every allowlisted segment into the private store, then roll
up published PersonState timelines. Idempotent, and aware of two kinds of
change:

- extractor version changed -> the segment is re-extracted (prompt iteration);
- a segment with the same start but a later end -> the session GREW since the
  last pass (live watching); the old observation is replaced.

Chronological order per person matters: each extraction receives the person's
latest prior observation, which is what makes trajectory_note describe motion.

Usage: python -m presence.pipeline.extract_all
"""

from __future__ import annotations

import sys
from datetime import datetime

from presence.core import rollup
from presence.extract.extractor import (
    ExtractionError,
    Extractor,
    extraction_backend,
    load_api_key,
)
from presence.pipeline.config import PRIVATE_DB, PUBLIC_DB
from presence.pipeline.sample_extract import MIN_MINUTES, gather_segments
from presence.pipeline.store import PrivateStore


def run(min_minutes: int = MIN_MINUTES, verbose: bool = True) -> dict:
    """One extract-and-publish pass. Returns counts for the caller's log line."""
    if extraction_backend() != "claude_cli" and not load_api_key():
        raise ExtractionError("no ANTHROPIC_API_KEY in environment or .env")

    private = PrivateStore(PRIVATE_DB)

    by_person: dict[str, list] = {}
    for person, seg in gather_segments(min_minutes=min_minutes):
        by_person.setdefault(person, []).append(seg)
    for segments in by_person.values():
        segments.sort(key=lambda s: s.t_start)

    extractor = Extractor()
    counts = {"extracted": 0, "skipped": 0, "failed": 0}

    for person, segments in sorted(by_person.items()):
        for seg in segments:
            start, end = seg.t_start.isoformat(), seg.t_end.isoformat()

            # v1.0 unit of analysis: observations are extraction WINDOWS,
            # appended — a long session becomes a sequence, never one
            # replaced label. The rolling-update cost property is kept: each
            # window reads only events past what previous windows covered,
            # with the latest observation as compressed memory. (History
            # extracted under older prompt versions is left standing; no
            # mass re-extraction on version bumps.)
            covered = private.covered_until(person, start, end)
            if covered is not None and covered >= seg.t_end:
                counts["skipped"] += 1
                continue
            delta_events = None
            if covered is not None:
                delta_events = [
                    e for e in seg.events
                    if e.timestamp and e.timestamp > covered
                ]
                if not delta_events:
                    counts["skipped"] += 1
                    continue
            previous = private.latest(person)

            try:
                obs = extractor.extract_segment(
                    seg, person_id=person, previous=previous, events=delta_events
                )
            except (ExtractionError, ValueError) as e:
                if verbose:
                    print(f"  FAILED {person} {seg.t_start:%Y-%m-%d %H:%M}: {e}")
                counts["failed"] += 1
                continue
            obs.t_start = covered or seg.t_start  # window bounds, not segment
            obs.t_end = seg.t_end
            private.add(obs)
            counts["extracted"] += 1
            if verbose:
                print(f"  {person:<16} {obs.t_start:%Y-%m-%d %H:%M}  {obs.topic.gist}")

    public = rollup.open_public_writer(PUBLIC_DB)
    for person in sorted(by_person):
        n = rollup.publish_history(private, public, person)
        if verbose:
            print(f"published {n:3d} states for {person}")
    public.close()
    private.close()
    return counts


def main() -> None:
    try:
        counts = run()
    except ExtractionError as e:
        print(f"cannot run: {e}")
        sys.exit(1)
    print(
        f"\nextracted {counts['extracted']}, skipped {counts['skipped']}"
        f" (already current), failed {counts['failed']}"
    )


if __name__ == "__main__":
    main()
