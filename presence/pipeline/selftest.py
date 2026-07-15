"""Install self-test: verifies every layer a participant needs, without
spending API money (the extraction harness runs against a fake client on
synthetic data). Run by install.sh; safe to rerun anytime.

Usage: python -m presence.pipeline.selftest
"""

from __future__ import annotations

import sys

from presence.pipeline import config
from presence.pipeline.pause import is_paused
from presence.pipeline.relay_client import RelayClient
from presence.pipeline.transcript_parser import parse_transcript

PASS, FAIL, WARN = "  ok ", " FAIL", " warn"
failures = 0


def report(status: str, message: str) -> None:
    global failures
    if status == FAIL:
        failures += 1
    print(f"[{status}] {message}")


def main() -> None:
    v = sys.version_info
    report(PASS if v >= (3, 12) else FAIL, f"python {v.major}.{v.minor}")

    report(
        PASS if config.PERSON_ID != "me" else WARN,
        f"person id: {config.PERSON_ID}" + ("" if config.PERSON_ID != "me" else " (default — set PRESENCE_PERSON_ID)"),
    )
    report(PASS, f"group mode: {config.GROUP_MODE}")

    requested = [n.strip() for n in
                 (config.env_value("PRESENCE_SOURCES") or "claude_code").split(",")
                 if n.strip()]
    from presence.pipeline.sources import active_sources
    active_names = [s.name for s in active_sources()]
    for name in requested:
        report(PASS if name in active_names else FAIL,
               f"capture source '{name}': "
               + ("active" if name in active_names
                  else "configured but unavailable (tool data missing or"
                       " its allowlist empty)"))

    if "claude_code" in requested:
        if not config.ALLOWED_PROJECT_PREFIXES:
            report(FAIL, "PRESENCE_ALLOWLIST is empty — no projects will be captured")
        else:
            transcripts = config.allowed_transcripts()
            status = PASS if transcripts else WARN
            report(status, f"allowlist: {len(config.ALLOWED_PROJECT_PREFIXES)} prefixes, "
                           f"{len(transcripts)} transcript files found")
            if transcripts:
                newest = max(transcripts, key=lambda p: p.stat().st_mtime)
                events = list(parse_transcript(newest))
                report(PASS if events else FAIL,
                       f"parsed newest transcript: {len(events)} events (structure only)")

    report(
        PASS if config.env_value("ANTHROPIC_API_KEY") else FAIL,
        "ANTHROPIC_API_KEY " + ("present" if config.env_value("ANTHROPIC_API_KEY") else "missing from .env"),
    )

    # Extraction harness end-to-end on synthetic data, zero API cost.
    try:
        sys.path.insert(0, str(config.REPO_ROOT))
        from tests.synthetic import write_synthetic_transcript
        from tests.test_extractor_harness import VALID_RESPONSE, FakeClient
        from presence.extract.extractor import Extractor
        from presence.pipeline.segmenter import segment_events
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "synthetic.jsonl"
            write_synthetic_transcript(f)
            seg = segment_events(list(parse_transcript(f)), gap_minutes=60)[0]
            obs = Extractor(client=FakeClient([VALID_RESPONSE])).extract_segment(
                seg, person_id="selftest"
            )
        report(PASS, f"extraction harness (synthetic, no API cost): gist='{obs.topic.gist}'")
    except Exception as e:
        report(FAIL, f"extraction harness: {e}")

    clients = [c for c in RelayClient.boards_from_env() if c.enabled]
    if not clients:
        report(WARN, "relay: no boards configured (local-only mode)")
    for client in clients:
        try:
            group = client.fetch_group()
            report(PASS, f"board '{client.name}' (tier {client.tier}): "
                         f"reachable, {len(group.get('per_person', []))} present")
            who = client.whoami()
            if who == config.PERSON_ID:
                report(PASS, f"board '{client.name}': token matches '{who}'")
            else:
                report(FAIL, f"board '{client.name}': token belongs to "
                             f"'{who}' but PRESENCE_PERSON_ID is "
                             f"'{config.PERSON_ID}' — every push will be "
                             f"rejected. Make them match in .env, restart.")
        except Exception as e:
            report(FAIL, f"board '{client.name}': {e}")

    report(WARN if is_paused() else PASS, "paused" if is_paused() else "consent: active")

    print()
    if failures:
        print(f"{failures} check(s) failed — see above.")
        sys.exit(1)
    print("all checks passed")


if __name__ == "__main__":
    main()
