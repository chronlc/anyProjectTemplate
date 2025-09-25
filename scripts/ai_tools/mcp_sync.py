"""Production-oriented MCP sync helper.

Guiding principles implemented here:
- Atomic local writes (temp file + move) for durability
- Periodic resync and compare with memory to detect drift
- Minimal batching guidance (collect small changes and write fewer updates)
- Keep large blobs on disk and store references in memory

Notes:
- In an assistant runtime, replace the internal `local_write`/`local_read`
  calls with the MCP memory tool APIs (the code provides explicit hooks).
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional


LOCAL_STORE = Path("tmp/mcp_local.json")
TMP_STORE = Path("tmp/mcp_local.json.tmp")


def _ensure_tmp():
    LOCAL_STORE.parent.mkdir(parents=True, exist_ok=True)
    if not LOCAL_STORE.exists():
        LOCAL_STORE.write_text("{}", encoding="utf-8")


def local_read() -> Dict[str, Any]:
    _ensure_tmp()
    try:
        return json.loads(LOCAL_STORE.read_text(encoding="utf-8"))
    except Exception:
        # on corruption, try to recover from tmp or return empty
        if TMP_STORE.exists():
            try:
                return json.loads(TMP_STORE.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}


def local_write(data: Dict[str, Any]) -> None:
    _ensure_tmp()
    TMP_STORE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    TMP_STORE.replace(LOCAL_STORE)


def write_memory(key: str, value: Any, batch: bool = False) -> None:
    """Write a small JSON-safe value into local store atomically.

    batch: when True, callers intend to write multiple keys and should instead
    collect changes and call `flush_batch` to reduce frequent writes.
    """
    data = local_read()
    data[key] = value
    if not batch:
        local_write(data)
    else:
        # keep changes in memory; caller must call flush_batch with the updated dict
        return


def read_memory(key: str) -> Any:
    data = local_read()
    return data.get(key)


def append_changelog(key: str, entry: Dict[str, Any]) -> None:
    data = local_read()
    cl_key = key + ":changelog"
    cl = data.setdefault(cl_key, [])
    cl.append(entry)
    data[cl_key] = cl
    local_write(data)


def flush_batch(batch_data: Dict[str, Any]) -> None:
    """Atomically flush a prepared batch (dictionary) to the local store."""
    local_write(batch_data)


def resync_from_disk() -> Dict[str, Any]:
    """Force a read from disk; used when agent feels lost and needs to re-sync.

    Returns the current memory dict.
    """
    return local_read()


def detect_oscillation(key: str, window: int = 5) -> Optional[str]:
    """Look for repeated toggling in the last `window` changelog entries.

    Returns an explanatory string if oscillation is detected, otherwise None.
    """
    data = local_read()
    cl = data.get(key + ":changelog", [])
    if len(cl) < window:
        return None
    # naive oscillation detection: check if last N entries alternate between two values
    recent = cl[-window:]
    vals = [json.dumps(e.get("payload", e)) for e in recent]
    unique = list(dict.fromkeys(vals))
    if len(unique) == 2:
        return (
            f"Oscillation detected between {unique[0]} and "
            f"{unique[1]}"
        )
    return None


def human_block_and_record(reason: str) -> None:
    ts = int(time.time())
    entry = {"ts": ts, "reason": reason}
    append_changelog("@anyProjectTemplate:block", entry)


if __name__ == "__main__":
    print("Local MCP store path:", str(LOCAL_STORE))
    print(json.dumps(local_read(), indent=2))
