# @anyProjectTemplate

Small skeleton project that demonstrates how an AI agent can bootstrap a project
from `docs/PROJECT_FEATURES.md`. It contains helper scripts for reading the
feature document, syncing small records to a local MCP-like store, and a tiny
generator to scaffold idempotently.

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
