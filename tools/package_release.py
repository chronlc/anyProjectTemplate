#!/usr/bin/env python3
import os
import zipfile
import json
from datetime import datetime

EXCLUDE_DIRS = {".git", "venv", ".venv", ".pytest_cache", "__pycache__", "dist"}
EXCLUDE_FILES = {"file_manifest.json", ".DS_Store"}

def should_include(path):
    parts = path.split(os.sep)
    if any(part in EXCLUDE_DIRS for part in parts):
        return False
    if os.path.basename(path) in EXCLUDE_FILES:
        return False
    return True

def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    dist_dir = os.path.join(base_dir, "dist")
    os.makedirs(dist_dir, exist_ok=True)

    # Load version from config.json if available
    version = "0.1.0"
    config_path = os.path.join(base_dir, "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            try:
                data = json.load(f)
                version = data.get("version", version)
            except Exception:
                pass

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    zip_name = f"anyProjectTemplate-v{version}-{ts}.zip"
    zip_path = os.path.join(dist_dir, zip_name)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, base_dir)
                if should_include(rel_path):
                    zf.write(full_path, rel_path)

    print(f"🎉 Release package created: {zip_path}")

if __name__ == "__main__":
    main()
