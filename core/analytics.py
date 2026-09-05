"""
core/analytics.py
----------------------------------------------------------------------
MODULE 4c — Performance Analytics & Visualization
----------------------------------------------------------------------
Generates the visual analytics ATHENA promises: a strategy comparison
chart, a resource-utilization breakdown, a constraint heatmap, and a
history trend line across past runs — plus a tabular performance
summary (Module 4's "Strategy Comparison Engine").
"""

import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR) if os.path.basename(_THIS_DIR) == "core" else _THIS_DIR
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from typing import Dict, List

import matplotlib
matplotlib.use("Agg")  # headless-safe backend — no display required
import matplotlib.pyplot as plt
import numpy as np

from core.problem_model import Problem
from core.optimization_engine import RankedSolution

DEFAULT_OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "outputs")

# Palette consistent across every chart ATHENA produces
NAVY = "#1B2A4A"
PURPLE = "#6C4AB6"
TEAL = "#1FB6A6"
ORANGE = "#FF8A3D"
GREY = "#8891A5"
BG = "#F7F8FC"


class AnalyticsDashboard:
    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or DEFAULT_OUTPUT_DIR
        os.makedirs(output_dir, exist_ok=True)

    # ---------------- Strategy comparison bar chart ----------------
    def plot_strategy_comparison(self, ranked: List[RankedSolution], filename: str = "strategy_comparison.png") -> str:
        names = [r.metrics.strategy_name for r in ranked]
        scores = [r.metrics.optimization_score for r in ranked]
        colors = [PURPLE if i > 0 else ORANGE for i in range(len(ranked))]

        fig, ax = plt.subplots(figsize=(9, 5), facecolor=BG)
        ax.set_facecolor(BG)
        bars = ax.bar(names, scores, color=colors, width=0.55, zorder=3)
        for bar, score in zip(bars, scores):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
                     f"{score:.1f}%", ha="center", fontsize=11, fontweight="bold", color=NAVY)

        ax.set_ylim(0, 110)
        ax.set_ylabel("Optimization Score (%)", fontsize=11, color=NAVY)
        ax.set_title("Strategy Comparison \u2014 Optimization Score by Algorithm", fontsize=13, fontweight="bold", color=NAVY, pad=14)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", linestyle="--", alpha=0.35, zorder=0)
        plt.xticks(rotation=10, ha="right", fontsize=9.5)
        plt.tight_layout()

        path = os.path.join(self.output_dir, filename)
        fig.savefig(path, dpi=150)
        plt.close(fig)
        return path

    # ---------------- Resource utilization ----------------
    def plot_resource_utilization(self, problem: Problem, ranked: List[RankedSolution],
                                   filename: str = "resource_utilization.png") -> str:
        winner_solution = ranked[0].solution
        per_resource_load: Dict[str, int] = {}
        for slot_id in winner_solution.assignments.values():
            resource_name = slot_id.split("@")[0]
            per_resource_load[resource_name] = per_resource_load.get(resource_name, 0) + 1

        names = [r.name for r in problem.resources]
        capacities = [r.effective_capacity() * len(problem.timeslots) for r in problem.resources]
        used = [per_resource_load.get(n, 0) for n in names]

        fig, ax = plt.subplots(figsize=(9, 5), facecolor=BG)
        ax.set_facecolor(BG)
        x = np.arange(len(names))
        width = 0.38
        ax.bar(x - width / 2, capacities, width, label="Total Capacity", color=GREY, zorder=3)
        ax.bar(x + width / 2, used, width, label="Used (Winning Solution)", color=TEAL, zorder=3)
        ax.set_xticks(x)
        ax.set_xticklabels(names, rotation=30, ha="right", fontsize=9)
        ax.set_ylabel("Units", fontsize=11, color=NAVY)
        ax.set_title(f"Resource Utilization \u2014 {ranked[0].metrics.strategy_name}", fontsize=13, fontweight="bold", color=NAVY, pad=14)
        ax.legend(frameon=False, fontsize=9.5)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", linestyle="--", alpha=0.35, zorder=0)
        plt.tight_layout()

        path = os.path.join(self.output_dir, filename)
        fig.savefig(path, dpi=150)
        plt.close(fig)
        return path

    # ---------------- Constraint heatmap ----------------
    def plot_constraint_heatmap(self, problem: Problem, ranked: List[RankedSolution],
                                 filename: str = "constraint_heatmap.png") -> str:
        winner_solution = ranked[0].solution
        resources = [r.name for r in problem.available_resources()]
        timeslots = problem.timeslots

        load = np.zeros((len(resources), len(timeslots)))
        cap = np.zeros((len(resources), len(timeslots)))
        res_index = {name: i for i, name in enumerate(resources)}
        slot_cap = {r.name: r.capacity for r in problem.available_resources()}

        for slot_id in winner_solution.assignments.values():
            res_name, ts = slot_id.split("@")
            if res_name in res_index and ts in timeslots:
                load[res_index[res_name], timeslots.index(ts)] += 1

        for r in resources:
            cap[res_index[r], :] = slot_cap[r]

        with np.errstate(divide="ignore", invalid="ignore"):
            pct = np.where(cap > 0, load / cap * 100, 0)

        fig, ax = plt.subplots(figsize=(1.1 * len(timeslots) + 3, 0.45 * len(resources) + 2.5), facecolor=BG)
        im = ax.imshow(pct, cmap="RdYlGn_r", vmin=0, vmax=100, aspect="auto")
        ax.set_xticks(range(len(timeslots)))
        ax.set_xticklabels(timeslots, fontsize=9)
        ax.set_yticks(range(len(resources)))
        ax.set_yticklabels(resources, fontsize=9)
        ax.set_title("Constraint Heatmap \u2014 Resource Load per Timeslot (%)", fontsize=12.5, fontweight="bold", color=NAVY, pad=12)

        for i in range(len(resources)):
            for j in range(len(timeslots)):
                ax.text(j, i, f"{pct[i, j]:.0f}%", ha="center", va="center",
                         fontsize=8, color="black" if pct[i, j] < 65 else "white")

        cbar = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.03)
        cbar.set_label("Load %", fontsize=9)
        plt.tight_layout()

        path = os.path.join(self.output_dir, filename)
        fig.savefig(path, dpi=150)
        plt.close(fig)
        return path

    # ---------------- History trend ----------------
    def plot_history_trend(self, history: List[Dict], filename: str = "history_trend.png") -> str:
        if not history:
            return ""

        runs = list(range(1, len(history) + 1))
        scores = [h["winner_score"] for h in history]

        fig, ax = plt.subplots(figsize=(9, 4.5), facecolor=BG)
        ax.set_facecolor(BG)
        ax.plot(runs, scores, marker="o", color=PURPLE, linewidth=2, zorder=3)
        ax.fill_between(runs, scores, min(scores) - 5 if scores else 0, color=PURPLE, alpha=0.08)
        ax.set_xlabel("Run #", fontsize=10.5, color=NAVY)
        ax.set_ylabel("Winning Score (%)", fontsize=10.5, color=NAVY)
        ax.set_title("Knowledge Repository \u2014 Score Trend Across Past Runs", fontsize=13, fontweight="bold", color=NAVY, pad=14)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", linestyle="--", alpha=0.35, zorder=0)
        plt.tight_layout()

        path = os.path.join(self.output_dir, filename)
        fig.savefig(path, dpi=150)
        plt.close(fig)
        return path

    def generate_all(self, problem: Problem, ranked: List[RankedSolution], history: List[Dict]) -> Dict[str, str]:
        paths = {
            "strategy_comparison": self.plot_strategy_comparison(ranked),
            "resource_utilization": self.plot_resource_utilization(problem, ranked),
            "constraint_heatmap": self.plot_constraint_heatmap(problem, ranked),
        }
        trend_path = self.plot_history_trend(history)
        if trend_path:
            paths["history_trend"] = trend_path
        return paths


