"""Invite a person to a board you host: mint their token, merge its hash
into the board's RELAY_TOKENS secret, and hand back exactly what to send
them privately. One mechanism, two entries — the settings GUI button and:

    python -m presence.relay.invite <board> <person>

Works for boards on either backend. Detection is by relay URL:
  *.workers.dev  -> Cloudflare (hashes merge via the local
                    worker/hashes.<board>.json file; CF secrets are
                    write-only, so that file is the source of truth)
  *.fly.dev      -> Fly (current hashes are read back live from the
                    machine's env via `fly ssh console`, so no local
                    file is needed and pre-invite boards work too)

The token appears once, for the host to send out-of-band; only its hash
touches disk or the relay. Inviting mints a credential — the person is
not on the board until they receive the token, configure, and restart.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

from presence.pipeline import config
from presence.relay.mktoken import VALID_PERSON

WORKER_DIR = Path(__file__).parent / "worker"
# GUI-launched apps (Dock) get a minimal PATH; brew lives here on most Macs.
_EXTRA_PATHS = ["/opt/homebrew/bin", "/usr/local/bin"]


def _find_exe(name: str) -> str | None:
    found = shutil.which(name)
    if found:
        return found
    for base in _EXTRA_PATHS:
        candidate = Path(base) / name
        if candidate.is_file():
            return str(candidate)
    return None


def board_backend(board: dict) -> str | None:
    """'cloudflare' / 'fly' if this machine can plausibly host-manage the
    board, else None (a room someone else hosts)."""
    host = urlparse(board["url"] or "").hostname or ""
    if host.endswith(".workers.dev"):
        cfg = WORKER_DIR / f"wrangler.{board['name']}.toml"
        return "cloudflare" if cfg.is_file() and _find_exe("npx") else None
    if host.endswith(".fly.dev"):
        return "fly" if _find_exe("fly") else None
    return None


def _run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=120,
                          cwd=config.REPO_ROOT, **kw)


def _current_hashes(board: dict, backend: str) -> dict:
    if backend == "cloudflare":
        path = WORKER_DIR / f"hashes.{board['name']}.json"
        if not path.is_file():
            raise RuntimeError(
                f"no {path.name} found — this board predates hash files. "
                "Recreate it with one \"person\": \"hash\" entry per member "
                "(hashes only, never tokens), then retry.")
        return json.loads(path.read_text())
    app = urlparse(board["url"]).hostname.removesuffix(".fly.dev")
    proc = _run([_find_exe("fly"), "ssh", "console", "-a", app, "-C",
                 "printenv RELAY_TOKENS"])
    if proc.returncode != 0:
        raise RuntimeError(
            f"couldn't read the board's member list from Fly ({app}): "
            f"{proc.stderr.strip() or proc.stdout.strip()}")
    return json.loads(proc.stdout.strip())


def _push_hashes(board: dict, backend: str, hashes: dict) -> None:
    payload = json.dumps(hashes)
    if backend == "cloudflare":
        cfg = WORKER_DIR / f"wrangler.{board['name']}.toml"
        proc = _run([_find_exe("npx"), "wrangler@latest", "secret", "put",
                     "RELAY_TOKENS", "--config", str(cfg)], input=payload)
        if proc.returncode != 0:
            raise RuntimeError(f"wrangler secret put failed: "
                               f"{proc.stderr.strip() or proc.stdout.strip()}")
        path = WORKER_DIR / f"hashes.{board['name']}.json"
        path.write_text(payload)
        path.chmod(0o600)
        return
    app = urlparse(board["url"]).hostname.removesuffix(".fly.dev")
    proc = _run([_find_exe("fly"), "secrets", "set", "-a", app,
                 f"RELAY_TOKENS={payload}"])
    if proc.returncode != 0:
        raise RuntimeError(f"fly secrets set failed: "
                           f"{proc.stderr.strip() or proc.stdout.strip()}")


def env_lines(board: dict, token: str) -> str:
    """The .env block the invitee appends — paste-ready for a first-time
    user (one board, no placeholders to edit)."""
    key = board["name"].upper().replace("-", "_")
    return "\n".join([
        f"PRESENCE_BOARDS={board['name']}",
        f"RELAY_URL_{key}={board['url']}",
        f"RELAY_TOKEN_{key}={token}",
        f"PRESENCE_TIER_{key}={board['tier']}",
    ])


def rename_host_files(old: str, new: str) -> None:
    """Keep host-side per-board files in step with a board rename, so the
    invite button still recognizes a renamed CF board as ours."""
    for pattern in ("wrangler.{}.toml", "hashes.{}.json"):
        src = WORKER_DIR / pattern.format(old)
        dst = WORKER_DIR / pattern.format(new)
        if src.is_file() and not dst.exists():
            src.rename(dst)


def invite(board_name: str, person: str) -> dict:
    """Mint + register a token for `person` on `board_name`. Returns the
    one-time message for the host to send. Raises RuntimeError with a
    human-readable reason on any failure."""
    person = person.strip().lower()
    if not VALID_PERSON.match(person):
        raise RuntimeError(
            f"invalid name {person!r}: lowercase letters, digits, dash, "
            "underscore — and it must EXACTLY match the PRESENCE_PERSON_ID "
            "they will install with.")
    board = next((b for b in config.boards() if b["name"] == board_name), None)
    if board is None:
        raise RuntimeError(f"no board named {board_name!r} in your .env")
    backend = board_backend(board)
    if backend is None:
        raise RuntimeError(
            f"'{board_name}' isn't hosted from this machine — ask that "
            "room's host to run the invite.")

    hashes = _current_hashes(board, backend)
    if person in hashes:
        raise RuntimeError(
            f"'{person}' is already a member of '{board_name}'. Re-inviting "
            "would revoke their current token; remove them first if that's "
            "really what you want.")

    token = secrets.token_urlsafe(32)
    hashes[person] = hashlib.sha256(token.encode()).hexdigest()
    _push_hashes(board, backend, hashes)

    return {
        "person": person,
        "board": board_name,
        "token": token,
        "message": (
            f"You're invited to the '{board_name}' we.ather room.\n"
            f"After installing (README), add to your .env:\n\n"
            f"{env_lines(board, token)}\n\n"
            f"Then restart the app and run:\n"
            f"  .venv/bin/python -m presence.pipeline.selftest\n\n"
            f"(Already using we.ather? Easiest is the app: settings gear "
            f"→ add a room → paste the name, URL and token above. "
            f"Or by hand: keep your existing PRESENCE_BOARDS line and just "
            f"add ,{board_name} to it.)"
        ),
    }


def main() -> None:
    if len(sys.argv) != 3:
        print("usage: python -m presence.relay.invite <board> <person>")
        sys.exit(1)
    try:
        result = invite(sys.argv[1], sys.argv[2])
    except RuntimeError as e:
        print(f"invite failed: {e}")
        sys.exit(1)
    print(f"token minted and registered for {result['person']} "
          f"on '{result['board']}'. Send them this privately "
          "(shown once, not stored):\n")
    print(result["message"])


if __name__ == "__main__":
    main()
