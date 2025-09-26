# tools/sync_memory.py
"""
Sync seed files into JSON memory + vector DB.

Usage:
  python3 tools/sync_memory.py         # runs sync from repo root
This is intended to be invoked by anyProject.py via the 'sync' command.
"""

import json
import os
from pathlib import Path
from tools import safe_writer, logger, vector_store

log = logger.get_logger()

ROOT = Path(__file__).resolve().parent.parent
PROGRAM_FEATURES = ROOT / "PROGRAM_FEATURES.json"
RESEARCH_GUIDELINES = ROOT / "RESEARCH_GUIDELINES.md"
MEMORY_DIR = ROOT / "memory"
TODO_FILE = MEMORY_DIR / "todo.json"

def load_program_features():
    if not PROGRAM_FEATURES.exists():
        raise FileNotFoundError("PROGRAM_FEATURES.json not found. Please populate it.")
    with open(PROGRAM_FEATURES, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def load_research_guidelines():
    if not RESEARCH_GUIDELINES.exists():
        return ""
    return RESEARCH_GUIDELINES.read_text(encoding="utf-8")

def generate_tasks_from_features(features: dict):
    """
    Turn PROGRAM_FEATURES JSON into a list of task dicts.
    We create a task per top-level feature and nested subtasks if present.
    """
    tasks = []
    # example expected schema: {"name":"MyApp","features":[{"id":"f1","title":"Login","notes":"..."}]}
    for feat in features.get("features", []):
        tid = feat.get("id") or feat.get("title", "")[:40]
        task = {
            "id": str(tid),
            "title": feat.get("title") or feat.get("name") or "feature",
            "description": feat.get("notes") or feat.get("description") or "",
            "status": "pending",
            "source": "PROGRAM_FEATURES",
        }
        # sub-tasks if modules listed
        subs = []
        for mod in feat.get("modules", []) if isinstance(feat.get("modules", []), list) else []:
            subs.append({
                "id": f"{task['id']}-{mod.get('name','mod')}",
                "title": mod.get("name"),
                "description": mod.get("notes",""),
                "status": "pending",
                "source": "PROGRAM_FEATURES"
            })
        if subs:
            task["subtasks"] = subs
        tasks.append(task)
    return tasks

def merge_todos(existing: dict, new_tasks: list):
    """
    Merge new tasks into existing todo.json without duplicating by id.
    """
    if "tasks" not in existing:
        existing["tasks"] = []
    known = {t["id"] for t in existing["tasks"] if "id" in t}
    appended = 0
    for t in new_tasks:
        if t.get("id") in known:
            continue
        existing["tasks"].append(t)
        appended += 1
    return existing, appended

def write_todo_json(obj):
    safe_writer.write_file_safe(str(TODO_FILE), json.dumps(obj, indent=2), mode="merge")

def sync():
    log.info("Starting sync: reading seeds, updating memory.json and vector DB")

    # ensure memory dir
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    # load current todo
    if TODO_FILE.exists():
        try:
            current = json.loads(TODO_FILE.read_text(encoding="utf-8"))
        except Exception:
            current = {"tasks": []}
    else:
        current = {"tasks": []}

    # load seeds
    features = load_program_features()
    research_md = load_research_guidelines()

    # 1) generate tasks
    new_tasks = generate_tasks_from_features(features)
    merged, added = merge_todos(current, new_tasks)
    write_todo_json(merged)
    log.info(f"Tasks merged into {TODO_FILE} — added {added} new tasks")

    # 2) ingest vector DB: PROGRAM_FEATURES.json and RESEARCH_GUIDELINES.md
    pf_text = json.dumps(features, indent=2)
    n_pf = vector_store.ingest("PROGRAM_FEATURES", pf_text, metadata={"type":"features"})
    log.info(f"Ingested PROGRAM_FEATURES into vector DB: {n_pf} chunks")

    if research_md.strip():
        n_r = vector_store.ingest("RESEARCH_GUIDELINES", research_md, metadata={"type":"research"})
        log.info(f"Ingested RESEARCH_GUIDELINES into vector DB: {n_r} chunks")
    else:
        log.info("No RESEARCH_GUIDELINES.md content to ingest")

    # 3) report vector count
    total = vector_store.count()
    log.info(f"Vector DB contains {total} vectors now")

if __name__ == "__main__":
    sync()
