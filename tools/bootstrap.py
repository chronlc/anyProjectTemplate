#!/usr/bin/env python3
"""
Safe bootstrap script for anyProjectTemplate.
- Idempotent: can be run multiple times without overwriting user changes.
- Only creates missing dirs/files.
- Configs are merged instead of replaced.
"""

import os
import json
import subprocess
from pathlib import Path
from tools.logger import log


ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
MEMORY = ROOT / "memory"
DEBUG = ROOT / "debug"
VECTOR_DB = ROOT / "vector_db"
PLANNING = ROOT / "planning"
AUTOMATION = ROOT / "automation"
VENV = ROOT / "venv"
REQUIREMENTS = ROOT / "requirements.txt"
CONFIG = ROOT / "config.json"
RULES = ROOT / "rules.md"
OLD_RULES = ROOT / "instructions.md"
DEVICE_CONFIG = DEBUG / "device_config.json"
RUNNER = DEBUG / "runner.py"


def ensure_dir(path: Path):
    if not path.exists():
        path.mkdir(parents=True)
        log(f"📂 Created {path}")
    else:
        log(f"✔ Directory exists: {path}")


def ensure_file(path: Path, content: str = ""):
    if not path.exists():
        path.write_text(content)
        log(f"📄 Created file: {path}")
    else:
        log(f"✔ File exists: {path}")


def merge_json(path: Path, new_data: dict):
    if path.exists():
        try:
            existing = json.loads(path.read_text())
        except json.JSONDecodeError:
            existing = {}
        merged = {**new_data, **existing}  # existing keys win
        path.write_text(json.dumps(merged, indent=2))
        log(f"🔄 Merged config: {path}")
    else:
        path.write_text(json.dumps(new_data, indent=2))
        log(f"✅ Wrote new config: {path}")


def create_virtualenv():
    if not VENV.exists():
        log("📦 Creating virtual environment...")
        subprocess.run(["python3", "-m", "venv", str(VENV)], check=True)
    else:
        log("✔ venv already exists")

    pip = VENV / "bin" / "pip"
    if REQUIREMENTS.exists():
        log(f"⚡ Installing dependencies from {REQUIREMENTS}")
        subprocess.run([str(pip), "install", "-r", str(REQUIREMENTS)], check=True)
    else:
        log("⚠ No requirements.txt found")


def migrate_rules():
    if OLD_RULES.exists() and not RULES.exists():
        OLD_RULES.rename(RULES)
        log(f"📑 Migrated {OLD_RULES.name} → {RULES.name}")
    elif RULES.exists():
        log(f"✔ Rules file exists: {RULES}")
    else:
        RULES.write_text("# Rules\n")
        log(f"📄 Created new rules.md")


def setup_debug():
    ensure_dir(DEBUG)
    ensure_file(DEVICE_CONFIG, json.dumps({"devices": []}, indent=2))
    ensure_file(RUNNER, "# Debug runner\n")


def main():
    log("🚀 Safe bootstrapping project...")

    # ensure core dirs
    for d in [MEMORY, VECTOR_DB, PLANNING, AUTOMATION]:
        ensure_dir(d)

    # migrate or ensure rules
    migrate_rules()

    # config merge
    default_cfg = {"project": "anyProjectTemplate", "version": "1.0.0"}
    merge_json(CONFIG, default_cfg)

    # requirements + venv
    create_virtualenv()

    # debug setup
    setup_debug()

    log("🎉 Safe bootstrap complete! Repo is ready.")


if __name__ == "__main__":
    main()
