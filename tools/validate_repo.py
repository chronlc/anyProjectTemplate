#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import os
import json

# --- Configuration ---
REQUIRED_FILES = {
    "PROGRAM_FEATURES.json": json.dumps(
        {"name": "MyApp", "version": "0.1.0", "features": []}, indent=2
    ),
    "RESEARCH_GUIDELINES.md": "# Research Guidelines\n\nPaste your research notes here.\n",
    "config.json": json.dumps(
        {"project": "anyProjectTemplate", "use_vector_db": True}, indent=2
    ),
    "rules.md": "# Rules\n\nProject rules and constraints.\n",
    "requirements.txt": "# Add project dependencies here\n",
}

REQUIRED_DIRS = [
    "planning",
    "vector_db",
    "automation",
    "debug",
    "memory",
    "tools",
]

IGNORED_ITEMS = ["venv/", ".venv/"]

# --- Functions ---
def ensure_file(path, content=""):
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(content)
        print(f"📄 Created file: {path}")
    else:
        print(f"✔ File exists: {path}")

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
        print(f"📂 Created directory: {path}")
    else:
        print(f"✔ Directory exists: {path}")

    # ensure .gitkeep if empty
    if not any(os.scandir(path)):
        gitkeep = os.path.join(path, ".gitkeep")
        open(gitkeep, "a").close()
        print(f"➕ Added .gitkeep to {path}")

def check_gitignore():
    if not os.path.exists(".gitignore"):
        print("⚠ No .gitignore found!")
        return

    with open(".gitignore", "r") as f:
        lines = f.read().splitlines()

    updated = False
    for item in IGNORED_ITEMS:
        if item not in lines:
            lines.append(item)
            updated = True

    if updated:
        with open(".gitignore", "w") as f:
            f.write("\n".join(lines) + "\n")
        print("✅ Updated .gitignore")
    else:
        print("✔ .gitignore already covers venvs")

# --- Main ---
def main():
    print("🔍 Validating repo structure...\n")

    # files
    for f, content in REQUIRED_FILES.items():
        ensure_file(f, content)

    # dirs
    for d in REQUIRED_DIRS:
        ensure_dir(d)

    # gitignore
    check_gitignore()

    print("\n🎉 Validation complete.")

if __name__ == "__main__":
    main()
