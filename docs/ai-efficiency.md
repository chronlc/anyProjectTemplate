# AI efficiency and cost controls

This repository includes lightweight building blocks to keep AI API costs low and to prevent CI from making any external AI calls.

Key components
- `scripts/ai_tools/api_client.py` — centralized entrypoint for AI calls. Honours `AI_ENABLE_NETWORK=false` in CI and by default returns deterministic stubs.
- `scripts/ai_tools/cache.py` — local SQLite cache to dedupe prompt/response pairs.
- `scripts/ai_tools/rate_limiter.py` — basic token-bucket limiter to spread requests.
- `scripts/ai_tools/self_tuner.py` — small epsilon-greedy tuner to prefer cheaper models when they meet quality thresholds.

Environment variables
- `AI_ENABLE_NETWORK` (default `false` in CI) — when `false` the client returns stubs and avoids network traffic.
- `AI_CACHE_DB` — path to the local cache DB (default `.ai_cache.sqlite`).
- `AI_MODEL` — default model name used by the client if a model isn't provided.

CI behaviour
- `.github/workflows/ci.yml` sets `AI_ENABLE_NETWORK=false` for all CI jobs so workflows never hit external AI APIs.

How to use
- In local development enable `AI_ENABLE_NETWORK=true` and configure a provider in `scripts/ai_tools/api_client.py`.
