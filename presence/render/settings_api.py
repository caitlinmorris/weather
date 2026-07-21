"""Settings bridge for the pywebview app: the GUI half of consent and
configuration. The consent rules hold here exactly as in the installer —
the allowlist is chosen by the human through explicit selection, and
tokens/keys are write-only from the GUI (shown masked, replaced only when
a new value is typed).

Saving writes .env then relaunches the app (execv keeps the PID, so the
single-instance guard stays truthful) — the read-settings-at-launch
footgun finally closes for config changes."""

from __future__ import annotations

from pathlib import Path

from presence.pipeline import config

WIZARD_REQUIRED = ("ANTHROPIC_API_KEY", "PRESENCE_PERSON_ID")


def settings_snapshot() -> dict:
    """Current settings for the GUI — secrets reported as presence only."""
    from presence.relay.invite import board_backend

    boards = []
    for b in config.boards():
        boards.append({
            "name": b["name"],
            "url": b["url"],
            "tier": b["tier"],
            "has_token": bool(b["token"]),
            # non-None means this machine can mint invites for the room
            "hosted_backend": board_backend(b),
        })
    return {
        "person_id": config.env_value("PRESENCE_PERSON_ID") or "",
        "has_api_key": bool(config.env_value("ANTHROPIC_API_KEY")),
        "sources": [s.strip() for s in
                    (config.env_value("PRESENCE_SOURCES") or "claude_code").split(",")
                    if s.strip()],
        "claude_allowlist": list(config.ALLOWED_PROJECT_PREFIXES),
        "claude_projects": sorted(
            p.name for p in config.PROJECTS_ROOT.iterdir() if p.is_dir()
        ) if config.PROJECTS_ROOT.is_dir() else [],
        "warp_allowlist": [p.strip() for p in
                           (config.env_value("PRESENCE_ALLOWLIST_WARP") or "").split(",")
                           if p.strip()],
        "debug": config.env_value("PRESENCE_DEBUG") == "1",
        "boards": boards,
    }


def settings_to_env(payload: dict, current_board_names: list[str]) -> dict:
    """Translate the GUI payload into .env updates. Pure and testable.
    Board removal cleans up that board's keys; tokens/keys only change
    when a non-empty new value arrives."""
    updates: dict = {
        "PRESENCE_PERSON_ID": (payload.get("person_id") or "").strip() or None,
        "PRESENCE_SOURCES": ",".join(payload.get("sources") or ["claude_code"]),
        "PRESENCE_ALLOWLIST": ",".join(payload.get("claude_allowlist") or []),
        "PRESENCE_ALLOWLIST_WARP": ",".join(payload.get("warp_allowlist") or []),
        "PRESENCE_DEBUG": "1" if payload.get("debug") else None,
    }
    if (payload.get("api_key") or "").strip():
        updates["ANTHROPIC_API_KEY"] = payload["api_key"].strip()

    boards = payload.get("boards") or []
    names = [b["name"].strip() for b in boards if b.get("name", "").strip()]
    updates["PRESENCE_BOARDS"] = ",".join(names) if names else None
    for b in boards:
        name = b.get("name", "").strip()
        if not name:
            continue
        key = name.upper().replace("-", "_")
        updates[f"RELAY_URL_{key}"] = (b.get("url") or "").strip() or None
        updates[f"PRESENCE_TIER_{key}"] = b.get("tier") or "topic"
        if (b.get("token") or "").strip():
            updates[f"RELAY_TOKEN_{key}"] = b["token"].strip()
    for gone in set(current_board_names) - set(names):
        key = gone.upper().replace("-", "_")
        updates[f"RELAY_URL_{key}"] = None
        updates[f"RELAY_TOKEN_{key}"] = None
        updates[f"PRESENCE_TIER_{key}"] = None
    return updates


class SettingsApi:
    """Exposed to the settings page as window.pywebview.api."""

    def __init__(self):
        self.restart_requested = False
        self._settings_window = None

    # -- called from JS ---------------------------------------------------------

    def get_settings(self) -> dict:
        return settings_snapshot()

    def choose_warp_folder(self) -> str | None:
        import webview

        active = webview.active_window()
        if active is None:
            return None
        picked = active.create_file_dialog(webview.FOLDER_DIALOG)
        return picked[0] if picked else None

    def invite_member(self, board_name: str, person: str) -> dict:
        """Mint + register a token for a new member of a board this
        machine hosts. The token goes back to the page once, for the
        host to send privately — it is never stored."""
        from presence.relay.invite import invite

        try:
            result = invite(board_name, person)
        except RuntimeError as e:
            return {"ok": False, "error": str(e)}
        except Exception as e:  # subprocess/timeout surprises, readable-ish
            return {"ok": False, "error": f"{type(e).__name__}: {e}"}
        return {"ok": True, "message": result["message"]}

    def save_settings(self, payload: dict) -> dict:
        current = [b["name"] for b in config.boards()]
        updates = settings_to_env(payload, current)
        config.update_env(updates)
        return {"ok": True}

    def save_and_restart(self, payload: dict) -> dict:
        result = self.save_settings(payload)
        self.restart_requested = True
        import webview

        for w in list(webview.windows):
            w.destroy()
        return result

    def open_settings(self) -> None:
        import webview

        if self._settings_window is not None:
            return
        page = Path(__file__).parent / "settings.html"
        self._settings_window = webview.create_window(
            "we.ather settings", url=page.as_uri(), js_api=self,
            width=540, height=680, on_top=True,
        )

        def cleared():
            self._settings_window = None

        self._settings_window.events.closed += cleared
