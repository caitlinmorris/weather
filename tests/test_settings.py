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
