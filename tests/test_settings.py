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
    updates = settings_to_env(payload, current_board_names=["studio", "old"])
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
        current_board_names=[],
    )
    assert updates["ANTHROPIC_API_KEY"] == "sk-new"
    assert updates["PRESENCE_DEBUG"] is None
    assert updates["PRESENCE_BOARDS"] is None
