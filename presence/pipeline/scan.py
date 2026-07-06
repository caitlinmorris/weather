"""Inventory the allowlisted transcripts: how much raw material exists for the
replay demo. Prints metadata only (counts, durations, dates) — never content.

Usage: python -m presence.pipeline.scan
"""

from __future__ import annotations

from presence.pipeline.config import allowed_project_dirs
from presence.pipeline.segmenter import segment_events
from presence.pipeline.transcript_parser import parse_transcript


def main() -> None:
    grand_segments = 0
    grand_minutes = 0.0

    for project in allowed_project_dirs():
        files = sorted(project.glob("*.jsonl"))
        if not files:
            continue
        segments = []
        for f in files:
            segments.extend(segment_events(list(parse_transcript(f))))
        # Segments under 2 minutes are opened-and-abandoned sessions, not work.
        segments = [s for s in segments if s.duration_minutes >= 2]
        if not segments:
            continue

        minutes = sum(s.duration_minutes for s in segments)
        prompts = sum(s.human_prompt_count for s in segments)
        first = min(s.t_start for s in segments)
        last = max(s.t_end for s in segments)
        grand_segments += len(segments)
        grand_minutes += minutes

        print(f"\n{project.name}")
        print(f"  files: {len(files)}  segments: {len(segments)}")
        print(f"  work time: {minutes / 60:.1f}h   human prompts: {prompts}")
        print(f"  span: {first.date()} -> {last.date()}")
        for s in segments[-3:]:
            print(
                f"    {s.t_start:%m-%d %H:%M}  {s.duration_minutes:4.0f} min  "
                f"{len(s.events):4d} events  {s.human_prompt_count:3d} prompts"
            )

    print(f"\nTOTAL: {grand_segments} segments, {grand_minutes / 60:.1f}h of material")


if __name__ == "__main__":
    main()
