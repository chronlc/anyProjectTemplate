"""Self-tuning module: simple epsilon-greedy bandit to choose model/profile cheaply."""
from __future__ import annotations

import random
from typing import List, Dict, Any


class SelfTuner:
    def __init__(self, options: List[Dict[str, Any]], epsilon: float = 0.1):
        """options: list of candidate models/profiles, each a dict with 'name' and 'cost_est'."""
        self.options = options
        self.epsilon = epsilon
        self.counts = {opt['name']: 0 for opt in options}
        self.rewards = {opt['name']: 0.0 for opt in options}

    def choose(self) -> str:
        if random.random() < self.epsilon:
            return random.choice(self.options)['name']
        # pick best avg reward/cost
        best = None
        best_score = -float('inf')
        for opt in self.options:
            name = opt['name']
            avg = (self.rewards[name] / self.counts[name]) if self.counts[name] > 0 else 0.0
            score = avg - opt.get('cost_est', 0.0)
            if score > best_score:
                best_score = score
                best = name
        return best

    def update(self, name: str, reward: float) -> None:
        self.counts[name] += 1
        self.rewards[name] += reward
