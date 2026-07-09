from presence.pipeline.projects import rewrite_allowlist


def test_rewrite_allowlist_replaces_in_place(tmp_path):
    env = tmp_path / ".env"
    env.write_text(
        "ANTHROPIC_API_KEY=sk-synthetic\n"
        "PRESENCE_ALLOWLIST=-old-prefix\n"
        "RELAY_URL=https://example.test\n"
    )
    rewrite_allowlist(env, ["-old-prefix", "-new-project"])
    lines = env.read_text().splitlines()
    assert "PRESENCE_ALLOWLIST=-old-prefix,-new-project" in lines
    assert lines[0] == "ANTHROPIC_API_KEY=sk-synthetic"  # untouched
    assert lines[2] == "RELAY_URL=https://example.test"
    assert sum(1 for l in lines if l.startswith("PRESENCE_ALLOWLIST=")) == 1


def test_rewrite_allowlist_appends_when_missing(tmp_path):
    env = tmp_path / ".env"
    env.write_text("ANTHROPIC_API_KEY=sk-synthetic\n")
    rewrite_allowlist(env, ["-only-project"])
    text = env.read_text()
    assert text.endswith("PRESENCE_ALLOWLIST=-only-project\n")
    assert text.startswith("ANTHROPIC_API_KEY=sk-synthetic\n")
