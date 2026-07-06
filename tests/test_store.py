from datetime import datetime, timedelta, timezone

import pytest

from presence.core.schema import (
    Momentum,
    PersonState,
    Phase,
    PresenceLevel,
    SessionObservation,
    Topic,
)
from presence.pipeline.store import PrivateStore, PublicStore

T = datetime(2026, 7, 1, 9, 0, tzinfo=timezone.utc)


def _obs(minute: int) -> SessionObservation:
    return SessionObservation(
        person_id="p1",
        t_start=T + timedelta(minutes=minute),
        t_end=T + timedelta(minutes=minute + 30),
        topic=Topic(tags=["synthetic"], gist="synthetic work", domain="testing"),
        phase=Phase.BUILDING,
        momentum=Momentum.STEADY,
    )


def test_private_store_roundtrip(tmp_path):
    store = PrivateStore(tmp_path / "private.db")
    first, second = _obs(0), _obs(60)
    store.add(first)
    store.add(second)
    assert store.latest("p1").observation_id == second.observation_id
    assert len(store.window("p1", T)) == 2
    assert store.latest("p1").topic.gist == "synthetic work"
    store.close()


def test_public_store_requires_writer_flag(tmp_path):
    reader = PublicStore(tmp_path / "public.db")
    state = PersonState(person_id="p1", updated_at=T, presence=PresenceLevel.ACTIVE)
    with pytest.raises(PermissionError):
        reader.publish(state)
    reader.close()


def test_public_store_roundtrip_and_history(tmp_path):
    path = tmp_path / "public.db"
    writer = PublicStore(path, writer=True)
    for minute in (0, 60):
        writer.publish(
            PersonState(
                person_id="p1",
                updated_at=T + timedelta(minutes=minute),
                presence=PresenceLevel.ACTIVE,
                topic_gist="synthetic gist",
            )
        )
    writer.close()

    reader = PublicStore(path)
    assert reader.latest("p1").updated_at == T + timedelta(minutes=60)
    assert len(reader.history("p1")) == 2
    assert [s.person_id for s in reader.all_latest()] == ["p1"]
    reader.close()
