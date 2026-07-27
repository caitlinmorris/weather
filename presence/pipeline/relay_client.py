"""Client for the presence relay. Backend-swappable by design: the rest of
the pipeline only ever calls push / fetch_group / revoke, so replacing the
relay (e.g. with Firestore) touches this file alone.

to_wire() is the client-side half of tier enforcement: it emits ONLY the
shared-tier fields. The relay's WireState whitelist is the server-side half —
either alone catching an over-share is a bug in the other.

Config (env or .env): RELAY_URL, RELAY_TOKEN. Both unset = local-only mode;
every method becomes a quiet no-op returning None.
"""

from __future__ import annotations

import httpx

from presence.core.schema import PersonState
from presence.pipeline.config import boards, env_value

TIMEOUT = 5.0
TIERS = ("presence", "topic")


def to_wire(state: PersonState, tier: str = "topic") -> dict:
    wire = {
        "person_id": state.person_id,
        "updated_at": state.updated_at.isoformat(),
        "presence": state.presence.value,
        "topic_gist": state.topic_gist,
        "topic_micro": state.topic_micro,
        "topic_tags": state.topic_tags,
        "phase": state.phase.value,
        "staleness_hours": state.staleness_hours,
        "last_active": state.last_active.isoformat() if state.last_active else None,
    }
    if tier == "presence":
        # Presence-only board: heartbeat and rhythm, no "what" at all.
        wire.update(topic_gist="", topic_micro="", topic_tags=[],
                    phase="unknown")
    elif tier != "verbose":
        # Standard "topic" tier transmits exactly what the docs promise:
        # the <=5-word micro + tags. The full 15-word gist crosses only
        # on boards that opted into the "verbose" tier (Caitlin, 2026-07-27).
        wire.update(topic_gist="")
    return wire


class RelayClient:
    def __init__(self, url: str | None, token: str | None,
                 name: str = "board", tier: str = "topic"):
        self.url = url.rstrip("/") if url else None
        self.token = token
        self.name = name
        self.tier = tier if tier in TIERS else "topic"

    @classmethod
    def from_env(cls) -> "RelayClient":
        all_boards = boards()
        if all_boards:
            b = all_boards[0]
            return cls(b["url"], b["token"], b["name"], b["tier"])
        return cls(None, None)

    @classmethod
    def boards_from_env(cls) -> list["RelayClient"]:
        return [cls(b["url"], b["token"], b["name"], b["tier"]) for b in boards()]

    @property
    def enabled(self) -> bool:
        return bool(self.url and self.token)

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    def push(self, state: PersonState) -> bool:
        if not self.enabled:
            return False
        response = httpx.post(
            f"{self.url}/state", json=to_wire(state, self.tier),
            headers=self._headers(), timeout=TIMEOUT,
        )
        response.raise_for_status()
        return True

    def fetch_group(self) -> dict | None:
        if not self.enabled:
            return None
        response = httpx.get(
            f"{self.url}/group", headers=self._headers(), timeout=TIMEOUT
        )
        response.raise_for_status()
        return response.json()

    def whoami(self) -> str | None:
        if not self.enabled:
            return None
        response = httpx.get(
            f"{self.url}/whoami", headers=self._headers(), timeout=TIMEOUT
        )
        response.raise_for_status()
        return response.json().get("person_id")

    def revoke(self, person_id: str) -> bool:
        if not self.enabled:
            return False
        response = httpx.delete(
            f"{self.url}/state/{person_id}",
            headers=self._headers(), timeout=TIMEOUT,
        )
        response.raise_for_status()
        return True
