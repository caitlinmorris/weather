"""An Anthropic-SDK-shaped client that routes through the local `claude`
CLI in headless mode, so extraction bills to the person's existing Claude
subscription (their Claude Code login) instead of a metered API key.

Same prompt, same Haiku model pin — only the billing/auth path differs.
Selected via PRESENCE_EXTRACTOR=claude_cli (default is the API). The
system prompt is prepended to the user message: headless -p mode owns the
real system prompt, and Haiku follows the concatenated form fine.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

# GUI-launched apps (Dock) get a minimal PATH; cover the usual installs.
_CANDIDATE_DIRS = [
    "/opt/homebrew/bin",
    "/usr/local/bin",
    str(Path.home() / ".local" / "bin"),
    str(Path.home() / ".claude" / "local"),
]


class CliUnavailable(Exception):
    pass


def find_claude() -> str | None:
    found = shutil.which("claude")
    if found:
        return found
    for base in _CANDIDATE_DIRS:
        candidate = Path(base) / "claude"
        if candidate.is_file():
            return str(candidate)
    return None


def parse_cli_envelope(stdout: str) -> str:
    """The CLI's --output-format json envelope -> the model's text.
    Raises ValueError with the envelope's own error info when it failed."""
    envelope = json.loads(stdout)
    if envelope.get("is_error"):
        raise ValueError(f"claude CLI returned an error: "
                         f"{envelope.get('result') or envelope}")
    result = envelope.get("result")
    if not isinstance(result, str):
        raise ValueError(f"claude CLI envelope had no text result "
                         f"(keys: {sorted(envelope)})")
    return result


class _TextBlock:
    type = "text"

    def __init__(self, text: str):
        self.text = text


class _Response:
    def __init__(self, text: str):
        self.content = [_TextBlock(text)]


class _Messages:
    def __init__(self, exe: str):
        self._exe = exe

    def create(self, model: str, max_tokens: int, system: str,
               messages: list[dict]) -> _Response:
        prompt = system + "\n\n" + messages[0]["content"]
        proc = subprocess.run(
            [self._exe, "-p", "--output-format", "json", "--model", model],
            input=prompt, capture_output=True, text=True, timeout=300,
        )
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "").strip()[:500]
            raise RuntimeError(
                f"claude CLI extraction failed (are you logged in to "
                f"Claude Code?): {detail}")
        return _Response(parse_cli_envelope(proc.stdout))


class ClaudeCliClient:
    """Duck-types the one SDK surface the extractor uses:
    client.messages.create(...) -> response with .content text blocks."""

    def __init__(self):
        exe = find_claude()
        if exe is None:
            raise CliUnavailable(
                "PRESENCE_EXTRACTOR=claude_cli but no `claude` CLI found — "
                "install Claude Code, or switch billing back to an API key "
                "in settings.")
        self.messages = _Messages(exe)
