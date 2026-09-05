"""
core/optimization_engine.py
----------------------------------------------------------------------
MODULE 3 — Resource Optimization and Adaptive Decision Making
----------------------------------------------------------------------
Responsibilities:
    - Optimize resource utilization
    - Perform adaptive decision making
    - Prioritize intelligent solutions

Features implemented here:
    - OptimizationEngine     (computes hard metrics for each solution)
    - PriorityScheduler       (priority-fairness metric)
    - AdaptiveDecisionSystem  (mode-aware weighted scoring)
    - StrategyRankingModule   (final ranking + percentage scores)
"""

import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR) if os.path.basename(_THIS_DIR) == "core" else _THIS_DIR
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import statistics
from dataclasses import dataclass, field
from typing import Dict, List

from core.problem_model import Problem
from core.planning_engine import Solution, FeasibilityAnalysis


# ======================================================================================
# Metrics
# ======================================================================================

@dataclass
class SolutionMetrics:
    strategy_name: str
    constraint_satisfaction_rate: float     # assigned / total units
    resource_utilization_pct: float         # used capacity / total capacity
    conflicts: int                          # unassigned count
    load_balance_score: float               # 0-100, 100 = perfectly balanced across resources
    priority_fairness_score: float          # 0-100, 100 = all high-priority units served
    execution_time: float
    nodes_explored: int
    optimization_score: float = 0.0         # filled in by AdaptiveDecisionSystem


class OptimizationEngine:
    """Turns a raw Solution into a set of comparable, objective metrics."""

    def compute(self, problem: Problem, solution: Solution) -> SolutionMetrics:
        fa = FeasibilityAnalysis.check(problem, solution)

        total_capacity = problem.total_capacity_all_slots()
        used_capacity = len(solution.assignments)
        utilization = (used_capacity / total_capacity * 100) if total_capacity else 0.0

        # Load balance: how evenly the assignments spread across resources.
        # Lower standard deviation of per-resource load => higher balance score.
        per_resource_load: Dict[str, int] = {}
        for slot_id in solution.assignments.values():
            resource_name = slot_id.split("@")[0]
            per_resource_load[resource_name] = per_resource_load.get(resource_name, 0) + 1
        loads = list(per_resource_load.values())
        if len(loads) > 1 and statistics.mean(loads) > 0:
            cv = statistics.pstdev(loads) / statistics.mean(loads)  # coefficient of variation
            load_balance_score = max(0.0, 100 - cv * 100)
        else:
            load_balance_score = 100.0 if loads else 0.0

        # Priority fairness: what fraction of *priority-weighted demand* was served.
        total_priority = sum(problem.priorities) or 1
        served_priority = sum(problem.priorities[u] for u in solution.assignments)
        priority_fairness_score = served_priority / total_priority * 100

        return SolutionMetrics(
            strategy_name=solution.strategy_name,
            constraint_satisfaction_rate=fa["constraint_satisfaction_rate"] * 100,
            resource_utilization_pct=min(100.0, utilization),
            conflicts=fa["unassigned_count"],
            load_balance_score=load_balance_score,
            priority_fairness_score=priority_fairness_score,
            execution_time=solution.execution_time,
            nodes_explored=solution.nodes_explored,
        )

    def compute_all(self, problem: Problem, solutions: List[Solution]) -> List[SolutionMetrics]:
        return [self.compute(problem, s) for s in solutions]


# ======================================================================================
# Priority Scheduler
# ======================================================================================

class PriorityScheduler:
    """Standalone utility other modules can call to re-order units by
    priority (used for reporting, and available for GUI 'what-if' controls
    that want to re-run planning under a different priority ordering)."""

    @staticmethod
    def order_by_priority(problem: Problem) -> List[int]:
        return sorted(range(problem.num_units), key=lambda i: -problem.priorities[i])

    @staticmethod
    def priority_breakdown(problem: Problem) -> Dict[int, int]:
        breakdown: Dict[int, int] = {}
        for p in problem.priorities:
            breakdown[p] = breakdown.get(p, 0) + 1
        return dict(sorted(breakdown.items(), reverse=True))


# ======================================================================================
# Adaptive Decision System
# ======================================================================================

