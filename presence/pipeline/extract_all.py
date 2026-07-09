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
from presence.extract.extractor import ExtractionError, Extractor, load_api_key
from presence.pipeline.config import PRIVATE_DB, PUBLIC_DB
from presence.pipeline.sample_extract import MIN_MINUTES, gather_segments
from presence.pipeline.store import PrivateStore


def run(min_minutes: int = MIN_MINUTES, verbose: bool = True) -> dict:
    """One extract-and-publish pass. Returns counts for the caller's log line."""
    if not load_api_key():
        raise ExtractionError("no ANTHROPIC_API_KEY in environment or .env")

    private = PrivateStore(PRIVATE_DB)
    # (person, t_start) -> (t_end, extractor_version) of stored observations.
    existing = {
        (p, a): (b, v) for (p, a, b), v in private.spans().items()
    }

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
            stored = existing.get((person, start))
            if stored == (end, extractor.extractor_version):
                counts["skipped"] += 1
                continue

            # Rolling update (the design's core cost property): when a
            # segment merely GREW under the same extractor version, feed the
            # model only the events past the previous observation plus that
            # observation as compressed memory — never the whole session
            # again. Full re-reads happen only on version changes.
            delta_events = None
            previous = None
            if stored is not None:
                stored_end, stored_version = stored
                if stored_version == extractor.extractor_version:
                    previous = private.get_span(person, start, stored_end)
                    watermark = datetime.fromisoformat(stored_end)
                    delta_events = [
                        e for e in seg.events
                        if e.timestamp and e.timestamp > watermark
                    ]
                    if not delta_events:
                        counts["skipped"] += 1
                        continue  # grew by nothing extractable; keep old obs
                private.delete_span(person, start, stored_end)
            if previous is None:
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
            private.add(obs)
            counts["extracted"] += 1
            if verbose:
                print(f"  {person:<16} {seg.t_start:%Y-%m-%d %H:%M}  {obs.topic.gist}")

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
