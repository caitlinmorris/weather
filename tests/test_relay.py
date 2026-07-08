"""Relay security properties as tests. Each maps to a claim in
docs/security-model.md — if one fails, the doc is lying."""

import hashlib
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from presence.core.schema import (
    Momentum,
    Openness,
    PersonState,
    Phase,
    PresenceLevel,
    Stance,
)
from presence.pipeline.relay_client import to_wire
from presence.relay.app import create_app

TOK_A, TOK_B = "token-alice-secret", "token-bob-secret"
HASHES = {
    "alice": hashlib.sha256(TOK_A.encode()).hexdigest(),
    "bob": hashlib.sha256(TOK_B.encode()).hexdigest(),
}
T = datetime(2026, 7, 8, 9, 0, tzinfo=timezone.utc).isoformat()


def wire(person="alice", **over):
    base = {
        "person_id": person,
        "updated_at": T,
        "presence": "active",
        "topic_gist": "synthetic status",
        "topic_micro": "synthesizing fixtures",
        "topic_tags": ["synthetic"],
        "phase": "building",
        "openness": "neutral",
        "staleness_hours": 0.1,
    }
    base.update(over)
    return base


@pytest.fixture
def client():
    return TestClient(create_app(token_hashes=HASHES))


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_duplicate_pushes_dedup_by_timestamp(client):
    for _ in range(3):
        assert client.post("/state", json=wire(), headers=auth(TOK_A)).status_code == 204
    group = client.get("/group", headers=auth(TOK_B)).json()
    assert len(group["per_person"][0]["states"]) == 1
    # A different timestamp is a new entry, not a duplicate.
    later = wire(updated_at="2026-07-08T10:00:00+00:00")
    client.post("/state", json=later, headers=auth(TOK_A))
    group = client.get("/group", headers=auth(TOK_B)).json()
    assert len(group["per_person"][0]["states"]) == 2


def test_push_and_group_roundtrip(client):
    assert client.post("/state", json=wire(), headers=auth(TOK_A)).status_code == 204
    group = client.get("/group", headers=auth(TOK_B)).json()
    people = {p["person_id"] for p in group["per_person"]}
    assert people == {"alice"}
    assert group["per_person"][0]["states"][0]["topic_micro"] == "synthesizing fixtures"


def test_unknown_token_rejected(client):
    assert client.post("/state", json=wire(), headers=auth("guess")).status_code == 401
    assert client.get("/group", headers=auth("guess")).status_code == 401
    assert client.get("/group").status_code == 401  # no header at all


def test_token_cannot_write_someone_elses_state(client):
    r = client.post("/state", json=wire(person="bob"), headers=auth(TOK_A))
    assert r.status_code == 403


def test_over_tier_fields_rejected_not_ignored(client):
    for forbidden in ("momentum", "stance", "trajectory", "evidence"):
        r = client.post(
            "/state", json=wire(**{forbidden: "grinding"}), headers=auth(TOK_A)
        )
        assert r.status_code == 422, f"{forbidden} was accepted"


def test_oversize_and_invalid_values_rejected(client):
    assert client.post(
        "/state", json=wire(topic_gist="x" * 500), headers=auth(TOK_A)
    ).status_code == 422
    assert client.post(
        "/state", json=wire(phase="vibing"), headers=auth(TOK_A)
    ).status_code == 422
    assert client.post(
        "/state", json=wire(topic_tags=["t"] * 12), headers=auth(TOK_A)
    ).status_code == 422


def test_revocation_purges_and_is_own_only(client):
    client.post("/state", json=wire(), headers=auth(TOK_A))
    # Bob cannot revoke Alice.
    assert client.delete("/state/alice", headers=auth(TOK_B)).status_code == 403
    # Alice revokes herself: gone from the group entirely, ring buffer included.
    assert client.delete("/state/alice", headers=auth(TOK_A)).status_code == 204
    group = client.get("/group", headers=auth(TOK_B)).json()
    assert group["per_person"] == []
    # Idempotent: revoking while absent is not an error.
    assert client.delete("/state/alice", headers=auth(TOK_A)).status_code == 204


def test_to_wire_strips_private_tier_fields():
    state = PersonState(
        person_id="alice",
        updated_at=datetime(2026, 7, 8, 9, 0, tzinfo=timezone.utc),
        presence=PresenceLevel.ACTIVE,
        topic_gist="synthetic status",
        momentum=Momentum.GRINDING,   # T1: must not survive to_wire
        stance=Stance.LEARNING,       # T1: must not survive to_wire
        phase=Phase.BUILDING,
        openness=Openness.NEUTRAL,
    )
    payload = to_wire(state)
    assert "momentum" not in payload and "stance" not in payload
    assert "trajectory" not in payload
    assert payload["topic_gist"] == "synthetic status"


def test_wire_payload_is_accepted_by_relay(client):
    # The client's serializer and the relay's whitelist must stay in sync.
    state = PersonState(
        person_id="alice",
        updated_at=datetime(2026, 7, 8, 9, 0, tzinfo=timezone.utc),
        phase=Phase.DEBUGGING,
    )
    r = client.post("/state", json=to_wire(state), headers=auth(TOK_A))
    assert r.status_code == 204
