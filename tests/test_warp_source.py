"""Warp source against a synthetic warp.sqlite (schema per docs/warp-schema.txt).
All content here is invented."""

import sqlite3
from datetime import timezone

from presence.pipeline.sources.warp import WarpSource

ALLOWED = "/home/lara/maps"
PRIVATE = "/home/lara/private"


def make_db(path):
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE ai_queries (id INTEGER PRIMARY KEY, exchange_id TEXT,"
        " conversation_id TEXT, start_ts DATETIME, input TEXT,"
        " working_directory TEXT, output_status TEXT, model_id TEXT)")
    conn.execute(
        "CREATE TABLE commands (id INTEGER PRIMARY KEY, command TEXT,"
        " exit_code INTEGER, start_ts DATETIME, pwd TEXT,"
        " is_agent_executed BOOLEAN)")
    rows = [
        ("2026-07-15 09:00:00.100000", "fix the overlay layering", ALLOWED),
        ("2026-07-15 09:20:00.000000", "why is the legend clipped", ALLOWED),
        # after a >30 min gap: second work burst
        ("2026-07-15 10:10:00.000000", "add zoom controls", ALLOWED),
        # never ingested: outside the allowlist
        ("2026-07-15 09:05:00.000000", "SECRET private prompt", PRIVATE),
    ]
    for ts, text, wd in rows:
        conn.execute("INSERT INTO ai_queries (start_ts, input,"
                     " working_directory) VALUES (?,?,?)", (ts, text, wd))
    for ts, code, pwd in [
        ("2026-07-15 09:05:00", 1, ALLOWED),
        ("2026-07-15 09:06:00", 0, ALLOWED),
        ("2026-07-15 09:07:00", 2, PRIVATE),  # excluded
        ("2026-07-15 10:18:00", 0, ALLOWED),  # gives burst 2 real duration
    ]:
        conn.execute("INSERT INTO commands (start_ts, exit_code, pwd)"
                     " VALUES (?,?,?)", (ts, code, pwd))
    conn.commit()
    conn.close()


def _source(tmp_path):
    db = tmp_path / "warp.sqlite"
    make_db(db)
    return WarpSource(db_path=db, allow_prefixes=[ALLOWED])


def test_allowlist_filters_in_sql(tmp_path):
    events = _source(tmp_path).events()
    assert all("SECRET" not in e.text for e in events)
    assert all((e.cwd or "").startswith(ALLOWED) for e in events)


def test_events_shape_and_order(tmp_path):
    events = _source(tmp_path).events()
    assert [e.timestamp for e in events] == sorted(e.timestamp for e in events)
    prompts = [e for e in events if e.is_human_prompt]
    assert len(prompts) == 3
    assert prompts[0].timestamp.tzinfo == timezone.utc
    # commands: failed one carries exit in stderr; success carries nothing;
    # command TEXT never appears anywhere.
    results = [e.tool_result for e in events if e.tool_result]
    assert [r.stderr for r in results] == ["exit 1", "", ""]


def test_segments_split_and_origin(tmp_path, monkeypatch):
    from presence.pipeline import config
    monkeypatch.setattr(config, "GROUP_MODE", "person")
    monkeypatch.setattr(config, "PERSON_ID", "lara")
    pairs = _source(tmp_path).segments(min_minutes=5)
    assert len(pairs) == 2  # 30-min gap splits the morning
    assert all(person == "lara" for person, _ in pairs)
    assert all(seg.origin == "warp" for _, seg in pairs)


def test_last_activity_within_allowlist(tmp_path):
    beat = _source(tmp_path).last_activity()
    assert beat.strftime("%H:%M") == "10:18"  # private rows don't count


def test_unavailable_without_allowlist(tmp_path):
    db = tmp_path / "warp.sqlite"
    make_db(db)
    assert not WarpSource(db_path=db, allow_prefixes=[]).available()


def test_extractor_records_warp_source(tmp_path):
    from presence.core.schema import Source
    from presence.extract.extractor import Extractor
    from tests.test_extractor_harness import VALID_RESPONSE, FakeClient

    person, seg = _source(tmp_path).segments(min_minutes=5)[0]
    obs = Extractor(client=FakeClient([VALID_RESPONSE])).extract_segment(
        seg, person_id=person)
    assert obs.source == Source.WARP
