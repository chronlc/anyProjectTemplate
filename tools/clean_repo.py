#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def remove_dir(name):
    path = ROOT / name
    if path.exists():
        print(f"🗑 Removing {path}")
        shutil.rmtree(path)

def remove_file(name):
    path = ROOT / name
    if path.exists():
        print(f"🗑 Removing {path}")
        path.unlink()

def ensure_gitignore():
    gi = ROOT / ".gitignore"
    patterns = [
        "venv/",
        ".venv/",
        ".pytest_cache/",
        "tmp/",
        "*.log",
        "*.pyc",
        "__pycache__/",
        ".ai_cache.sqlite",
        ".idea/",
        ".vscode/",
    ]
    if gi.exists():
        lines = gi.read_text().splitlines()
    else:
        lines = []
    updated = set(lines) | set(patterns)
    gi.write_text("\n".join(sorted(updated)) + "\n")
    print("✅ Updated .gitignore")

if __name__ == "__main__":
    # Remove duplicate virtualenv
    remove_dir(".venv")

    # Remove docs folder (already migrated)
    remove_dir("docs")

    # Remove AI cache file
    remove_file(".ai_cache.sqlite")

    # Update .gitignore
    ensure_gitignore()

    print("🎉 Cleanup complete")
