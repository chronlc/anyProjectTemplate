"""Minimal MCP block writer for local testing.

Writes a block entry into `tmp/mcp_local.json` (a simple JSON array) and also creates a timestamped JSON file under `tmp/auto_fix/blocks/`.
This is intentionally minimal and does not call external MCP APIs.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parents[2]
MCP_LOCAL = ROOT / "tmp" / "mcp_local.json"
BLOCK_DIR = ROOT / "tmp" / "auto_fix" / "blocks"
BLOCK_DIR.mkdir(parents=True, exist_ok=True)


def write_block(diagnostics: Dict[str, object]) -> Path:
    ts = datetime.utcnow().isoformat()
    entry = {"time": ts, "diagnostics": diagnostics}
    # append to mcp_local.json (simple array)
    if MCP_LOCAL.exists():
        data = json.loads(MCP_LOCAL.read_text())
        if not isinstance(data, list):
            data = [data]
    else:
        data = []
    data.append(entry)
    MCP_LOCAL.write_text(json.dumps(data, indent=2))
    out = BLOCK_DIR / f"block_{ts}.json"
    out.write_text(json.dumps(entry, indent=2))
    return out


if __name__ == "__main__":
    import sys

    note = {"reason": sys.argv[1] if len(sys.argv) > 1 else "manual-block"}
    p = write_block(note)
    print(f"Wrote block to {p}")
