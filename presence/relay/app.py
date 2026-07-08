"""The presence relay: a tiny authenticated store for published PersonStates.

Security model in docs/security-model.md — the properties enforced here:
- WireState is a whitelist with extra="forbid": fields beyond the shared tier
  (momentum, stance, trajectory, evidence, anything unknown) are REJECTED,
  not ignored. Tier enforcement is server-side, never client courtesy.
- Tokens are held only as SHA-256 hashes; comparison is constant-time.
  A token can write and delete only its own person's state.
- Storage is in-memory: current states + a bounded, TTL-pruned ring buffer.
  A relay restart loses nothing that a client push won't restore in minutes,
  and there is deliberately no long-term archive to steal.
- Logs carry metadata only; state bodies are never logged.

Config via env:
  RELAY_TOKENS  JSON mapping person_id -> sha256 hex of their bearer token,
                e.g. {"caitlin": "ab12...", "dan": "cd34..."}
                Generate pairs with: python -m presence.relay.mktoken <person>

Run locally:  uvicorn presence.relay.app:app --port 8080
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from collections import defaultdict, deque
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from presence.core.schema import Openness, Phase, PresenceLevel

RING_MAX = 40
RING_TTL_SECONDS = 7 * 24 * 3600
RATE_LIMIT_PER_MINUTE = 120


class WireState(BaseModel):
    """The complete set of fields that may cross the network. Mirrors the
    JSON example in docs/security-model.md — keep the two in sync."""

    model_config = ConfigDict(extra="forbid")

    person_id: str = Field(max_length=40)
    updated_at: datetime
    presence: PresenceLevel = PresenceLevel.AWAY
    topic_gist: str = Field("", max_length=240)
    topic_micro: str = Field("", max_length=80)
    topic_tags: list[str] = Field(default_factory=list, max_length=7)
    phase: Phase = Phase.UNKNOWN
    openness: Openness = Openness.UNKNOWN
    staleness_hours: float = Field(0.0, ge=0)


def create_app(token_hashes: dict[str, str] | None = None) -> FastAPI:
    if token_hashes is None:
        raw = os.environ.get("RELAY_TOKENS", "")
        if not raw:
            raise RuntimeError("RELAY_TOKENS not set; refusing to start open")
        token_hashes = json.loads(raw)

    app = FastAPI(title="we.ather relay", docs_url=None, redoc_url=None)
    rings: dict[str, deque] = defaultdict(lambda: deque(maxlen=RING_MAX))
    request_log: dict[str, deque] = defaultdict(lambda: deque(maxlen=RATE_LIMIT_PER_MINUTE))

    def authed_person(authorization: str = Header(default="")) -> str:
        token = authorization.removeprefix("Bearer ").strip()
        digest = hashlib.sha256(token.encode()).hexdigest()
        for person, stored in token_hashes.items():
            if hmac.compare_digest(digest, stored):
                _rate_limit(person)
                return person
        raise HTTPException(401, "unknown token")

    def _rate_limit(person: str) -> None:
        now = time.monotonic()
        log = request_log[person]
        if len(log) == log.maxlen and now - log[0] < 60:
            raise HTTPException(429, "slow down")
        log.append(now)

    def _prune(ring: deque) -> None:
        cutoff = time.time() - RING_TTL_SECONDS
        while ring and ring[0][0] < cutoff:
            ring.popleft()

    @app.post("/state", status_code=204)
    def push_state(state: WireState, person: str = Depends(authed_person)):
        if state.person_id != person:
            raise HTTPException(403, "token may only write its own state")
        ring = rings[person]
        _prune(ring)
        payload = state.model_dump(mode="json")
        # Idempotent by timestamp: clients backfill their recent window every
        # cycle, so the ring self-heals after client or relay restarts without
        # accumulating duplicates.
        if any(s["updated_at"] == payload["updated_at"] for _, s in ring):
            return
        ring.append((time.time(), payload))

    @app.get("/group")
    def group(person: str = Depends(authed_person)):
        per_person = []
        for member, ring in rings.items():
            _prune(ring)
            if ring:
                per_person.append(
                    {"person_id": member, "states": [s for _, s in ring]}
                )
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "per_person": per_person,
        }

    @app.delete("/state/{person_id}", status_code=204)
    def revoke(person_id: str, person: str = Depends(authed_person)):
        if person_id != person:
            raise HTTPException(403, "token may only revoke its own state")
        rings.pop(person, None)  # idempotent: absent is fine

    @app.get("/health")
    def health():
        return {"ok": True, "people_present": len([r for r in rings.values() if r])}

    return app


# uvicorn entry point (reads RELAY_TOKENS from env)
if os.environ.get("RELAY_TOKENS"):
    app = create_app()
