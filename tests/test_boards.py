import importlib
import json
import time
from pathlib import Path

from presence.core.schema import Momentum, PersonState, Phase
from presence.pipeline.relay_client import to_wire
from datetime import datetime, timezone

T = datetime(2026, 7, 15, 9, 0, tzinfo=timezone.utc)


def _reload_config(monkeypatch, **env):
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    import presence.pipeline.config as config
    config = importlib.reload(config)
    # Hermetic: unstubbed keys must not fall through to the repo's real
    # .env (this leaked once — a tier default assertion passed only
    # because the dev machine's .env happened to agree).
    monkeypatch.setattr(config, "REPO_ROOT", Path("/nonexistent-hermetic"))
    return config


def test_boards_multi(monkeypatch):
    config = _reload_config(
        monkeypatch,
        PRESENCE_BOARDS="dan, lara",
        RELAY_URL_DAN="https://a.example", RELAY_TOKEN_DAN="t1",
        RELAY_URL_LARA="https://b.example", RELAY_TOKEN_LARA="t2",
        PRESENCE_TIER_LARA="presence",
    )
    bs = config.boards()
    assert [b["name"] for b in bs] == ["dan", "lara"]
    assert bs[0]["tier"] == "topic"      # default
    assert bs[1]["tier"] == "presence"   # explicit
    # Board missing url/token is dropped, not half-configured.
    config2 = _reload_config(monkeypatch, PRESENCE_BOARDS="dan,ghost")
    assert [b["name"] for b in config2.boards()] == ["dan"]


def test_boards_legacy_fallback(monkeypatch, tmp_path):
    monkeypatch.delenv("PRESENCE_BOARDS", raising=False)
    config = _reload_config(
        monkeypatch, RELAY_URL="https://x.example", RELAY_TOKEN="tok"
    )
    # Hermetic: don't let the repo's real .env leak into the fallback path.
    monkeypatch.setattr(config, "REPO_ROOT", tmp_path)
    bs = config.boards()
    assert len(bs) == 1 and bs[0]["name"] == "board" and bs[0]["tier"] == "topic"


def test_presence_tier_strips_all_what():
    state = PersonState(
        person_id="p", updated_at=T, topic_gist="secret gist",
        topic_micro="doing things", topic_tags=["x"],
        phase=Phase.DEBUGGING, momentum=Momentum.GRINDING,
    )
    wire = to_wire(state, tier="presence")
    assert wire["topic_gist"] == "" and wire["topic_micro"] == ""
    assert wire["topic_tags"] == [] and wire["phase"] == "unknown"
    assert wire["last_active"] is None and "momentum" not in wire
    assert "openness" not in wire  # killed in v1.0
    # topic tier keeps the micro-what; the full gist is verbose-only
    assert to_wire(state, tier="topic")["topic_micro"] == "doing things"
    assert to_wire(state, tier="topic")["topic_gist"] == ""
    assert to_wire(state, tier="verbose")["topic_gist"] == "secret gist"


def test_composite_merge_tags_boards_and_dedups(tmp_path, monkeypatch):
    from presence.render import build_page
    monkeypatch.setattr(
        "presence.render.build_page.config",
        type("C", (), {"DATA_DIR": tmp_path, "PERSON_ID": "caitlin"}),
    )
    shared = {"updated_at": "2026-07-15T09:00:00+00:00", "topic_gist": "g",
              "phase": "building"}
    (tmp_path / "group_cache_dan.json").write_text(json.dumps(
        {"per_person": [{"person_id": "caitlin", "states": [shared]},
                        {"person_id": "dan", "states": [dict(shared)]}]}))
    (tmp_path / "group_cache_lara.json").write_text(json.dumps(
        {"per_person": [{"person_id": "caitlin", "states": [dict(shared)]},
                        {"person_id": "lara", "states": [dict(shared)]}]}))
    data, boards = build_page.group_cache_data()
    assert [b["key"] for b in boards] == ["dan", "lara"]
    # Rooms are labeled by their OTHER members, never the config key.
    labels = {b["key"]: b["label"] for b in boards}
    assert labels["dan"] == "with dan" and labels["lara"] == "with lara"
    people = {p["person"]: p for p in data}
    assert set(people) == {"caitlin", "dan", "lara"}
    # Self keeps a copy PER BOARD (stacked strips show each room whole);
    # fused view overlaps the duplicates pixel-identically.
    assert len(people["caitlin"]["states"]) == 2
    assert {s["board"] for s in people["caitlin"]["states"]} == {"dan", "lara"}
    assert people["dan"]["states"][0]["board"] == "dan"
    assert people["lara"]["states"][0]["board"] == "lara"
