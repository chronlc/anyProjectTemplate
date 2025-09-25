# @anyProjectTemplate

Small skeleton project that demonstrates how an AI agent can bootstrap a project
from `docs/PROJECT_FEATURES.md`. It contains helper scripts for reading the
feature document, syncing small records to a local MCP-like store, and a tiny
generator to scaffold idempotently.

## Quick start

1. Create or activate the project's virtualenv using the provided scripts.
   - Example (Linux/macOS):

```bash
./scripts/setup_venv.sh
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run tests:

```bash
./scripts/run_in_venv.sh pytest -q
```

3. Use the built-in prompt task from VS Code (Command Palette -> Run Task -> "Run prompt") or run manually:

```bash
./scripts/run_in_venv.sh python ./scripts/run_prompt.py --prompt "Write a unit test for foo" --json
```

## Environment

Supported environment variables (see `.env.example`):

- `AI_ENABLE_NETWORK` (default: false) — when false returns a deterministic stub instead of calling a provider.
- `AI_MODEL` (default: `gpt-4o-mini`) — model name used for cache keys and traces.
- `AI_CACHE_DB` (default: `.ai_cache.sqlite`) — path to the SQLite cache.

## How to wire a real provider

The implementation point is `scripts/ai_tools/api_client.py`. The network path currently raises
an error if enabled to force explicit wiring. See `scripts/ai_tools/provider_example.py` for a
small stub that shows where to plug a real provider and add cost accounting.

## Notes on editor integration

- This project prefers editor `tasks.json` + small CLI runners for reproducible commands.
- If you want inline editor UX, consider adding a small VS Code extension that calls
  `./scripts/run_in_venv.sh python ./scripts/run_prompt.py --prompt "$prompt" --json` and inserts the result.


Try it locally:

```bash
python3 scripts/ai_tools/reader.py . --out tmp/model.json
python3 scripts/ai_tools/generator.py .
python3 scripts/ai_tools/mcp_sync.py
```

Notes:

- `mcp_sync.py` acts as a local stand-in for the MCP memory when running
  outside the assistant environment. The real agent should call the MCP
  tools directly.
- All tools are written to be idempotent and to log small artifacts to `tmp/`.
