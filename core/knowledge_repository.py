"""
core/knowledge_repository.py
----------------------------------------------------------------------
MODULE 4b — Knowledge Repository
----------------------------------------------------------------------
A lightweight, JSON-backed store of every problem ATHENA has solved and
what it decided, so past decisions can be reviewed, compared, and used
to track whether performance is improving over time.
"""

import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR) if os.path.basename(_THIS_DIR) == "core" else _THIS_DIR
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import json
import time
import uuid
from typing import Dict, List, Optional

from core.problem_model import Problem
from core.optimization_engine import RankedSolution

DEFAULT_KNOWLEDGE_PATH = os.path.join(_PROJECT_ROOT, "data", "knowledge_base.json")


class KnowledgeRepository:
    def __init__(self, path: str = None):
        self.path = path or DEFAULT_KNOWLEDGE_PATH
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        if not os.path.exists(path):
            self._write([])

    # ---------------- persistence helpers ----------------
    def _read(self) -> List[Dict]:
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data: List[Dict]) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # ---------------- public API ----------------
    def save_run(
        self,
        problem: Problem,
        ranked: List[RankedSolution],
        explanation: str,
        decision_mode: str,
    ) -> str:
        run_id = str(uuid.uuid4())[:8]
        record = {
            "run_id": run_id,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "problem_title": problem.title,
            "unit_label": problem.unit_label,
            "num_units": problem.num_units,
            "num_resources": len(problem.resources),
            "num_timeslots": len(problem.timeslots),
            "decision_mode": decision_mode,
            "winner_strategy": ranked[0].metrics.strategy_name,
            "winner_score": ranked[0].metrics.optimization_score,
            "all_scores": {
                r.metrics.strategy_name: r.metrics.optimization_score for r in ranked
            },
            "constraint_satisfaction_rate": ranked[0].metrics.constraint_satisfaction_rate,
            "resource_utilization_pct": ranked[0].metrics.resource_utilization_pct,
            "conflicts": ranked[0].metrics.conflicts,
            "explanation": explanation,
        }
        data = self._read()
        data.append(record)
        self._write(data)
        return run_id

    def load_history(self) -> List[Dict]:
        return self._read()

    def query_similar(self, problem: Problem, tolerance: float = 0.3) -> List[Dict]:
        """Finds past runs with a comparably-sized problem (+/- tolerance)."""
        history = self._read()
        lo, hi = problem.num_units * (1 - tolerance), problem.num_units * (1 + tolerance)
        return [r for r in history if lo <= r["num_units"] <= hi]

    def get_stats(self) -> Dict:
        history = self._read()
        if not history:
            return {"total_runs": 0}

        scores = [r["winner_score"] for r in history]
        strategy_wins: Dict[str, int] = {}
        for r in history:
            strategy_wins[r["winner_strategy"]] = strategy_wins.get(r["winner_strategy"], 0) + 1

        return {
            "total_runs": len(history),
            "average_winner_score": round(sum(scores) / len(scores), 2),
            "best_score_ever": max(scores),
            "most_frequent_winner": max(strategy_wins, key=lambda k: strategy_wins[k]),
            "strategy_win_counts": strategy_wins,
        }

    def clear(self) -> None:
        self._write([])


# ---------------- Quick self-test ----------------
if __name__ == "__main__":
    from core.problem_model import Resource
    from core.planning_engine import SolutionGenerator
    from core.optimization_engine import OptimizationEngine, AdaptiveDecisionSystem, StrategyRankingModule
    from core.explainable_ai import ExplainableAIEngine

    repo = KnowledgeRepository(path=os.path.join(_PROJECT_ROOT, "data", "test_knowledge_base.json"))
    repo.clear()

    p = Problem(
        title="Repo Test", unit_label="Student", num_units=150,
        resources=[Resource(f"Lab-{i+1}", capacity=10) for i in range(8)],
        timeslots=["9AM", "11AM"],
    )
    solutions = SolutionGenerator().generate_all(p)
    metrics = OptimizationEngine().compute_all(p, solutions)
    scored = AdaptiveDecisionSystem(mode="balanced").score(metrics)
    ranked = StrategyRankingModule().rank(solutions, scored)
    explanation = ExplainableAIEngine().explain(ranked, p.unit_label)

    run_id = repo.save_run(p, ranked, explanation, "balanced")
    print("Saved run:", run_id)
    print("History length:", len(repo.load_history()))
    print("Stats:", repo.get_stats())

    os.remove(os.path.join(_PROJECT_ROOT, "data", "test_knowledge_base.json"))