# Each mode is a weight vector over:
# (satisfaction, utilization, load_balance, priority_fairness, speed)
DECISION_MODES: Dict[str, Dict[str, float]] = {
    "balanced": {
        "satisfaction": 0.30, "utilization": 0.20, "load_balance": 0.15,
        "priority_fairness": 0.25, "speed": 0.10,
    },
    "maximize_utilization": {
        "satisfaction": 0.20, "utilization": 0.45, "load_balance": 0.15,
        "priority_fairness": 0.10, "speed": 0.10,
    },
    "minimize_conflicts": {
        "satisfaction": 0.50, "utilization": 0.15, "load_balance": 0.10,
        "priority_fairness": 0.15, "speed": 0.10,
    },
    "priority_first": {
        "satisfaction": 0.15, "utilization": 0.15, "load_balance": 0.10,
        "priority_fairness": 0.50, "speed": 0.10,
    },
    "fastest": {
        "satisfaction": 0.20, "utilization": 0.15, "load_balance": 0.10,
        "priority_fairness": 0.15, "speed": 0.40,
    },
}


class AdaptiveDecisionSystem:
    """Combines the raw metrics into a single, mode-aware optimization score.

    This is what makes ATHENA "adaptive": the same set of candidate
    solutions can be re-ranked differently depending on what the decision
    maker currently cares about most (raw throughput vs. fairness vs. speed),
    without re-running any search."""

    def __init__(self, mode: str = "balanced"):
        if mode not in DECISION_MODES:
            raise ValueError(f"Unknown decision mode '{mode}'. Options: {list(DECISION_MODES)}")
        self.mode = mode
        self.weights = DECISION_MODES[mode]

    def score(self, metrics_list: List[SolutionMetrics]) -> List[SolutionMetrics]:
        if not metrics_list:
            return []

        max_time = max((m.execution_time for m in metrics_list), default=0.0) or 1e-9
        w = self.weights

        for m in metrics_list:
            speed_score = (1 - (m.execution_time / max_time)) * 100  # faster = higher
            m.optimization_score = round(
                w["satisfaction"] * m.constraint_satisfaction_rate
                + w["utilization"] * m.resource_utilization_pct
                + w["load_balance"] * m.load_balance_score
                + w["priority_fairness"] * m.priority_fairness_score
                + w["speed"] * speed_score,
                2,
            )
        return metrics_list


# ======================================================================================
# Strategy Ranking Module
# ======================================================================================

@dataclass
class RankedSolution:
    rank: int
    solution: Solution
    metrics: SolutionMetrics


class StrategyRankingModule:
    """Sorts scored solutions best-to-worst and assigns rank numbers,
    matching the document's 'Solution-1 = 85%, Solution-2 = 92% ...' style
    of presenting ranked candidates."""

    def rank(self, solutions: List[Solution], metrics_list: List[SolutionMetrics]) -> List[RankedSolution]:
        paired = list(zip(solutions, metrics_list))
        paired.sort(key=lambda pair: pair[1].optimization_score, reverse=True)
        return [
            RankedSolution(rank=i + 1, solution=sol, metrics=met)
            for i, (sol, met) in enumerate(paired)
        ]


# ---------------- Quick self-test ----------------
if __name__ == "__main__":
    from core.problem_model import Resource
    from core.planning_engine import SolutionGenerator

    p = Problem(
        title="Demo",
        unit_label="Student",
        num_units=300,
        resources=[Resource(f"Lab-{i+1}", capacity=8) for i in range(6)],
        timeslots=["9AM", "11AM"],
    )

    solutions = SolutionGenerator().generate_all(p)
    metrics = OptimizationEngine().compute_all(p, solutions)
    scored = AdaptiveDecisionSystem(mode="balanced").score(metrics)
    ranked = StrategyRankingModule().rank(solutions, scored)

    for r in ranked:
        print(f"#{r.rank} {r.metrics.strategy_name:24s} score={r.metrics.optimization_score:5.1f}%  "
              f"satisfaction={r.metrics.constraint_satisfaction_rate:5.1f}%  "
              f"utilization={r.metrics.resource_utilization_pct:5.1f}%  "
              f"fairness={r.metrics.priority_fairness_score:5.1f}%")
