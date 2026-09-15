"""Extraction never reads past the backfill window, stamp or no stamp.
Synthetic segments only."""

from datetime import datetime, timedelta, timezone

from presence.extract.extractor import ExtractionError
from presence.pipeline import extract_all
from presence.pipeline.config import BACKFILL_HOURS
from presence.pipeline.segmenter import Segment
from presence.pipeline.transcript_parser import TranscriptEvent

NOW = datetime(2026, 9, 14, 16, 0, tzinfo=timezone.utc)
EDGE = NOW - timedelta(hours=BACKFILL_HOURS)


def _ago(hours: float) -> datetime:
    return NOW - timedelta(hours=hours)


def _segment(name: str, start_h: float, end_h: float) -> Segment:
    """One synthetic human prompt every 10 minutes from start_h to end_h ago."""
    events, t = [], _ago(start_h)
    while t <= _ago(end_h):
        events.append(TranscriptEvent(type="user", timestamp=t, role="user",
                                      text=f"synthetic {name}"))
        t += timedelta(minutes=10)
    return Segment(session_id=name, project_cwd="/synthetic",
                   t_start=_ago(start_h), t_end=_ago(end_h), events=events)


class RecordingExtractor:
    """Notes the event window extract_all hands over, then raises so the
    pass counts it as failed and stores nothing."""

    def __init__(self):
        self.windows: dict[str, int] = {}

    def extract_segment(self, seg, person_id, previous=None, events=None):
        self.windows[seg.session_id] = len(seg.events if events is None else events)
        raise ExtractionError("recording only")


def test_backfill_epoch_is_the_later_of_stamp_and_window():
    epoch = extract_all.backfill_epoch
    assert epoch(None, NOW) == EDGE            # no stamp: window alone
    assert epoch(_ago(24 * 30), NOW) == EDGE   # old stamp: window wins
    assert epoch(_ago(1), NOW) == _ago(1)      # fresh stamp: stamp wins


def test_run_skips_old_segments_and_clamps_straddlers(tmp_path, monkeypatch):
    old = _segment("old", 30, 28)           # ended long before the window
    straddle = _segment("straddle", 6, 2)   # 25 events; 12 fall after the edge
    fresh = _segment("fresh", 1, 0.5)       # fully inside
    fake = RecordingExtractor()

    monkeypatch.setattr(extract_all, "PRIVATE_DB", tmp_path / "private.db")
    monkeypatch.setattr(extract_all, "PUBLIC_DB", tmp_path / "public.db")
    monkeypatch.setattr(extract_all, "load_api_key", lambda: "synthetic-key")
    monkeypatch.setattr(extract_all, "install_epoch", lambda: None)
    monkeypatch.setattr(extract_all, "Extractor", lambda: fake)
    monkeypatch.setattr(extract_all, "gather_segments",
                        lambda min_minutes: [("p1", s) for s in (old, straddle, fresh)])

    counts = extract_all.run(min_minutes=5, verbose=False, now=NOW)

    assert counts == {"extracted": 0, "skipped": 1, "failed": 2}
    assert fake.windows == {"straddle": 12, "fresh": len(fresh.events)}
