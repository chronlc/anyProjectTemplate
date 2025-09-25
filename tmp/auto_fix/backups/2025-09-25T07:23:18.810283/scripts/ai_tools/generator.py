"""Basic scaffolding generator.

This generator is intentionally minimal: it reads the feature model JSON (from
the reader), writes a scaffold marker, and demonstrates idempotent upsert
behaviour.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from scripts.ai_tools.reader import load_feature_model
from scripts.ai_tools.mcp_sync import (
    write_memory,
    append_changelog,
)


def upsert_scaffold(root: str, model: Dict[str, Any]) -> Dict[str, Any]:
    rootp = Path(root)
    tmp = rootp / "tmp"
    tmp.mkdir(exist_ok=True)
    marker = tmp / "scaffold.json"
    payload = {
        "model_path": model.get("path"),
        "features_count": len(model.get("features", [])),
    }

    # idempotent write
    if marker.exists():
        existing = json.loads(marker.read_text(encoding="utf-8"))
        if existing == payload:
            return {"status": "unchanged", "path": str(marker)}

    marker.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_memory("@anyProjectTemplate:scaffold_marker", payload)
    append_changelog("@anyProjectTemplate:scaffold", {"action": "upsert", "payload": payload})
    return {"status": "written", "path": str(marker)}


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()

    model = load_feature_model(args.root)
    if "error" in model:
        print("No PROJECT_FEATURES.md found; nothing to do.")
        return
    res = upsert_scaffold(args.root, model)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
