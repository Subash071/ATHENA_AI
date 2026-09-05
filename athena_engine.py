"""
athena_engine.py
----------------------------------------------------------------------
The top-level orchestrator that runs a problem through all four ATHENA
modules in sequence, exactly matching the brief's workflow:

    User Problem
        -> Problem Understanding Engine      (Module 1)
        -> Constraint Identification         (Module 1)
        -> Resource Analysis Engine          (Module 1)
        -> Strategic Planning Engine         (Module 2)
        -> Generate Multiple Solutions       (Module 2)
        -> Solution Ranking System           (Module 3)
        -> Resource Optimization Engine      (Module 3)
        -> Adaptive Decision Engine          (Module 3)
        -> Explainable AI Engine             (Module 4)
        -> Knowledge Repository              (Module 4)
        -> Performance Analytics Engine      (Module 4)
        -> Optimal Solution Generated
"""

import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from dataclasses import dataclass
from typing import Dict, List

from core.problem_model import Problem, ProblemUnderstandingEngine, ProblemAnalysisReport
from core.planning_engine import SolutionGenerator, Solution
from core.optimization_engine import (
    OptimizationEngine, AdaptiveDecisionSystem, StrategyRankingModule, RankedSolution
)
from core.explainable_ai import ExplainableAIEngine
from core.knowledge_repository import KnowledgeRepository
from core.analytics import AnalyticsDashboard, PerformanceEvaluationSystem
from core.decision_report import DecisionEngine, FinalDecisionReport


@dataclass
class AthenaResult:
    problem: Problem
    analysis: ProblemAnalysisReport
    solutions: List[Solution]
    ranked: List[RankedSolution]
    explanation: str
    ranking_lines: List[str]
    performance_summary: List[Dict]
    chart_paths: Dict[str, str]
    run_id: str
    decision_mode: str
    final_report: FinalDecisionReport


class AthenaEngine:
    """One call runs the entire Understand -> Plan -> Optimize -> Explain
    -> Remember -> Visualize pipeline."""

    def __init__(self, knowledge_path: str = None, output_dir: str = None):
        self.understanding_engine = ProblemUnderstandingEngine()
        self.solution_generator = SolutionGenerator()
        self.optimization_engine = OptimizationEngine()
        self.explainable_ai = ExplainableAIEngine()
        self.repository = KnowledgeRepository(
            path=knowledge_path or os.path.join(_PROJECT_ROOT, "data", "knowledge_base.json")
        )
        self.analytics = AnalyticsDashboard(
            output_dir=output_dir or os.path.join(_PROJECT_ROOT, "outputs")
        )
        self.performance_eval = PerformanceEvaluationSystem()
        self.decision_engine = DecisionEngine()

    def run(self, problem: Problem, decision_mode: str = "balanced", save_charts: bool = True) -> AthenaResult:
        # Module 1 — Understand
        analysis = self.understanding_engine.process(problem)

        # Module 2 — Plan & generate multiple strategies
        solutions = self.solution_generator.generate_all(problem)

        # Module 3 — Optimize, adaptively score, and rank
        metrics = self.optimization_engine.compute_all(problem, solutions)
        scored = AdaptiveDecisionSystem(mode=decision_mode).score(metrics)
        ranked = StrategyRankingModule().rank(solutions, scored)

        # Module 5 — Final Decision Engine Output: what did the winner ACTUALLY decide?
        final_report = self.decision_engine.build(problem, ranked)

        # Module 4 — Explain, remember, analyze
        explanation = self.explainable_ai.explain(ranked, problem.unit_label)
        ranking_lines = self.explainable_ai.explain_ranking_table(ranked)
        run_id = self.repository.save_run(problem, ranked, explanation, decision_mode)
        performance_summary = self.performance_eval.summarize(ranked)

        chart_paths = {}
        if save_charts:
            history = self.repository.load_history()
            chart_paths = self.analytics.generate_all(problem, ranked, history)

        return AthenaResult(
            problem=problem,
            analysis=analysis,
            solutions=solutions,
            ranked=ranked,
            explanation=explanation,
            ranking_lines=ranking_lines,
            performance_summary=performance_summary,
            chart_paths=chart_paths,
            run_id=run_id,
            decision_mode=decision_mode,
            final_report=final_report,
        )


# ---------------- Quick self-test ----------------
if __name__ == "__main__":
    from scenarios import scenario_lab_allocation

    engine = AthenaEngine()
    result = engine.run(scenario_lab_allocation(), decision_mode="balanced")

    print("Run ID:", result.run_id)
    print("Conflicts detected:", len(result.analysis.conflicts))
    print("\nRanking:")
    for line in result.ranking_lines:
        print(" ", line)
    print("\nExplanation:\n", result.explanation)
    print("\nCharts:", result.chart_paths)