# ======================================================================================
# Performance Evaluation System (tabular summary — Module 4's Strategy Comparison Engine)
# ======================================================================================

class PerformanceEvaluationSystem:
    def summarize(self, ranked: List[RankedSolution]) -> List[Dict]:
        return [
            {
                "Rank": r.rank,
                "Strategy": r.metrics.strategy_name,
                "Score (%)": round(r.metrics.optimization_score, 1),
                "Satisfaction (%)": round(r.metrics.constraint_satisfaction_rate, 1),
                "Utilization (%)": round(r.metrics.resource_utilization_pct, 1),
                "Load Balance (%)": round(r.metrics.load_balance_score, 1),
                "Fairness (%)": round(r.metrics.priority_fairness_score, 1),
                "Conflicts": r.metrics.conflicts,
                "Time (ms)": round(r.metrics.execution_time * 1000, 2),
                "Nodes": r.metrics.nodes_explored,
            }
            for r in ranked
        ]


# ---------------- Quick self-test ----------------
if __name__ == "__main__":
    from core.problem_model import Resource
    from core.planning_engine import SolutionGenerator
    from core.optimization_engine import OptimizationEngine, AdaptiveDecisionSystem, StrategyRankingModule
    from core.knowledge_repository import KnowledgeRepository
    from core.explainable_ai import ExplainableAIEngine

    p = Problem(
        title="Analytics Test", unit_label="Student", num_units=180,
        resources=[Resource(f"Lab-{i+1}", capacity=9) for i in range(8)],
        timeslots=["9AM", "11AM", "1PM"],
    )
    solutions = SolutionGenerator().generate_all(p)
    metrics = OptimizationEngine().compute_all(p, solutions)
    scored = AdaptiveDecisionSystem(mode="balanced").score(metrics)
    ranked = StrategyRankingModule().rank(solutions, scored)

    repo = KnowledgeRepository(path=os.path.join(_PROJECT_ROOT, "data", "test_knowledge_base.json"))
    repo.clear()
    explanation = ExplainableAIEngine().explain(ranked, p.unit_label)
    for _ in range(5):
        repo.save_run(p, ranked, explanation, "balanced")

    dash = AnalyticsDashboard(output_dir=DEFAULT_OUTPUT_DIR)
    paths = dash.generate_all(p, ranked, repo.load_history())
    for k, v in paths.items():
        print(k, "->", v, "exists:", os.path.exists(v))

    summary = PerformanceEvaluationSystem().summarize(ranked)
    for row in summary:
        print(row)

    os.remove(os.path.join(_PROJECT_ROOT, "data", "test_knowledge_base.json"))
