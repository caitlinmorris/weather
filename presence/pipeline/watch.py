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

import json
import time
from datetime import datetime

import httpx

from presence.pipeline import extract_all
from presence.pipeline.config import GROUP_CACHE, PERSON_ID, PUBLIC_DB
from presence.pipeline.pause import is_paused
from presence.pipeline.relay_client import RelayClient
from presence.pipeline.store import PublicStore
from presence.render.build_page import build

INTERVAL_SECONDS = 300
# Live mode wants the current session visible before it is 10 minutes old.
LIVE_MIN_MINUTES = 5


BACKFILL_HOURS = 4  # match the field view's window


def sync_relay(client: RelayClient, store: PublicStore) -> str:
    """Push own recent history (not just latest): the relay dedups by
    timestamp, so re-pushing the window every cycle is idempotent and makes
    the ring self-healing across app and relay restarts. Only PERSON_ID's
    states are ever pushed — in projects (pseudo-people) mode no state
    carries that id, so nothing leaves even with a relay configured."""
    from datetime import datetime, timedelta, timezone

    cutoff = datetime.now(timezone.utc) - timedelta(hours=BACKFILL_HOURS)
    window = [s for s in store.history(PERSON_ID) if s.updated_at >= cutoff]
    pushed = sum(1 for s in window if client.push(s))
    group = client.fetch_group()
    if group is not None:
        GROUP_CACHE.write_text(json.dumps(group))
    return f"relay: pushed={pushed} group={len((group or {}).get('per_person', []))}"


def main() -> None:
    client = RelayClient.from_env()
    mode = "relay " + client.url if client.enabled else "local-only"
    print(f"we.ather watch: extracting every 5 min ({mode}) · Ctrl-C to stop")
    while True:
        stamp = f"[{datetime.now():%H:%M}]"
        if is_paused():
            print(f"{stamp} paused — no capture, no push (resume with:"
                  " python -m presence.pipeline.pause resume)")
            time.sleep(INTERVAL_SECONDS)
            continue
        try:
            counts = extract_all.run(min_minutes=LIVE_MIN_MINUTES, verbose=False)
            store = PublicStore(PUBLIC_DB)
            note = ""
            if client.enabled:
                # Relay trouble must never freeze the local widget: sync has
                # its own guard; build always runs.
                try:
                    note = " · " + sync_relay(client, store)
                except httpx.HTTPStatusError as e:
                    code = e.response.status_code
                    hint = (" — PRESENCE_PERSON_ID doesn't match your token's"
                            " identity; fix .env and restart"
                            if code == 403 else "")
                    note = f" · RELAY SYNC FAILED: HTTP {code}{hint}"
                except Exception as e:
                    note = f" · relay sync failed: {e}"
            build(store)
            store.close()
            if counts["extracted"] or counts["failed"] or note:
                print(f"{stamp} extracted {counts['extracted']},"
                      f" failed {counts['failed']}{note}")
            else:
                print(f"{stamp} no change")
        except Exception as e:  # keep the loop alive across transient failures
            print(f"{stamp} cycle failed: {e}")
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
