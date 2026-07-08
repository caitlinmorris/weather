"""Consent switch: pause / resume / status.

Pausing does two things, in order: revokes your state at the relay (you
render as ordinary "away" to the group within one poll) and sets a local
flag that stops the watch loop from extracting or pushing anything until
you resume. Nobody is notified; absence is indistinguishable from not
working (design principle 4).

Usage:
    python -m presence.pipeline.pause          # pause
    python -m presence.pipeline.pause resume
    python -m presence.pipeline.pause status
"""

from __future__ import annotations

import sys

from presence.pipeline.config import DATA_DIR, PAUSE_FLAG, PERSON_ID
from presence.pipeline.relay_client import RelayClient


def is_paused() -> bool:
    return PAUSE_FLAG.exists()


def pause() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PAUSE_FLAG.touch()
    client = RelayClient.from_env()
    if client.enabled:
        try:
            client.revoke(PERSON_ID)
            print(f"paused · relay state for '{PERSON_ID}' purged; you now read as away")
        except Exception as e:
            print(f"paused locally, but relay revoke failed ({e}) — "
                  "your last state will age out; retry when online")
    else:
        print("paused · local-only mode, nothing was being shared")


def resume() -> None:
    PAUSE_FLAG.unlink(missing_ok=True)
    print("resumed · capture and sharing restart on the next watch cycle")


def main() -> None:
    command = sys.argv[1] if len(sys.argv) > 1 else "pause"
    if command == "pause":
        pause()
    elif command == "resume":
        resume()
    elif command == "status":
        print("paused" if is_paused() else "active")
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
