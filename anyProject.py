#!/usr/bin/env python3
"""
anyProject.py - Unified project orchestrator (production-ready)

Commands:
  init        - validate, bootstrap, and seed vector+memory (prompts to edit placeholders)
  sync        - sync PROGRAM_FEATURES + RESEARCH_GUIDELINES into vector DB & memory
  plan        - generate memory/plan.json from PROGRAM_FEATURES.json
  scaffold    - scaffold platform-specific (calls tools/scaffold_<platform>.py)
  codegen     - batch tasks from memory/todo.json into memory/batches/ (rate-limit safe)
  doctor      - run self-checks (venv, adb, Android SDK, vector DB, file health)
  status      - quick status overview
  validate    - run tools/validate_repo.py
  clean       - run tools/clean_repo.py
  help        - show this help
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
import logging

ROOT = Path(__file__).resolve().parent
TOOLS_DIR = ROOT / "tools"
MEMORY_DIR = ROOT / "memory"
VECTOR_DIR = ROOT / "vector_db"
LOG_DIR = ROOT / "logs"
BATCH_DIR = MEMORY_DIR / "batches"
TODO_FILE = MEMORY_DIR / "todo.json"
PLAN_FILE = MEMORY_DIR / "plan.json"
STATE_FILE = MEMORY_DIR / "state.json"
FEATURES_FILE = ROOT / "PROGRAM_FEATURES.json"
RESEARCH_FILE = ROOT / "RESEARCH_GUIDELINES.md"
CONFIG_FILE = ROOT / "config.json"

# Logging setup (rotating file + console)
LOG_DIR.mkdir(exist_ok=True)
logger = logging.getLogger("anyProject")
logger.setLevel(logging.DEBUG)
logfile = LOG_DIR / "anyproject.log"
handler = RotatingFileHandler(logfile, maxBytes=2_000_000, backupCount=5)
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(handler)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
logger.addHandler(ch)

# exit codes
EXIT_OK = 0
EXIT_FAIL = 2

# Utility helpers


def run_subprocess(cmd, cwd=None, capture=False, check=False):
    """Run subprocess and handle errors; return (returncode, stdout)."""
    try:
        if capture:
            res = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return res.returncode, res.stdout.strip() + ("\n" + res.stderr.strip() if res.stderr else "")
        else:
            res = subprocess.run(cmd, cwd=cwd)
            return res.returncode, ""
    except FileNotFoundError:
        logger.error(f"Command not found: {cmd[0]}")
        return 127, ""
    except Exception as e:
        logger.exception(f"Exception running {' '.join(cmd)}: {e}")
        return 1, str(e)


def ensure_memory_dirs():
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    VECTOR_DIR.mkdir(parents=True, exist_ok=True)
    BATCH_DIR.mkdir(parents=True, exist_ok=True)


def load_json_safe(path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        logger.warning(f"Failed to parse JSON at {path}, returning None")
        return None


def write_json_safe(path: Path, data, merge=False):
    if merge and path.exists():
        existing = load_json_safe(path) or {}
        if isinstance(existing, dict) and isinstance(data, dict):
            merged = {**existing, **data}
            path.write_text(json.dumps(merged, indent=2), encoding="utf-8")
            return
        if isinstance(existing, list) and isinstance(data, list):
            # append unique by id if present
            existing_ids = {item.get("id") for item in existing if isinstance(item, dict) and "id" in item}
            for item in data:
                if isinstance(item, dict) and item.get("id") not in existing_ids:
                    existing.append(item)
            path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
            return
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def is_placeholder_json(path: Path):
    """Detect if JSON is placeholder/empty."""
    if not path.exists():
        return True
    try:
        text = path.read_text(encoding="utf-8").strip()
        if text == "" or text == "{}":
            return True
        lower = text.lower()
        for marker in ["todo", "example", "describe", "placeholder"]:
            if marker in lower:
                return True
        # also check if no meaningful keys
        obj = json.loads(text)
        if isinstance(obj, dict) and not obj.get("features") and not obj.get("project_name") and not obj.get("name"):
            return True
        return False
    except Exception:
        return True


def is_placeholder_md(path: Path):
    if not path.exists():
        return True
    txt = path.read_text(encoding="utf-8").strip().lower()
    if txt == "" or txt.startswith("# research guidelines") or any(m in txt for m in ["todo", "example", "describe"]):
        return True
    return False


def prompt_edit(path: Path):
    editor = os.environ.get("EDITOR", "nano")
    logger.info(f"Opening {path} in {editor} for editing. Save and exit to continue.")
    try:
        subprocess.run([editor, str(path)])
    except Exception as e:
        logger.error(f"Failed to run editor {editor}: {e}")
        raise


# Command implementations


def cmd_validate(args):
    """Call tools/validate_repo.py"""
    validate_script = TOOLS_DIR / "validate_repo.py"
    if not validate_script.exists():
        logger.error("validate_repo.py not found in tools/")
        return EXIT_FAIL
    rc, out = run_subprocess([sys.executable, str(validate_script)], capture=True)
    if rc != 0:
        logger.error("validate_repo failed:\n" + out)
        return EXIT_FAIL
    logger.info("validate_repo: OK")
    return EXIT_OK


def cmd_bootstrap(args):
    """Run tools/bootstrap.py (safe, idempotent)"""
    bootstrap_script = TOOLS_DIR / "bootstrap.py"
    if not bootstrap_script.exists():
        logger.error("bootstrap.py not found in tools/")
        return EXIT_FAIL
    rc, out = run_subprocess([sys.executable, str(bootstrap_script)], capture=True)
    if rc != 0:
        logger.error("bootstrap failed:\n" + out)
        return EXIT_FAIL
    logger.info("bootstrap: OK")
    return EXIT_OK


def cmd_init(args):
    """Full init: validate, ensure seeds are non-placeholder, bootstrap, then seed vector/memory"""
    ensure_memory_dirs()
    logger.info("Running validate...")
    if cmd_validate(args) != EXIT_OK:
        logger.error("Validation failed; aborting init.")
        return EXIT_FAIL

    # ensure seed files exist
    if not FEATURES_FILE.exists():
        logger.info("Creating template PROGRAM_FEATURES.json (edit it).")
        FEATURES_FILE.write_text(json.dumps({
            "project_name": "MyNewApp",
            "platform": "android",
            "language": "kotlin",
            "features": []
        }, indent=2), encoding="utf-8")

    if not RESEARCH_FILE.exists():
        RESEARCH_FILE.write_text("# Research Guidelines\n\n", encoding="utf-8")

    # prompt editing if placeholders
    while is_placeholder_json(FEATURES_FILE) or is_placeholder_md(RESEARCH_FILE):
        if is_placeholder_json(FEATURES_FILE):
            logger.warning("PROGRAM_FEATURES.json appears to be a template/placeholder.")
            if args.edit_missing:
                prompt_edit(FEATURES_FILE)
            else:
                logger.info("Run 'anyProject.py edit-features' or re-run init with --edit-missing to edit now.")
                return EXIT_FAIL
        if is_placeholder_md(RESEARCH_FILE):
            logger.warning("RESEARCH_GUIDELINES.md appears to be a template/placeholder.")
            if args.edit_missing:
                prompt_edit(RESEARCH_FILE)
            else:
                logger.info("Run 'anyProject.py edit-guidelines' or re-run init with --edit-missing to edit now.")
                return EXIT_FAIL

    # bootstrap (safe)
    if cmd_bootstrap(args) != EXIT_OK:
        return EXIT_FAIL

    # seed vector DB & memory via tools/sync_memory.py if present, else call vector_store directly via CLI
    sync_script = TOOLS_DIR / "sync_memory.py"
    if sync_script.exists():
        rc, out = run_subprocess([sys.executable, str(sync_script)], capture=True)
        if rc != 0:
            logger.error("sync_memory failed:\n" + out)
            return EXIT_FAIL
        logger.info("seed via sync_memory: OK")
    else:
        # attempt vector_store.py --ingest-source for both files
        vs = TOOLS_DIR / "vector_store.py"
        if vs.exists():
            rc, out = run_subprocess([sys.executable, str(vs), "--ingest-source", "PROGRAM_FEATURES", str(FEATURES_FILE)], capture=True)
            if rc != 0:
                logger.error("vector_store ingest PROGRAM_FEATURES failed:\n" + out)
                return EXIT_FAIL
            rc, out = run_subprocess([sys.executable, str(vs), "--ingest-source", "RESEARCH_GUIDELINES", str(RESEARCH_FILE)], capture=True)
            if rc != 0:
                logger.error("vector_store ingest RESEARCH_GUIDELINES failed:\n" + out)
                return EXIT_FAIL
            logger.info("seed via vector_store CLI: OK")
        else:
            logger.warning("No sync_memory.py or vector_store.py found to seed vector DB; skipping seeding.")

    # update state
    ensure_memory_dirs()
    state = {
        "status": "initialized",
        "last_init": datetime.utcnow().isoformat() + "Z",
    }
    write_json_safe(STATE_FILE, state)
    logger.info("Init complete. Project is initialized.")
    return EXIT_OK


def cmd_sync(args):
    """Re-sync seed files into vector DB + memory (idempotent)"""
    ensure_memory_dirs()
    sync_script = TOOLS_DIR / "sync_memory.py"
    if sync_script.exists():
        rc, out = run_subprocess([sys.executable, str(sync_script)], capture=True)
        if rc != 0:
            logger.error("sync failed:\n" + out)
            return EXIT_FAIL
        logger.info("sync_memory: OK")
        return EXIT_OK
    # fallback: try vector_store CLI options
    vs = TOOLS_DIR / "vector_store.py"
    if vs.exists():
        rc, out = run_subprocess([sys.executable, str(vs), "--ingest-source", "PROGRAM_FEATURES", str(FEATURES_FILE)], capture=True)
        if rc != 0:
            logger.error("vector_store ingest PROGRAM_FEATURES failed:\n" + out)
            return EXIT_FAIL
        rc, out = run_subprocess([sys.executable, str(vs), "--ingest-source", "RESEARCH_GUIDELINES", str(RESEARCH_FILE)], capture=True)
        if rc != 0:
            logger.error("vector_store ingest RESEARCH_GUIDELINES failed:\n" + out)
            return EXIT_FAIL
        logger.info("vector_store CLI ingest: OK")
        return EXIT_OK
    logger.error("No sync implementation found (tools/sync_memory.py or tools/vector_store.py).")
    return EXIT_FAIL


def cmd_plan(args):
    """Generate a plan JSON (memory/plan.json) from PROGRAM_FEATURES.json"""
    ensure_memory_dirs()
    pf = load_json_safe(FEATURES_FILE)
    if not pf:
        logger.error("PROGRAM_FEATURES.json missing or invalid. Run 'anyProject.py init' first.")
        return EXIT_FAIL

    # build simple plan: one task per feature key or item
    plan = {"generated_at": datetime.utcnow().isoformat() + "Z", "tasks": []}
    # features can be dict or list
    features = pf.get("features")
    if isinstance(features, dict):
        items = [{"id": k, "title": k, "details": v} for k, v in features.items()]
    elif isinstance(features, list):
        items = []
        for f in features:
            fid = f.get("id") or f.get("title") or str(len(items) + 1)
            items.append({"id": fid, "title": f.get("title") or f.get("name") or fid, "details": f})
    else:
        # fallback: parse top-level boolean toggles
        toggles = []
        for k, v in pf.items():
            if isinstance(v, bool):
                toggles.append({"id": k, "title": k, "enabled": v})
        items = toggles

    # convert items to tasks with minimal fields
    for it in items:
        task = {
            "id": str(it.get("id")),
            "title": it.get("title"),
            "description": json.dumps(it.get("details")) if isinstance(it.get("details"), dict) else str(it.get("details")),
            "status": "pending",
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
        plan["tasks"].append(task)

    # write plan safely (merge if existing)
    write_json_safe(PLAN_FILE, plan)
    # also merge into todo.json without duplicates
    todo = load_json_safe(TODO_FILE) or {"tasks": []}
    existing_ids = {t.get("id") for t in todo.get("tasks", []) if isinstance(t, dict) and t.get("id")}
    appended = 0
    for t in plan["tasks"]:
        if t["id"] not in existing_ids:
            todo["tasks"].append(t)
            appended += 1
    write_json_safe(TODO_FILE, todo)
    logger.info(f"Plan generated with {len(plan['tasks'])} tasks; {appended} new tasks added to {TODO_FILE}")
    return EXIT_OK


def cmd_scaffold(args):
    """Scaffold platform-specific project if scaffolder available"""
    pf = load_json_safe(FEATURES_FILE) or {}
    platform = pf.get("platform") or pf.get("platform_name") or None
    if not platform:
        logger.error("No platform specified in PROGRAM_FEATURES.json (key: 'platform').")
        return EXIT_FAIL
    script = TOOLS_DIR / f"scaffold_{platform}.py"
    if not script.exists():
        # fallback to scaffold_android.py for 'android'
        if platform.lower() == "android" and (TOOLS_DIR / "scaffold_android.py").exists():
            script = TOOLS_DIR / "scaffold_android.py"
        else:
            logger.error(f"No scaffolder found for platform '{platform}'. Place tools/scaffold_{platform}.py")
            return EXIT_FAIL
    rc, out = run_subprocess([sys.executable, str(script)], capture=True)
    if rc != 0:
        logger.error(f"Scaffold failed:\n{out}")
        return EXIT_FAIL
    logger.info(f"Scaffold for {platform} completed.")
    # mark in state
    st = load_json_safe(STATE_FILE) or {}
    st["last_scaffold"] = {"platform": platform, "time": datetime.utcnow().isoformat() + "Z"}
    write_json_safe(STATE_FILE, st, merge=True)
    return EXIT_OK


def cmd_codegen(args):
    """Batch tasks from TODO into memory/batches for safe rate-limited codegen"""
    ensure_memory_dirs()
    todo = load_json_safe(TODO_FILE) or {"tasks": []}
    pending = [t for t in todo.get("tasks", []) if t.get("status") == "pending"]
    if not pending:
        logger.info("No pending tasks to batch for codegen.")
        return EXIT_OK

    batch_size = args.batch_size or 5
    delay = args.delay or 0  # seconds between batches, used to throttle if needed

    batches = [pending[i:i + batch_size] for i in range(0, len(pending), batch_size)]
    created = 0
    for idx, batch in enumerate(batches, start=1):
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        batch_file = BATCH_DIR / f"batch_{idx}_{ts}.json"
        write_json_safe(batch_file, {"created_at": ts, "tasks": batch})
        logger.info(f"Created batch {batch_file} with {len(batch)} tasks.")
        created += 1
        # mark tasks as 'batched'
        for t in batch:
            for z in todo["tasks"]:
                if z.get("id") == t.get("id"):
                    z["status"] = "batched"
                    z["batched_at"] = ts
        if delay:
            time.sleep(delay)

    # write back todo.json
    write_json_safe(TODO_FILE, todo)
    logger.info(f"Codegen batching complete: {created} batch files created in {BATCH_DIR}")
    # update state
    st = load_json_safe(STATE_FILE) or {}
    st["last_codegen"] = {"batches": created, "time": datetime.utcnow().isoformat() + "Z"}
    write_json_safe(STATE_FILE, st, merge=True)
    return EXIT_OK


def cmd_doctor(args):
    """Run a full health check and report issues"""
    ensure_memory_dirs()
    issues = []
    # 1) venv check
    venv_path = ROOT / "venv"
    if venv_path.exists():
        logger.info("venv: present")
    else:
        issues.append("venv missing (run init to create or create a venv)")

    # 2) adb check
    adb_path = shutil.which("adb")
    if adb_path:
        logger.info(f"adb: found at {adb_path}")
        # try devices
        rc, out = run_subprocess(["adb", "devices"], capture=True)
        if rc == 0:
            logger.info("adb devices output:")
            logger.info(out)
        else:
            issues.append("adb present but 'adb devices' failed or returned error")
    else:
        issues.append("adb not found on PATH")

    # 3) Android SDK env
    if os.getenv("ANDROID_HOME") or os.getenv("ANDROID_SDK_ROOT"):
        logger.info("Android SDK env var detected")
    else:
        issues.append("ANDROID_HOME / ANDROID_SDK_ROOT not set")

    # 4) seed files
    if is_placeholder_json(FEATURES_FILE):
        issues.append("PROGRAM_FEATURES.json missing or placeholder")
    else:
        logger.info("PROGRAM_FEATURES.json: OK")
    if is_placeholder_md(RESEARCH_FILE):
        issues.append("RESEARCH_GUIDELINES.md missing or placeholder")
    else:
        logger.info("RESEARCH_GUIDELINES.md: OK")

    # 5) vector DB count
    vs = TOOLS_DIR / "vector_store.py"
    if vs.exists():
        rc, out = run_subprocess([sys.executable, str(vs), "--count"], capture=True)
        if rc == 0:
            try:
                # vector_store prints like: vectors: N
                for line in out.splitlines():
                    if "vectors" in line.lower():
                        logger.info(line.strip())
                        break
            except Exception:
                logger.info("vector_store count: output:\n" + out)
        else:
            issues.append("vector_store CLI returned error on --count")
    else:
        logger.info("vector_store not present in tools/ (skipping vector check)")

    # print issues summary
    if issues:
        logger.error("Doctor found issues:")
        for i in issues:
            logger.error(" - " + i)
        return EXIT_FAIL
    logger.info("Doctor: all checks passed")
    return EXIT_OK


def cmd_status(args):
    ensure_memory_dirs()
    cnt = 0
    vs = TOOLS_DIR / "vector_store.py"
    if vs.exists():
        rc, out = run_subprocess([sys.executable, str(vs), "--count"], capture=True)
        if rc == 0:
            for line in out.splitlines():
                if "vectors" in line.lower():
                    try:
                        cnt = int(''.join([c for c in line if c.isdigit()]))
                    except Exception:
                        cnt = 0
    logger.info(f"Vector DB: {cnt} entries")
    for f in [FEATURES_FILE, RESEARCH_FILE, CONFIG_FILE]:
        logger.info(f"{f.name}: {'OK' if f.exists() else 'MISSING'}")
    if TODO_FILE.exists():
        todo = load_json_safe(TODO_FILE) or {"tasks": []}
        total = len(todo.get("tasks", []))
        pending = len([t for t in todo.get("tasks", []) if t.get("status") == "pending"])
        logger.info(f"TODO: {total} tasks ({pending} pending)")
    else:
        logger.info("TODO: none")


def cmd_clean(args):
    clean_script = TOOLS_DIR / "clean_repo.py"
    if not clean_script.exists():
        logger.error("clean_repo.py missing in tools/")
        return EXIT_FAIL
    rc, out = run_subprocess([sys.executable, str(clean_script)], capture=True)
    if rc != 0:
        logger.error("clean_repo failed:\n" + out)
        return EXIT_FAIL
    logger.info("clean_repo: OK")
    return EXIT_OK


# CLI setup
def build_parser():
    p = argparse.ArgumentParser(prog="anyProject", description="Manage project lifecycle")
    sp = p.add_subparsers(dest="command")

    sp.add_parser("init", help="Validate, bootstrap, prompt to edit, and seed vector+memory")
    sp.add_parser("sync", help="Sync seed files into vector DB & memory")
    sp.add_parser("plan", help="Generate plan.json from PROGRAM_FEATURES.json")
    sc = sp.add_parser("scaffold", help="Run language/platform scaffolder based on PROGRAM_FEATURES.json")
    cg = sp.add_parser("codegen", help="Batch tasks into memory/batches for codegen")
    cg.add_argument("--batch-size", type=int, default=5)
    cg.add_argument("--delay", type=int, default=0, help="Seconds to wait between batches")
    sp.add_parser("doctor", help="Run system checks (venv, adb, SDK, vector DB)")
    sp.add_parser("status", help="Quick overview (vector count, files, todo)")
    sp.add_parser("validate", help="Run validate_repo.py")
    sp.add_parser("clean", help="Run clean_repo.py")
    sp.add_parser("edit-features", help="Open PROGRAM_FEATURES.json in $EDITOR")
    sp.add_parser("edit-guidelines", help="Open RESEARCH_GUIDELINES.md in $EDITOR")

    # flags
    p.add_argument("--edit-missing", action="store_true", help="During init, open missing seed files in editor automatically")
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()

    # ensure memory dirs exist
    ensure_memory_dirs()

    cmd = args.command
    if cmd == "init":
        return_code = cmd_init(args)
    elif cmd == "sync":
        return_code = cmd_sync(args)
    elif cmd == "plan":
        return_code = cmd_plan(args)
    elif cmd == "scaffold":
        return_code = cmd_scaffold(args)
    elif cmd == "codegen":
        return_code = cmd_codegen(args)
    elif cmd == "doctor":
        return_code = cmd_doctor(args)
    elif cmd == "status":
        return_code = cmd_status(args)
    elif cmd == "validate":
        return_code = cmd_validate(args)
    elif cmd == "clean":
        return_code = cmd_clean(args)
    elif cmd == "edit-features":
        prompt_edit(FEATURES_FILE)
        return_code = EXIT_OK
    elif cmd == "edit-guidelines":
        prompt_edit(RESEARCH_FILE)
        return_code = EXIT_OK
    else:
        parser.print_help()
        return_code = EXIT_OK

    # log final state and exit
    if return_code == EXIT_OK:
        logger.info(f"Command '{cmd}' finished successfully")
    else:
        logger.error(f"Command '{cmd}' failed (exit code {return_code})")
    sys.exit(return_code)


if __name__ == "__main__":
    main()
