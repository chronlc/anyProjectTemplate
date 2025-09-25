"""Helper to attempt safe, minimal automatic fixes for lint/test failures.

Behavior:
- Runs ruff/flake8, black, isort (if available) with --fix where applicable.
- Runs pytest and reports status.
- Produces diffs and backups in `tmp/auto_fix/` and writes a small JSON report.
- Intended to be safe and deterministic: only runs well-known formatters/linters' autofix features.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TMP = ROOT / "tmp" / "auto_fix"
TMP.mkdir(parents=True, exist_ok=True)
REPORT_PATH = TMP / "report.json"
BACKUP_DIR = TMP / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_FORMATTERS = [
    ("black", [sys.executable, "-m", "black", "."]),
    ("isort", [sys.executable, "-m", "isort", "."]),
    ("ruff", [sys.executable, "-m", "ruff", "--fix", "."]),
]


def _run(cmd: list[str]) -> tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return p.returncode, p.stdout, p.stderr
    except FileNotFoundError:
        return 127, "", f"{cmd[0]} not found"


def make_backups():
    # create backups for tracked files that might change
    # We'll copy all .py files under the project into backups with timestamp
    ts = datetime.utcnow().isoformat()
    dest = BACKUP_DIR / ts
    dest.mkdir(parents=True, exist_ok=True)
    for p in ROOT.rglob("*.py"):
        rel = p.relative_to(ROOT)
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, out)
    return dest


def run_formatters(report: dict) -> None:
    for name, cmd in DEFAULT_FORMATTERS:
        rc, out, err = _run(cmd)
        report["formatters"].append({"name": name, "rc": rc, "stdout": out, "stderr": err})


def run_linters(report: dict) -> None:
    # run flake8
    rc, out, err = _run([sys.executable, "-m", "flake8"])
    report["linters"].append({"name": "flake8", "rc": rc, "stdout": out, "stderr": err})


def run_tests(report: dict) -> None:
    rc, out, err = _run([sys.executable, "-m", "pytest", "-q"])
    report["tests"] = {"rc": rc, "stdout": out, "stderr": err}


def write_report(report: dict) -> None:
    REPORT_PATH.write_text(json.dumps(report, indent=2))


def main():
    report = {"timestamp": datetime.utcnow().isoformat(), "formatters": [], "linters": [], "tests": {}}
    backup = make_backups()
    report["backup_dir"] = str(backup)

    run_formatters(report)
    run_linters(report)
    # re-run linters after fixes
    run_linters(report)
    run_tests(report)

    write_report(report)
    print(f"Auto-fix report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
