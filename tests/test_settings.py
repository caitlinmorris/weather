"""Settings GUI logic — the pure, testable halves."""

from presence.pipeline.config import update_env
from presence.render.settings_api import settings_to_env


def test_update_env_updates_removes_appends(tmp_path):
    env = tmp_path / ".env"
    env.write_text("# comment stays\nA=1\nB=2\nC=3\n")
    update_env({"B": "20", "C": None, "D": "4"}, env_path=env)
    text = env.read_text()
    assert "# comment stays" in text and "A=1" in text
    assert "B=20" in text and "C=" not in text and "D=4" in text
    assert oct(env.stat().st_mode)[-3:] == "600"


def test_settings_to_env_full_payload():
    payload = {
        "person_id": " matt ",
        "api_key": "",
        "sources": ["claude_code", "warp"],
        "claude_allowlist": ["-Users-m-proj"],
        "warp_allowlist": ["/Users/m/code"],
        "debug": True,
        "boards": [
            {"name": "studio", "url": "https://x.dev", "tier": "presence", "token": ""},
            {"name": "thesis", "url": "https://y.dev", "tier": "topic", "token": "tok9"},
        ],
    }
    updates = settings_to_env(payload, current_boards=[
        {"name": "studio", "token": "s-tok"}, {"name": "old", "token": "o-tok"},
    ])
    assert updates["PRESENCE_PERSON_ID"] == "matt"
    assert "ANTHROPIC_API_KEY" not in updates  # blank key = keep existing
    assert updates["PRESENCE_SOURCES"] == "claude_code,warp"
    assert updates["PRESENCE_DEBUG"] == "1"
    assert updates["PRESENCE_BOARDS"] == "studio,thesis"
    assert updates["PRESENCE_TIER_STUDIO"] == "presence"
    assert "RELAY_TOKEN_STUDIO" not in updates  # blank token = keep existing
    assert updates["RELAY_TOKEN_THESIS"] == "tok9"
    # Removed board 'old' gets its keys cleaned up:
    assert updates["RELAY_URL_OLD"] is None
    assert updates["RELAY_TOKEN_OLD"] is None
    assert updates["PRESENCE_TIER_OLD"] is None


def test_settings_to_env_key_only_when_typed():
    updates = settings_to_env(
        {"person_id": "m", "api_key": " sk-new ", "sources": [],
         "claude_allowlist": [], "warp_allowlist": [], "debug": False,
         "boards": []},
        current_boards=[],
    )
    assert updates["ANTHROPIC_API_KEY"] == "sk-new"
    assert updates["PRESENCE_DEBUG"] is None
    assert updates["PRESENCE_BOARDS"] is None


def test_settings_to_env_rename_carries_token():
    # Regression: renaming 'dan' -> 'family' with a blank token field must
    # move dan's token to the new key, not orphan the room (2026-07-21).
    payload = {
        "person_id": "c", "api_key": "", "sources": [],
        "claude_allowlist": [], "warp_allowlist": [], "debug": False,
        "boards": [{"name": "family", "url": "https://r.fly.dev",
                    "tier": "topic", "token": "", "original": "dan"}],
    }
    updates = settings_to_env(payload, current_boards=[
        {"name": "dan", "token": "dan-tok"},
    ])
    assert updates["RELAY_TOKEN_FAMILY"] == "dan-tok"
    assert updates["RELAY_TOKEN_DAN"] is None
    assert updates["PRESENCE_BOARDS"] == "family"


def test_invite_rejects_placeholder_names():
    import pytest
    from presence.relay.invite import invite

    with pytest.raises(RuntimeError, match="invalid name"):
        invite("anyboard", "<Friend>")


def test_env_lines_paste_ready():
    from presence.relay.invite import env_lines

    board = {"name": "art-club", "url": "https://x.workers.dev", "tier": "presence"}
    lines = env_lines(board, "tok123")
    assert "RELAY_URL_ART_CLUB=https://x.workers.dev" in lines
    assert "RELAY_TOKEN_ART_CLUB=tok123" in lines
    assert "PRESENCE_TIER_ART_CLUB=presence" in lines


def test_board_backend_none_for_foreign_hosts():
    from presence.relay.invite import board_backend

    assert board_backend({"name": "x", "url": "https://evil.example.com"}) is None
    assert board_backend({"name": "x", "url": None}) is None


