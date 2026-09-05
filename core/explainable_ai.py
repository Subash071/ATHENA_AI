"""
core/explainable_ai.py
----------------------------------------------------------------------
MODULE 4a — Explainable AI Engine
----------------------------------------------------------------------
Turns the ranked, scored solutions into a human-readable justification
for *why* the winning strategy was chosen over the alternatives —
the "Why was Solution-3 selected?" requirement from the brief.
"""

import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR) if os.path.basename(_THIS_DIR) == "core" else _THIS_DIR
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from typing import List
from core.optimization_engine import RankedSolution


class ExplainableAIEngine:
    def explain(self, ranked: List[RankedSolution], unit_label: str = "unit") -> str:
        if not ranked:
            return "No solutions were generated to explain."

        winner = ranked[0]
        runner_up = ranked[1] if len(ranked) > 1 else None
        m = winner.metrics

        reasons = []
        reasons.append(
            f"achieved the highest overall optimization score of {m.optimization_score:.1f}%"
        )
        reasons.append(f"satisfied {m.constraint_satisfaction_rate:.1f}% of all {unit_label} requests")
        reasons.append(f"reached {m.resource_utilization_pct:.1f}% resource utilization")
        reasons.append(f"kept only {m.conflicts} unresolved conflict(s)")
        reasons.append(f"scored {m.load_balance_score:.1f}% on load balance across resources")
        reasons.append(f"served {m.priority_fairness_score:.1f}% of priority-weighted demand")
        reasons.append(f"completed in {m.execution_time*1000:.2f} ms")

        lines = [
            f"Why was \"{winner.metrics.strategy_name}\" selected?",
            "",
            f"\"{winner.metrics.strategy_name}\" was ranked #1 because it " + ", ".join(reasons[:2]) + ".",
            f"In detail, this strategy {', '.join(reasons[2:])}.",
        ]

        if runner_up is not None:
            diff = m.optimization_score - runner_up.metrics.optimization_score
            lines.append(
                f"\nIt outperformed the runner-up, \"{runner_up.metrics.strategy_name}\" "
                f"({runner_up.metrics.optimization_score:.1f}%), by {diff:.1f} percentage points \u2014 "
                + self._compare_reason(m, runner_up.metrics)
            )

        return "\n".join(lines)

    @staticmethod
    def _compare_reason(winner_m, runner_m) -> str:
        deltas = {
            "constraint satisfaction": winner_m.constraint_satisfaction_rate - runner_m.constraint_satisfaction_rate,
            "resource utilization": winner_m.resource_utilization_pct - runner_m.resource_utilization_pct,
            "load balance": winner_m.load_balance_score - runner_m.load_balance_score,
            "priority fairness": winner_m.priority_fairness_score - runner_m.priority_fairness_score,
        }
        biggest = max(deltas, key=lambda k: deltas[k])
        if deltas[biggest] <= 0:
            return "primarily due to a faster, more efficient search."
        return f"mainly driven by a {deltas[biggest]:.1f} point advantage in {biggest}."

    def explain_ranking_table(self, ranked: List[RankedSolution]) -> List[str]:
        """Short one-liner per solution, in the doc's 'Solution-N = X%' style."""
        return [
            f"Solution-{r.rank} ({r.metrics.strategy_name}) = {r.metrics.optimization_score:.1f}%"
            for r in ranked
        ]


# ---------------- Quick self-test ----------------
if __name__ == "__main__":
    from core.problem_model import Problem, Resource
    from core.planning_engine import SolutionGenerator
    from core.optimization_engine import OptimizationEngine, AdaptiveDecisionSystem, StrategyRankingModule

    p = Problem(
        title="Demo", unit_label="Student", num_units=300,
        resources=[Resource(f"Lab-{i+1}", capacity=8) for i in range(6)],
        timeslots=["9AM", "11AM"],
    )
    solutions = SolutionGenerator().generate_all(p)
    metrics = OptimizationEngine().compute_all(p, solutions)
    scored = AdaptiveDecisionSystem(mode="balanced").score(metrics)
    ranked = StrategyRankingModule().rank(solutions, scored)

    print(ExplainableAIEngine().explain(ranked, p.unit_label))
    print()
    for line in ExplainableAIEngine().explain_ranking_table(ranked):
        print(line)
