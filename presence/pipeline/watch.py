"""Live self-watching loop: every few minutes, extract whatever grew, republish
states, rebuild the page. Pair with ambient.html#live in a small window.

This is the polling stand-in for the real hook-driven worker (Milestone C in
docs/next-steps.md); it trades a little latency for zero install surface.

Cost note: only new or grown segments trigger extraction, and each call reads
only the delta plus the prior observation, so a normal workday costs on the
order of a few dozen small Haiku calls.

Usage: python -m presence.pipeline.watch  (Ctrl-C to stop)
"""

from __future__ import annotations

import time
from datetime import datetime

from presence.pipeline import extract_all
from presence.pipeline.config import PUBLIC_DB
from presence.pipeline.store import PublicStore
from presence.render.build_page import build

INTERVAL_SECONDS = 300
# Live mode wants the current session visible before it is 10 minutes old.
LIVE_MIN_MINUTES = 5


def main() -> None:
    print("presence watch: extracting every 5 min · Ctrl-C to stop")
    while True:
        stamp = f"[{datetime.now():%H:%M}]"
        try:
            counts = extract_all.run(min_minutes=LIVE_MIN_MINUTES, verbose=False)
            store = PublicStore(PUBLIC_DB)
            build(store)
            store.close()
            if counts["extracted"] or counts["failed"]:
                print(f"{stamp} extracted {counts['extracted']}, failed {counts['failed']}")
            else:
                print(f"{stamp} no change")
        except Exception as e:  # keep the loop alive across transient failures
            print(f"{stamp} cycle failed: {e}")
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
