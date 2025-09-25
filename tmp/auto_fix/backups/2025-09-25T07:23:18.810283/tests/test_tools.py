import json

from scripts.ai_tools.reader import load_feature_model
from scripts.ai_tools.generator import upsert_scaffold


def test_reader(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    pf = docs / "PROJECT_FEATURES.md"
    pf.write_text("""# Title

## Feature: auth
- can login

## Feature: api
- exposes /health
""")
    model = load_feature_model(str(tmp_path))
    assert "features" in model
    assert any("Feature: auth" in f["title"] for f in model["features"])


def test_generator_idempotent(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    pf = docs / "PROJECT_FEATURES.md"
    pf.write_text("## Feature: a\n- x\n")
    model = load_feature_model(str(tmp_path))
    res1 = upsert_scaffold(str(tmp_path), model)
    res2 = upsert_scaffold(str(tmp_path), model)
    assert res1["status"] in ("written", "unchanged")
    assert res2["status"] == "unchanged"
    marker = tmp_path / "tmp" / "scaffold.json"
    assert marker.exists()
    # ensure payload is JSON
    data = json.loads(marker.read_text())
    assert "features_count" in data
