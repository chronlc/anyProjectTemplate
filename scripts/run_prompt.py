"""Minimal runner that calls the project's AI client for ad-hoc prompts.

This is intentionally tiny and well-suited to be invoked from `tasks.json`.
"""
from __future__ import annotations

import argparse
import json

from scripts.ai_tools import api_client


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run a prompt through the project's AI client"
        )
    )
    parser.add_argument("--prompt", "-p", required=True, help="Prompt string")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args(argv)

    res = api_client.call_ai(args.prompt, use_cache=True)
    if args.json:
        print(json.dumps(res, ensure_ascii=False))
    else:
        print(res.get("text"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
