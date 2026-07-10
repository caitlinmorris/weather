"""Milestone A exit test: run the extractor on a few real segments and print
the observations for eyeballing. Are the gists colleague-appropriate? Is
unknown being used honestly? (Observations are private-tier data printed to
the owner's own terminal — that's the point of the exercise.)

Usage: python -m presence.pipeline.sample_extract [n_segments]
"""

from __future__ import annotations

import sys

from presence.extract.extractor import ExtractionError, Extractor, load_api_key
from presence.pipeline.config import allowed_project_dirs, person_for_project
from presence.pipeline.segmenter import Segment, segment_events
from presence.pipeline.transcript_parser import parse_transcript

MIN_MINUTES = 10  # short segments make weak eyeball tests


def gather_segments(min_minutes: int = MIN_MINUTES) -> list[tuple[str, Segment]]:
    pairs = []
    for project in allowed_project_dirs():
        person = person_for_project(project.name)
        for f in sorted(project.glob("*.jsonl")):
            for seg in segment_events(list(parse_transcript(f))):
                if seg.duration_minutes >= min_minutes:
                    pairs.append((person, seg))
    pairs.sort(key=lambda p: p[1].t_start, reverse=True)
    return pairs


def find_segment(
    person_id: str, t_start_iso: str, t_end_iso: str, min_minutes: int = 5
) -> Segment | None:
    """Locate the live segment matching a stored observation's span — the
    sanctioned path for eval tools to reach transcript text (raw access
    stays inside pipeline/, per the boundary tests)."""
    for person, seg in gather_segments(min_minutes=min_minutes):
        if (person == person_id
                and seg.t_start.isoformat() == t_start_iso
                and seg.t_end.isoformat() == t_end_iso):
            return seg
    return None


def print_observation(person: str, seg: Segment, obs) -> None:
    print(f"\n{'=' * 70}")
    print(
        f"{person}  |  {seg.t_start:%Y-%m-%d %H:%M}  "
        f"({seg.duration_minutes:.0f} min, {seg.human_prompt_count} prompts)"
    )
    print(f"  gist:       {obs.topic.gist}")
    print(f"  tags:       {', '.join(obs.topic.tags)}   [{obs.topic.domain}]")
    for field in ("phase", "momentum", "stance", "openness"):
        value = getattr(obs, field).value
        conf = obs.confidence.get(field)
        conf_str = f"{conf:.2f}" if conf is not None else "  — "
        print(f"  {field:<10}  {value:<22} conf {conf_str}")
    print(f"  trajectory: {obs.trajectory_note}")
    print("  evidence:")
    for field, note in obs.evidence.items():
        print(f"    {field}: {note}")


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 4

    if not load_api_key():
        print(
            "No API key found. Create a file named .env at the repo root containing:\n"
            "  ANTHROPIC_API_KEY=sk-ant-...\n"
            "(or export it in your shell), then rerun this command."
        )
        sys.exit(1)

    pairs = gather_segments()[:n]
    if not pairs:
        print("No segments >= 10 minutes found in allowlisted projects.")
        sys.exit(1)

    extractor = Extractor()
    print(f"Extracting {len(pairs)} segments with {extractor.extractor_version} …")
    for person, seg in pairs:
        try:
            obs = extractor.extract_segment(seg, person_id=person)
        except ExtractionError as e:
            print(f"\n{person} {seg.t_start:%Y-%m-%d %H:%M}: extraction failed ({e})")
            continue
        print_observation(person, seg, obs)

    print(
        "\nExit test (docs/v0.1-plan.md, milestone A): would you show these gists"
        "\nto a colleague? Is unknown being used honestly? Note misses for the"
        "\nprompt-v2 conversation."
    )


if __name__ == "__main__":
    main()
