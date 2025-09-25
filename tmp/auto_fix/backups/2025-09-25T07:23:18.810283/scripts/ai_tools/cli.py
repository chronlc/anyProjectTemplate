"""Small CLI wrapper for the ai_tools.

Commands:
- scan: parse PROJECT_FEATURES.md and print JSON
- generate: run the generator to upsert scaffold
"""
from __future__ import annotations

import argparse
import json

from scripts.ai_tools.reader import load_feature_model
from scripts.ai_tools.generator import upsert_scaffold


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")

    s_scan = sub.add_parser("scan")
    s_scan.add_argument("root", nargs="?", default=".")

    s_gen = sub.add_parser("generate")
    s_gen.add_argument("root", nargs="?", default=".")

    args = parser.parse_args()
    if args.cmd == "scan":
        model = load_feature_model(args.root)
        print(json.dumps(model, indent=2))
    elif args.cmd == "generate":
        model = load_feature_model(args.root)
        if "error" in model:
            print("No PROJECT_FEATURES.md found; nothing to generate.")
            return
        res = upsert_scaffold(args.root, model)
        print(json.dumps(res, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
