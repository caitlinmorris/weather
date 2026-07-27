"""The sticky desktop widget: ambient.html#live in a small always-on-top
native window, with the watch loop running alongside in a background thread.

One command gives the full live experience:

    python -m presence.render.app

Close the window (or Ctrl-C the terminal) to stop everything. Pausing capture
is the same as quitting — the display just decays to quiet, which is the
correct rendering of absence.
"""

from __future__ import annotations

import atexit
import os
import threading

import webview

from presence.pipeline import watch
from presence.pipeline.config import DATA_DIR
from presence.render.build_page import OUT, build

PID_FILE = DATA_DIR / "app.pid"


def another_instance_running() -> bool:
    """Two apps = two watch loops = duplicate extraction. One is plenty."""
    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, 0)  # signal 0: existence check only
        return True
    except (FileNotFoundError, ValueError, ProcessLookupError, PermissionError):
        return False


def claim_instance() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()))
    atexit.register(lambda: PID_FILE.unlink(missing_ok=True))


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
    if another_instance_running():
        print("we.ather is already running — not starting a second instance."
              f" (If that's wrong, delete {PID_FILE} and relaunch.)")
        return
    claim_instance()

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

    from presence.pipeline.config import boards
    from presence.render.settings_api import SettingsApi, wizard_needed

    api = SettingsApi()
    room_count = max(1, len(boards()))
    webview.create_window(
        "we.ather",
        url=OUT.as_uri() + "#live",
        js_api=api,
        width=432,
        # stacked strips need vertical room: ~94px per additional board
        height=248 + 94 * (room_count - 1),
        on_top=True,
        resizable=True,
    )
    if wizard_needed():
        # First-run wizard: settings opens alongside the (empty) widget.
        webview.start(api.open_settings)
    else:
        webview.start()

    if api.restart_requested:
        # execv keeps the PID, so the single-instance pidfile stays true —
        # and settings changes apply themselves (the launch-time-config
        # footgun, finally closed for the GUI path).
        import sys

        PID_FILE.unlink(missing_ok=True)
        os.execv(sys.executable, [sys.executable, "-m", "presence.render.app"])


if __name__ == "__main__":
    main()
