"""Lightweight AI client abstraction.

Provides a minimal interface used by project scripts to call AI providers.
Network calls are disabled by default (controlled by AI_ENABLE_NETWORK env var)
so CI and tests never make external calls.
"""
from __future__ import annotations

import os
import hashlib
from typing import Optional, Dict, Any

from .cache import PromptCache
from .rate_limiter import RateLimiter

# Simple configuration via environment
AI_ENABLE_NETWORK = (
    os.getenv("AI_ENABLE_NETWORK", "false").lower() in ("1", "true", "yes")
)
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")

cache = PromptCache()
rate_limiter = RateLimiter()


def _make_key(prompt: str, model: str) -> str:
    h = hashlib.sha256()
    h.update(model.encode())
    h.update(b"\x00")
    h.update(prompt.encode())
    return h.hexdigest()


def call_ai(
    prompt: str,
    *,
    model: Optional[str] = None,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """Call AI with safety guards.

    Returns a dict with keys: text, model, cached(bool), cost_estimate(float)
    """
    model = model or AI_MODEL
    key = _make_key(prompt, model)

    if use_cache:
        cached = cache.get(key)
        if cached is not None:
            return {
                "text": cached,
                "model": model,
                "cached": True,
                "cost_estimate": 0.0,
            }

    # Guard: prevent network calls when disabled
    if not AI_ENABLE_NETWORK:
        # Return a deterministic stub. Callers should handle this in tests/CI.
        stub = f"[AI network disabled] {prompt[:200]}"
        if use_cache:
            cache.set(key, stub)
        return {
            "text": stub,
            "model": model,
            "cached": False,
            "cost_estimate": 0.0,
        }

    # Real network path: placeholder for real provider integration. Implementations
    # should add provider clients and cost accounting here.
    rate_limiter.acquire()  # may block or raise if over quota

    # Minimal placeholder implementation - raise to force explicit wiring.
    raise RuntimeError(
        "AI network enabled but no provider is configured. "
        "Set up provider in api_client.py"
    )
