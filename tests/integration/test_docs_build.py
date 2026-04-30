import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.integration
def test_mkdocs_build_strict(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "--strict", "--site-dir", str(tmp_path / "site")],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / "site" / "index.html").exists()


@pytest.mark.integration
def test_cli_reference_is_generated(monkeypatch: pytest.MonkeyPatch) -> None:
    executable_dir = str(Path(sys.executable).parent)
    monkeypatch.setenv("PATH", f"{executable_dir}:{os.environ.get('PATH', '')}")

    script_path = Path("scripts/dev/regen_cli_docs.py")
    spec = importlib.util.spec_from_file_location("regen_cli_docs", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    expected = module.render_cli_docs()
    actual = Path("docs/cli.md").read_text(encoding="utf-8")

    assert actual == expected