def test_env_lines_first_time_user_no_placeholders():
    from presence.relay.invite import env_lines

    board = {"name": "dan", "url": "https://r.fly.dev", "tier": "topic"}
    lines = env_lines(board, "tok")
    assert "PRESENCE_BOARDS=dan" in lines
    assert "..." not in lines  # nothing for the invitee to hand-edit


def test_rename_host_files_moves_cf_board_files(tmp_path, monkeypatch):
    from presence.relay import invite

    monkeypatch.setattr(invite, "WORKER_DIR", tmp_path)
    (tmp_path / "wrangler.dan.toml").write_text("x")
    (tmp_path / "hashes.dan.json").write_text("{}")
    invite.rename_host_files("dan", "family")
    assert (tmp_path / "wrangler.family.toml").is_file()
    assert (tmp_path / "hashes.family.json").is_file()
    assert not (tmp_path / "wrangler.dan.toml").exists()


def test_settings_to_env_extractor_choice():
    base = {"person_id": "c", "api_key": "", "sources": [],
            "claude_allowlist": [], "warp_allowlist": [], "debug": False,
            "boards": []}
    cli = settings_to_env({**base, "extractor": "claude_cli"}, current_boards=[])
    assert cli["PRESENCE_EXTRACTOR"] == "claude_cli"
    api = settings_to_env({**base, "extractor": "api"}, current_boards=[])
    assert api["PRESENCE_EXTRACTOR"] is None  # default stays out of .env


def test_cli_envelope_parsing():
    import pytest
    from presence.extract.cli_client import parse_cli_envelope

    assert parse_cli_envelope('{"result": "{\\"phase\\": \\"building\\"}"}') \
        == '{"phase": "building"}'
    with pytest.raises(ValueError, match="error"):
        parse_cli_envelope('{"is_error": true, "result": "limit reached"}')
    with pytest.raises(ValueError, match="no text result"):
        parse_cli_envelope('{"cost_usd": 0.01}')


def test_wire_tiers_gist_only_on_verbose():
    # The docs promise: topic tier = micro + tags; the 15-word gist
    # crosses only on verbose rooms; presence carries no "what" at all.
    from datetime import datetime, timezone
    from presence.core.schema import PersonState
    from presence.pipeline.relay_client import to_wire

    state = PersonState(
        person_id="t", updated_at=datetime.now(timezone.utc),
        topic_gist="a fifteen word description of the work",
        topic_micro="short phrase", topic_tags=["a", "b"],
    )
    topic = to_wire(state, tier="topic")
    assert topic["topic_gist"] == "" and topic["topic_micro"] == "short phrase"
    assert topic["topic_tags"] == ["a", "b"]
    verbose = to_wire(state, tier="verbose")
    assert verbose["topic_gist"].startswith("a fifteen")
    presence = to_wire(state, tier="presence")
    assert presence["topic_micro"] == "" and presence["topic_tags"] == []


def test_epoch_clamp_consent_starts_the_clock():
    from datetime import datetime, timezone
    from presence.pipeline.extract_all import epoch_clamp

    t = lambda h: datetime(2026, 7, 27, h, 0, tzinfo=timezone.utc)
    # no epoch (pre-ruling installs): unchanged behavior
    assert epoch_clamp(None, t(10), None) == (False, None)
    # segment fully before install: skipped entirely
    assert epoch_clamp(None, t(10), t(12)) == (True, None)
    # segment straddling install: extraction floored at the epoch
    assert epoch_clamp(None, t(14), t(12)) == (False, t(12))
    # already-covered past the epoch: covered wins
    assert epoch_clamp(t(13), t(14), t(12)) == (False, t(13))


def test_published_phase_is_the_windows_own_not_the_days_mode():
    # Caitlin ruling 2026-09-14: a writing window on a building-heavy
    # day publishes as WRITING. The 4h-mode smoothing flattened it.
    from datetime import datetime, timedelta, timezone
    from presence.core.rollup import rollup_window
    from presence.core.schema import Phase, SessionObservation

    t0 = datetime(2026, 9, 14, 12, 0, tzinfo=timezone.utc)
    obs = [
        SessionObservation(person_id="t", t_start=t0 + timedelta(minutes=i * 10),
                           t_end=t0 + timedelta(minutes=i * 10 + 9),
                           phase=Phase.BUILDING)
        for i in range(6)
    ]
    obs.append(SessionObservation(person_id="t",
                                  t_start=t0 + timedelta(minutes=60),
                                  t_end=t0 + timedelta(minutes=70),
                                  phase=Phase.WRITING))
    assert rollup_window(obs).phase == Phase.WRITING
