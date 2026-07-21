"""The widget's JS must parse: a syntax error kills the whole page —
including the self-reload timer, so a broken build can never heal itself.
Caught for real on 2026-07-21 (duplicate top-level const)."""

import re
import shutil
import subprocess
from pathlib import Path

import pytest

TEMPLATES = [
    Path(__file__).parents[1] / "presence" / "render" / "template.html",
    Path(__file__).parents[1] / "presence" / "render" / "settings.html",
]


@pytest.mark.parametrize("template", TEMPLATES, ids=lambda p: p.name)
def test_template_js_parses(template, tmp_path):
    node = shutil.which("node")
    if node is None:
        pytest.skip("node not installed")
    scripts = re.findall(r"<script>(.*?)</script>", template.read_text(), re.S)
    assert scripts, f"no script blocks found in {template.name}"
    for i, script in enumerate(scripts):
        stubbed = (script.replace("__DATA__", "[]")
                         .replace("__BOARDS__", "[]")
                         .replace("__BUILT__", '"x"'))
        js = tmp_path / f"{template.stem}_{i}.js"
        js.write_text(stubbed)
        result = subprocess.run([node, "--check", str(js)],
                                capture_output=True, text=True)
        assert result.returncode == 0, (
            f"{template.name} script block {i} does not parse:\n"
            f"{result.stderr}")
