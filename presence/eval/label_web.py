"""Web labeling UI — same flow and files as label_tool, easier on the eyes.

Serves a minimalist chat-style viewer on localhost only; labels append to
the same gitignored labels.jsonl, so run_eval and the terminal tool remain
interchangeable with this.

Usage: python -m presence.eval.label_web   (opens your browser)
"""

from __future__ import annotations

import threading
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

import uvicorn
from fastapi import Body, FastAPI
from fastapi.responses import HTMLResponse

from presence.eval.label_tool import (
    FIELDS,
    LABELS_FILE,
    SAMPLE_FILE,
    _append_jsonl,
    _load_jsonl,
)
from presence.pipeline.sample_extract import find_segment

PORT = 8377
PAGE = Path(__file__).parent / "label_web.html"

app = FastAPI(title="we.ather labeling", docs_url=None, redoc_url=None)


def _messages(events) -> list[dict]:
    """Chat-shaped view: human prompts, human-facing assistant text, and
    churn collapsed to step counts (cadence evidence, not noise)."""
    msgs: list[dict] = []
    omitted = 0

    def flush() -> None:
        nonlocal omitted
        if omitted:
            msgs.append({"kind": "steps", "n": omitted})
            omitted = 0

    for e in events:
        stamp = e.timestamp.strftime("%H:%M") if e.timestamp else "--:--"
        if e.is_human_prompt:
            flush()
            msgs.append({"kind": "you", "t": stamp, "text": e.text[:4000]})
        elif (e.type == "assistant" and e.text
              and (len(e.text) >= 200 or "?" in e.text[-300:])):
            flush()
            msgs.append({"kind": "assistant", "t": stamp, "text": e.text[:3000]})
        elif not e.is_meta and not e.is_sidechain and e.type in ("user", "assistant"):
            omitted += 1
    flush()
    return msgs


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return PAGE.read_text()


@app.get("/api/next")
def next_item() -> dict:
    samples = _load_jsonl(SAMPLE_FILE)
    labeled = {r["observation_id"] for r in _load_jsonl(LABELS_FILE)}
    todo = [s for s in samples if s["observation_id"] not in labeled]
    done = len(samples) - len(todo)

    while todo:
        obs = todo[0]
        seg = find_segment(obs["person_id"], obs["t_start"], obs["t_end"])
        if seg is None:
            _append_jsonl(LABELS_FILE, {
                "observation_id": obs["observation_id"], "skipped": True,
            })
            todo.pop(0)
            done += 1
            continue
        return {
            "done": done,
            "total": len(samples),
            "obs": {
                "observation_id": obs["observation_id"],
                "span": f"{obs['t_start'][:16]} → {obs['t_end'][:16]}",
                "extractor": {f: obs[f] for f in FIELDS},
                "confidence": obs.get("confidence", {}),
                "gist": obs["topic"]["gist"],
            },
            "enums": {
                f: [v.value for v in enum if v.value != "unknown"]
                for f, enum in FIELDS.items()
            },
            "messages": _messages(seg.events),
        }
    return {"done": done, "total": len(samples), "obs": None}


@app.post("/api/label")
def save_label(row: dict = Body(...)) -> dict:
    required = {"observation_id", "labels", "extractor", "gist"}
    if not required <= set(row):
        return {"ok": False, "error": f"missing {required - set(row)}"}
    row["labeled_at"] = datetime.now(timezone.utc).isoformat()
    row["via"] = "web"
    _append_jsonl(LABELS_FILE, row)
    return {"ok": True}


def main() -> None:
    url = f"http://127.0.0.1:{PORT}"
    print(f"we.ather labeling at {url} · Ctrl-C to stop")
    threading.Timer(0.8, webbrowser.open, args=(url,)).start()
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")


if __name__ == "__main__":
    main()
