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
from presence.pipeline.config import env_value

TIMEOUT = 5.0


def to_wire(state: PersonState) -> dict:
    return {
        "person_id": state.person_id,
        "updated_at": state.updated_at.isoformat(),
        "presence": state.presence.value,
        "topic_gist": state.topic_gist,
        "topic_micro": state.topic_micro,
        "topic_tags": state.topic_tags,
        "phase": state.phase.value,
        "openness": state.openness.value,
        "staleness_hours": state.staleness_hours,
        "last_active": state.last_active.isoformat() if state.last_active else None,
    }


class RelayClient:
    def __init__(self, url: str | None, token: str | None):
        self.url = url.rstrip("/") if url else None
        self.token = token

    @classmethod
    def from_env(cls) -> "RelayClient":
        return cls(env_value("RELAY_URL"), env_value("RELAY_TOKEN"))

    @property
    def enabled(self) -> bool:
        return bool(self.url and self.token)

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    def push(self, state: PersonState) -> bool:
        if not self.enabled:
            return False
        response = httpx.post(
            f"{self.url}/state", json=to_wire(state),
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
