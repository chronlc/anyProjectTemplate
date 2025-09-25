"""Simple reader to parse docs/PROJECT_FEATURES.md into a structured model.

This module focuses on safe, deterministic parsing. The format it
expects is simple markdown sections with headers like
`## Feature: <name>` or bullet lists under top-level headings. It
returns a dict suitable for generators.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any


def find_project_features(root: Path) -> Path | None:
    p = root / "docs" / "PROJECT_FEATURES.md"
    if p.exists():
        return p
    # fallback to docs/ in case of alternate layout
    for file in (root / "docs").glob("**/PROJECT_FEATURES.md"):
        return file
    return None


def parse_features_file(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    features = {"raw": text, "features": []}

    # Very small, robust parser: split on top-level headers
    lines = text.splitlines()
    current = None
    buffer = []
    for line in lines:
        if line.strip().startswith("## "):
            if current is not None:
                features["features"].append(
                    {"title": current, "body": "\n".join(buffer).strip()}
                )
            current = line.strip()[3:]
            buffer = []
        else:
            buffer.append(line)
    if current is not None:
        features["features"].append(
            {"title": current, "body": "\n".join(buffer).strip()}
        )

    return features


def load_feature_model(root_path: str = ".") -> Dict[str, Any]:
    root = Path(root_path)
    p = find_project_features(root)
    if not p:
        return {"error": "PROJECT_FEATURES.md not found"}
    model = parse_features_file(p)
    # attach metadata
    model["path"] = str(p)
    return model


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".", help="project root")
    parser.add_argument("--out", help="write json to file")
    args = parser.parse_args()

    model = load_feature_model(args.root)
    if args.out:
        Path(args.out).write_text(json.dumps(model, indent=2), encoding="utf-8")
    else:
        print(json.dumps(model, indent=2))


if __name__ == "__main__":
    main()
