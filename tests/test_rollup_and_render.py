import json
from datetime import datetime, timedelta, timezone

from presence.core import rollup
from presence.core.schema import (
    Momentum,
    Openness,
    Phase,
    SessionObservation,
    Stance,
    Tier,
    Topic,
)
from presence.pipeline.store import PrivateStore, PublicStore
from presence.render.build_page import build

T = datetime(2026, 7, 1, 9, 0, tzinfo=timezone.utc)


def _obs(minute, phase=Phase.BUILDING, momentum=Momentum.GRINDING):
    return SessionObservation(
        person_id="p1",
        t_start=T + timedelta(minutes=minute),
        t_end=T + timedelta(minutes=minute + 30),
        topic=Topic(
            tags=["synthetic"],
            gist="synthetic status line",
            micro_gist="synthesizing fixtures",
            domain="testing",
        ),
        phase=phase,
        momentum=momentum,
        stance=Stance.LEARNING,
        openness=Openness.NEUTRAL,
    )


def test_ambient_tier_strips_momentum_and_stance():
    state = rollup.rollup_window([_obs(0)], publish_tier=Tier.T2_AMBIENT)
    # The sensitive T1 fields must not survive per-person publication.
    assert state.momentum == Momentum.UNKNOWN
    assert state.stance == Stance.UNKNOWN
    # T2 fields do survive.
    assert state.topic_gist == "synthetic status line"
    assert state.topic_micro == "synthesizing fixtures"
    assert state.phase == Phase.BUILDING
    assert state.openness == Openness.NEUTRAL


def test_recency_weighted_mode_prefers_recent_and_known():
    obs = [
        _obs(0, phase=Phase.EXPLORING),
        _obs(60, phase=Phase.BUILDING),
        _obs(120, phase=Phase.BUILDING),
        _obs(180, phase=Phase.UNKNOWN),  # unknown never beats a known value
    ]
    assert rollup.rollup_window(obs).phase == Phase.BUILDING


def test_publish_history_writes_one_state_per_observation(tmp_path):
    private = PrivateStore(tmp_path / "private.db")
    for m in (0, 60, 600):
        private.add(_obs(m))
    public = rollup.open_public_writer(tmp_path / "public.db")
    assert rollup.publish_history(private, public, "p1") == 3
    history = public.history("p1")
    assert len(history) == 3
    assert all(s.momentum == Momentum.UNKNOWN for s in history)
    private.close(), public.close()


def test_built_page_contains_only_published_fields(tmp_path):
    private = PrivateStore(tmp_path / "private.db")
    private.add(_obs(0))
    public = rollup.open_public_writer(tmp_path / "public.db")
    rollup.publish_history(private, public, "p1")

    out = build(public, out=tmp_path / "ambient.html")
    html = out.read_text()
    assert "synthetic status line" in html  # T2 gist is rendered
    assert "synthesizing fixtures" in html  # T2 micro-gist is rendered
    assert "grinding" not in html  # T1 momentum never reaches the page
    assert "learning" not in json.dumps(html.split("const DATA = ")[1][:2000])
    private.close(), public.close()
