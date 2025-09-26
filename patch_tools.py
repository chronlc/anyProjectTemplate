#!/usr/bin/env python3
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TOOLS_DIR = ROOT / "tools"

# Shim we want to inject
SHIM = """\
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
"""

def patch_file(file_path: Path):
    text = file_path.read_text()

    # Skip if shim already present
    if "Path(__file__).resolve().parents[1]" in text:
        print(f"✔ Already patched: {file_path.name}")
        return

    # Find first non-shebang line
    lines = text.splitlines()
    insert_at = 0
    if lines and lines[0].startswith("#!"):
        insert_at = 1

    # Inject shim
    lines.insert(insert_at, SHIM)
    file_path.write_text("\n".join(lines) + "\n")
    print(f"🔧 Patched: {file_path.name}")

def main():
    if not TOOLS_DIR.exists():
        print("❌ No tools/ directory found.")
        return

    for py_file in TOOLS_DIR.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
        patch_file(py_file)

    print("\n🎉 All tool scripts patched successfully.")

if __name__ == "__main__":
    main()
