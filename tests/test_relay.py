"""Relay security properties as tests. Each maps to a claim in
docs/security-model.md — if one fails, the doc is lying."""

import hashlib
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from presence.core.schema import (
    Momentum,
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
    # Latest write wins: a corrected state replaces its stale ring entry.
    client.post("/state", json=wire(phase="polishing"), headers=auth(TOK_A))
    group = client.get("/group", headers=auth(TOK_B)).json()
    assert len(group["per_person"][0]["states"]) == 1
    assert group["per_person"][0]["states"][0]["phase"] == "polishing"
    # A different timestamp is a new entry, not a duplicate.
    later = wire(updated_at="2026-07-08T10:00:00+00:00")
    client.post("/state", json=later, headers=auth(TOK_A))
    group = client.get("/group", headers=auth(TOK_B)).json()
    assert len(group["per_person"][0]["states"]) == 2


def test_last_active_heartbeat_optional_and_accepted(client):
    # Pre-fast-path clients omit it; new clients send it. Both valid.
    assert client.post("/state", json=wire(), headers=auth(TOK_A)).status_code == 204
    beat = wire(last_active="2026-07-08T22:00:00+00:00")
    assert client.post("/state", json=beat, headers=auth(TOK_A)).status_code == 204
    states = client.get("/group", headers=auth(TOK_B)).json()["per_person"][0]["states"]
    assert states[-1]["last_active"].startswith("2026-07-08T22:00")


def test_whoami_returns_token_identity(client):
    assert client.get("/whoami", headers=auth(TOK_A)).json() == {"person_id": "alice"}
    assert client.get("/whoami", headers=auth(TOK_B)).json() == {"person_id": "bob"}
    assert client.get("/whoami", headers=auth("guess")).status_code == 401


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
    # openness is deprecated-but-accepted during the transition (and never
    # stored); everything else beyond-tier is rejected outright.
    r = client.post("/state", json=wire(openness="neutral"), headers=auth(TOK_A))
    assert r.status_code == 204
    states = client.get("/group", headers=auth(TOK_B)).json()["per_person"][0]["states"]
    assert all("openness" not in s for s in states)
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
    )
    payload = to_wire(state)
    assert "momentum" not in payload and "stance" not in payload
    assert "trajectory" not in payload
    # Default (topic) tier: the full gist stays home; verbose rooms opt in.
    assert payload["topic_gist"] == ""
    assert to_wire(state, tier="verbose")["topic_gist"] == "synthetic status"


def test_wire_payload_is_accepted_by_relay(client):
    # The client's serializer and the relay's whitelist must stay in sync.
    state = PersonState(
        person_id="alice",
        updated_at=datetime(2026, 7, 8, 9, 0, tzinfo=timezone.utc),
        phase=Phase.DEBUGGING,
    )
    r = client.post("/state", json=to_wire(state), headers=auth(TOK_A))
    assert r.status_code == 204


def test_cap_tier_strips_above_board_tier(monkeypatch):
    # A capped board refuses to STORE above its tier, whatever a client
    # sends — the study-board guarantee (2026-08-04).
    monkeypatch.setenv("CAP_TIER", "topic")
    capped = TestClient(create_app(token_hashes=HASHES))
    auth = {"Authorization": f"Bearer {TOK_A}"}
    r = capped.post("/state", json=wire(topic_gist="a full verbose gist"),
                    headers=auth)
    assert r.status_code == 204  # stripped, not rejected
    stored = capped.get("/group", headers=auth).json()["per_person"][0]["states"][0]
    assert stored["topic_gist"] == ""
    assert stored["topic_micro"] == "synthesizing fixtures"  # topic survives

    monkeypatch.setenv("CAP_TIER", "presence")
    presence_board = TestClient(create_app(token_hashes=HASHES))
    r = presence_board.post("/state", json=wire(), headers=auth)
    assert r.status_code == 204
    stored = presence_board.get("/group", headers=auth).json()["per_person"][0]["states"][0]
    assert stored["topic_micro"] == "" and stored["topic_tags"] == []
