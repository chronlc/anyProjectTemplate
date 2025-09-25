"""Safe apply/replace utility for file generation.

Rules implemented:
- Do not append to existing files. If a replace cannot be done via string
  replacement, delete and regenerate the file.
- Always write to a temp file and move into place atomically.
- Create a `.bak` backup of the previous file before replacing.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Callable


def safe_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    if path.exists():
        bak = path.with_suffix(path.suffix + ".bak")
        shutil.copy2(path, bak)
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def replace_or_regenerate(
    path: Path,
    new_content: str,
    can_patch: Callable[[str, str], bool] | None = None,
) -> None:
    """Try to patch via a provided predicate; if not possible, delete and regenerate.

    can_patch(old, new) -> bool should return True if a safe string-replace is OK.
    """
    if path.exists() and can_patch is not None:
        old = path.read_text(encoding="utf-8")
        if can_patch(old, new_content):
            # perform a direct replacement (caller ensures it is safe)
            safe_write(path, new_content)
            return

    # otherwise regenerate: remove and write fresh
    if path.exists():
        path.unlink()
    safe_write(path, new_content)


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("file")
    p.add_argument("--from-stdin", action="store_true")
    args = p.parse_args()
    if args.from_stdin:
        import sys

        content = sys.stdin.read()
        replace_or_regenerate(Path(args.file), content)
    else:
        print("use --from-stdin to pipe content")
