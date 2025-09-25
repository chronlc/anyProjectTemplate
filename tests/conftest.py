import sys
from pathlib import Path

# Ensure the project root is on sys.path so top-level package imports like
# `scripts.ai_tools` work during test collection.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
