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
from presence.pipeline.config import (
    PERSON_ID,
    PUBLIC_DB,
    allowed_transcripts,
    env_value,
    group_cache_path,
)
from presence.pipeline.pause import is_paused
from presence.pipeline.relay_client import RelayClient
from presence.pipeline.store import PublicStore
from presence.render.build_page import build

# PRESENCE_DEBUG=1 in .env tightens the whole loop for debugging sessions
# (extraction runs more often on grown segments — costs scale accordingly;
# turn it off for normal ambient use).
DEBUG_MODE = env_value("PRESENCE_DEBUG") == "1"
INTERVAL_SECONDS = int(env_value("PRESENCE_INTERVAL_SECONDS") or (60 if DEBUG_MODE else 300))
# Live mode wants the current session visible before it is 10 minutes old.
LIVE_MIN_MINUTES = 2 if DEBUG_MODE else 5


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
    if not window:
        # No recent states (quiet afternoon) still deserves a heartbeat:
        # push the latest state, however old, so presence isn't invisible.
        latest = store.latest(PERSON_ID)
        window = [latest] if latest else []
    if not window:
        # Zero states for this identity is loud, not silent: it usually means
        # PRESENCE_PERSON_ID changed after extraction ran under another name.
        return (f"relay: NOTHING TO PUSH — no states exist for "
                f"'{PERSON_ID}' (renamed? run migrate_identity, restart)")
    if window:
        # Fast-path presence heartbeat: newest allowlist-scoped activity
        # instant across all capture sources (timestamps only, never
        # content). Latest-write-wins dedup refreshes the entry in place.
        from presence.pipeline.sources import active_sources

        beats = [b for s in active_sources() if (b := s.last_activity())]
        if beats:
            window[-1].last_active = max(beats)
    pushed = sum(1 for s in window if client.push(s))
    group = client.fetch_group()
    if group is not None:
        group_cache_path(client.name).write_text(json.dumps(group))
    return (f"{client.name}: pushed={pushed} "
            f"group={len((group or {}).get('per_person', []))}")


def main() -> None:
    clients = [c for c in RelayClient.boards_from_env() if c.enabled]
    mode = ("boards: " + ", ".join(c.name for c in clients)) if clients else "local-only"
    if DEBUG_MODE:
        mode += " · DEBUG"
    print(f"we.ather watch: cycle every {INTERVAL_SECONDS}s ({mode}) · Ctrl-C to stop")
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
            notes = []
            for client in clients:
                # Relay trouble must never freeze the local widget (or the
                # OTHER boards): each board syncs under its own guard.
                try:
                    notes.append(sync_relay(client, store))
                except httpx.HTTPStatusError as e:
                    code = e.response.status_code
                    hint = (" — PRESENCE_PERSON_ID doesn't match your token's"
                            " identity; fix .env and restart"
                            if code == 403 else "")
                    notes.append(f"{client.name}: SYNC FAILED HTTP {code}{hint}")
                except Exception as e:
                    notes.append(f"{client.name}: sync failed: {e}")
            note = (" · " + " | ".join(notes)) if notes else ""
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
