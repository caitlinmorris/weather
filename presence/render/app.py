"""The sticky desktop widget: ambient.html#live in a small always-on-top
native window, with the watch loop running alongside in a background thread.

One command gives the full live experience:

    python -m presence.render.app

Close the window (or Ctrl-C the terminal) to stop everything. Pausing capture
is the same as quitting — the display just decays to quiet, which is the
correct rendering of absence.
"""

from __future__ import annotations

import threading

import webview

from presence.pipeline import watch
from presence.render.build_page import OUT, build


def bootstrap_page() -> None:
    """First run: build a page before opening the window. Extraction of
    existing history may take a few minutes; if it fails (no key, no
    transcripts yet), open with an honest empty field — the watch loop
    fills it in as work happens."""
    print("first run: building your page (extracting existing history — "
          "this can take a few minutes)…")
    from presence.pipeline import extract_all
    from presence.pipeline.config import PUBLIC_DB
    from presence.pipeline.store import PublicStore

    try:
        extract_all.run(verbose=True)
    except Exception as e:
        print(f"initial extraction skipped ({e}); starting with an empty field")
    store = PublicStore(PUBLIC_DB)
    build(store, allow_empty=True)
    store.close()


def main() -> None:
    # Quiet consent hygiene at launch: mention unreviewed project folders in
    # the terminal only — never auto-include, never ask from the widget.
    from presence.pipeline.projects import unreviewed

    new_dirs = unreviewed()
    if new_dirs:
        print(f"{len(new_dirs)} project folder(s) not in your allowlist — "
              "review with: python -m presence.pipeline.projects")

    if not OUT.exists():
        bootstrap_page()

    worker = threading.Thread(target=watch.main, daemon=True)
    worker.start()

    webview.create_window(
        "we.ather",
        url=OUT.as_uri() + "#live",
        width=432,
        height=248,
        on_top=True,
        resizable=True,
    )
    webview.start()


if __name__ == "__main__":
    main()
