#!/usr/bin/env python3
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # repo root
MANIFEST = ROOT / "file_manifest.json"


def compute_hash(filepath):
    """Compute SHA256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def scan_files():
    """Scan repo for all files except ignored ones."""
    files = []
    ignore = {".git", "__pycache__", ".pytest_cache", "venv", ".venv"}
    for dirpath, dirnames, filenames in os.walk(ROOT):
        # skip ignored directories
        dirnames[:] = [d for d in dirnames if d not in ignore]
        for name in filenames:
            if name.endswith((".pyc", ".log")):
                continue
            files.append(Path(dirpath) / name)
    return files


def build_manifest():
    files = scan_files()
    return {str(f.relative_to(ROOT)): compute_hash(f) for f in files}


def main():
    print("🔍 Checking repo file integrity...")

    if not MANIFEST.exists():
        print("📄 No manifest found, creating new one...")
        manifest = build_manifest()
        MANIFEST.write_text(json.dumps(manifest, indent=2))
        print(f"✅ Manifest created at {MANIFEST}")
        return

    # load existing manifest
    old = json.loads(MANIFEST.read_text())
    new = build_manifest()

    changed, missing, extra = [], [], []

    for path, h in old.items():
        if path not in new:
            missing.append(path)
        elif new[path] != h:
            changed.append(path)

    for path in new.keys():
        if path not in old:
            extra.append(path)

    if not changed and not missing and not extra:
        print("✅ All files match manifest (integrity check passed)")
    else:
        if changed:
            print("⚠️ Changed files:")
            for c in changed:
                print("  -", c)
        if missing:
            print("❌ Missing files:")
            for m in missing:
                print("  -", m)
        if extra:
            print("➕ New files not in manifest:")
            for e in extra:
                print("  -", e)


if __name__ == "__main__":
    main()
