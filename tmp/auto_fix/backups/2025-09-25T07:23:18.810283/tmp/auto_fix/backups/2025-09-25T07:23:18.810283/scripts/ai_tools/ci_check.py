import json

p = "tmp/auto_fix/report.json"
with open(p) as f:
    r = json.load(f)
if r.get("tests", {}).get("rc", 1) != 0:
    print("Tests failed in auto-fix step")
    raise SystemExit(1)
print("All checks passed")
