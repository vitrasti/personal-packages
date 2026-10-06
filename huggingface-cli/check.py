"""Offline smoke checks for the installed RPM launcher and private dependency set."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile

launcher = Path(sys.argv[1]).absolute()
expected_version = sys.argv[2]
payload = launcher.resolve().parent

with tempfile.TemporaryDirectory(prefix="hf-rpm-check-") as temp:
    home = Path(temp)
    env = dict(os.environ, HOME=temp, HF_HOME=str(home / "hf-home"),
               XDG_CACHE_HOME=str(home / "cache"), HF_HUB_OFFLINE="1",
               HF_HUB_DISABLE_TELEMETRY="1", HF_HUB_DISABLE_UPDATE_CHECK="1",
               HF_TOKEN="", HUGGING_FACE_HUB_TOKEN="", NO_COLOR="1")
    # Neither the current directory nor PYTHONPATH/user site may replace private libs.
    (home / "click.py").write_text("raise RuntimeError('Unisolated Python import')\n")
    env["PYTHONPATH"] = temp
    env["PYTHONUSERBASE"] = temp

    def run(*args, returncode=0):
        result = subprocess.run([str(launcher), *args], cwd=temp, env=env,
                                text=True, capture_output=True, timeout=60)
        assert result.returncode == returncode, result.stdout + result.stderr
        return result.stdout + result.stderr

    assert expected_version in run("version")
    assert "download" in run("--help")
    for args in (("auth", "login"), ("download",), ("upload",), ("cache",),
                 ("extensions",), ("skills",)):
        assert "Usage:" in run(*args, "--help")
    run("env")
    (home / "hf-home" / "hub").mkdir(parents=True)
    run("cache", "ls")
    assert "managed by RPM" in run("update", returncode=1)
    for shell in ("bash", "zsh", "fish"):
        env["SHELL"] = f"/usr/bin/{shell}"
        assert "_HF_COMPLETE" in run("--show-completion")

    # Offline download exercises CLI parsing and the real upstream cache layout.
    cache = home / "hf-home" / "hub" / "models--rpm-test--model"
    revision = "a" * 40
    snapshot = cache / "snapshots" / revision
    snapshot.mkdir(parents=True)
    (cache / "refs").mkdir()
    (cache / "refs" / "main").write_text(revision)
    (snapshot / "config.json").write_text('{"rpm_smoke_test": true}\n')
    assert str(snapshot / "config.json") in run("download", "rpm-test/model", "config.json")

    # Bootstrap the actual launcher without invoking main, then inspect imports and
    # validate the installed metadata against every applicable runtime requirement.
    inspection = """
import importlib
from importlib.metadata import distributions
from pathlib import Path
import runpy
import sys
runpy.run_path(sys.argv[1], run_name='hf_rpm_inspection')
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
import hf_xet
import httpx2
import yaml
root = Path(sys.argv[1]).resolve().parent / 'site-packages'
installed = {canonicalize_name(d.name): d for d in distributions(path=[str(root)])}
for dist in installed.values():
    for text in dist.requires or []:
        req = Requirement(text)
        if req.marker and not req.marker.evaluate({'extra': ''}):
            continue
        dependency = installed[canonicalize_name(req.name)]
        assert dependency.version in req.specifier, (dist.name, text, dependency.version)
for name in ('huggingface_hub', 'click', 'httpx2', 'httpcore2', 'hf_xet', 'yaml'):
    module = importlib.import_module(name)
    assert Path(module.__file__).is_relative_to(root), module.__file__
assert yaml.safe_load('check: true')['check'] is True
assert not yaml.__with_libyaml__
assert sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode
# The update policy must exit before consulting PyPI or spawning an installer.
from unittest.mock import patch
from click.testing import CliRunner
from huggingface_hub.cli.hf import app
with patch('huggingface_hub.cli.system._fetch_latest_pypi_version',
           side_effect=AssertionError('Unexpected update network access')):
    result = CliRunner().invoke(app, ['update'])
    assert result.exit_code == 1 and 'managed by RPM' in result.output, result.output
print('Private dependency metadata, native imports, isolation and update policy passed')
"""
    subprocess.run([sys.executable, "-ISB", "-c", inspection, str(payload / "hf.py")],
                   cwd=temp, env=env, check=True, timeout=60)
    assert not list(payload.rglob("__pycache__")), "Runtime wrote bytecode into payload"
    print("Passed: version/help, cache, offline download, shell completion and private runtime")
