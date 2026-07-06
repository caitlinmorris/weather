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
from presence.render.build_page import OUT


def main() -> None:
    if not OUT.exists():
        raise SystemExit("no ambient.html yet — run extract_all + build_page once first")

    worker = threading.Thread(target=watch.main, daemon=True)
    worker.start()

    webview.create_window(
        "presence",
        url=OUT.as_uri() + "#live",
        width=432,
        height=248,
        on_top=True,
        resizable=True,
    )
    webview.start()


if __name__ == "__main__":
    main()
