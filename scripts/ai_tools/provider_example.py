"""Example provider wiring stub.

This file demonstrates where to implement a real provider client and how to
measure/record a simple cost estimate. It's intentionally non-networking and
keeps behavior minimal; fill in provider logic as needed.
"""
from __future__ import annotations

from typing import Dict, Any


def call_provider(prompt: str, model: str) -> Dict[str, Any]:
    """Placeholder: implement provider call here and return {
    'text': str, 'cost_estimate': float
    }
    """
    # Example stub response
    return {"text": f"[provider stub] {prompt[:200]}", "cost_estimate": 0.0}
