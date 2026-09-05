"""
core/decision_report.py
----------------------------------------------------------------------
MODULE 5 — Final Decision Engine Output
----------------------------------------------------------------------
This is the piece that was missing: ATHENA could say "Greedy First-Fit
won" but never showed WHAT Greedy First-Fit actually decided. This
module takes the winning solution's raw assignment map
(unit_index -> "Resource@Timeslot") and turns it into a concrete,
human-readable allocation report — the actual schedule, not just an
algorithm comparison.

Design notes:
    - Large problems (e.g. 500 students) would produce hundreds of
      individual lines if printed one unit at a time. Instead, this
      module compresses consecutive unit indices assigned to the same
      (resource, timeslot) into ranges — "Unit 1-10" instead of ten
      separate lines — which is also exactly how a human would write
      up a real allocation schedule.
    - Every number in the report (utilization, status checks) is
      computed directly from the actual assignment data, never
      hardcoded or estimated.
"""

import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR) if os.path.basename(_THIS_DIR) == "core" else _THIS_DIR
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from core.problem_model import Problem
from core.optimization_engine import RankedSolution


@dataclass
class AllocationLine:
    resource: str
    timeslot: str
    unit_ranges: List[Tuple[int, int]]   # inclusive (start, end), 0-indexed internally
    count: int

    def unit_range_str(self, unit_label: str) -> str:
        parts = []
        for start, end in self.unit_ranges:
            if start == end:
                parts.append(f"{unit_label} {start + 1}")
            else:
                parts.append(f"{unit_label} {start + 1}-{end + 1}")
        return ", ".join(parts)


@dataclass
class FinalDecisionReport:
    algorithm_name: str
    optimization_score: float
    total_resources: int
    resources_used: int
    total_units: int
    unallocated_count: int
    conflicts_count: int
    allocation_lines: List[AllocationLine]
    resource_utilization: Dict[str, float]
    status_checks: List[Tuple[str, bool]]
    unallocated_units: List[int] = field(default_factory=list)

    @property
    def completion_pct(self) -> float:
        if self.total_units == 0:
            return 0.0
        return round((self.total_units - self.unallocated_count) / self.total_units * 100, 1)


def _compress_ranges(indices: List[int]) -> List[Tuple[int, int]]:
    """[1,2,3,5,6,8] -> [(1,3), (5,6), (8,8)]"""
    if not indices:
        return []
    indices = sorted(indices)
    ranges = []
    start = prev = indices[0]
    for i in indices[1:]:
        if i == prev + 1:
            prev = i
        else:
            ranges.append((start, prev))
            start = prev = i
    ranges.append((start, prev))
    return ranges


class DecisionEngine:
    """Builds the Final Decision Report for the winning (rank #1) solution."""

    def build(self, problem: Problem, ranked: List[RankedSolution]) -> FinalDecisionReport:
        winner = ranked[0]
        solution = winner.solution
        metrics = winner.metrics

        # Group assigned units by (resource, timeslot)
        by_slot: Dict[str, List[int]] = {}
        for unit_idx, slot_id in solution.assignments.items():
            by_slot.setdefault(slot_id, []).append(unit_idx)

        # Preserve a sensible order: resource order as defined in the problem,
        # then timeslot order as defined in the problem.
        allocation_lines: List[AllocationLine] = []
        resources_with_assignments = set()
        for r in problem.available_resources():
            for t in problem.timeslots:
                slot_id = f"{r.name}@{t}"
                units = by_slot.get(slot_id, [])
                if not units:
                    continue
                resources_with_assignments.add(r.name)
                allocation_lines.append(AllocationLine(
                    resource=r.name,
                    timeslot=t,
                    unit_ranges=_compress_ranges(units),
                    count=len(units),
                ))

        # Resource utilization: assigned units / total capacity across all timeslots
        resource_utilization: Dict[str, float] = {}
        for r in problem.available_resources():
            total_capacity = r.capacity * len(problem.timeslots)
            used = sum(
                len(by_slot.get(f"{r.name}@{t}", []))
                for t in problem.timeslots
            )
            resource_utilization[r.name] = round(
                (used / total_capacity * 100) if total_capacity else 0.0, 1
            )

        # "Conflicts" here means hard capacity violations (should always be
        # zero by construction — this is a live confirmation, not a hope)
        used_per_slot: Dict[str, int] = {}
        for slot_id, units in by_slot.items():
            used_per_slot[slot_id] = len(units)
        caps = {
            f"{r.name}@{t}": r.capacity
            for r in problem.available_resources() for t in problem.timeslots
        }
        conflicts_count = sum(
            1 for slot_id, used in used_per_slot.items() if used > caps.get(slot_id, 0)
        )

        status_checks = [
            ("Successfully Allocated", len(solution.unassigned) == 0),
            ("No Conflicts", conflicts_count == 0),
            ("Load Balanced", metrics.load_balance_score >= 70),
            ("Optimized Solution Generated", metrics.optimization_score >= 60),
        ]

        return FinalDecisionReport(
            algorithm_name=metrics.strategy_name,
            optimization_score=metrics.optimization_score,
            total_resources=len(problem.resources),
            resources_used=len(resources_with_assignments),
            total_units=problem.num_units,
            unallocated_count=len(solution.unassigned),
            conflicts_count=conflicts_count,
            allocation_lines=allocation_lines,
            resource_utilization=resource_utilization,
            status_checks=status_checks,
            unallocated_units=list(solution.unassigned),
        )

    @staticmethod
    def format_text_report(problem: Problem, report: FinalDecisionReport, max_lines: int = 60) -> str:
        """Renders the report in the exact plain-text style requested:
        a bordered 'FINAL DECISION REPORT' block, suitable for console
        output or a plain text widget."""
        W = 60
        lines = []
        lines.append("=" * W)
        lines.append("ATHENA'S FINAL DECISION REPORT".center(W))
        lines.append("=" * W)
        lines.append("")
        lines.append("Selected Algorithm:")
        lines.append("-" * 19)
        lines.append(report.algorithm_name)
        lines.append("")
        lines.append("Optimization Score:")
        lines.append("-" * 19)
        lines.append(f"{report.optimization_score:.1f}%")
        lines.append("")
        lines.append("Resources Used:")
        lines.append("-" * 15)
        lines.append(f"{report.resources_used} / {report.total_resources}")
        lines.append("")
        lines.append("Unallocated Units:")
        lines.append("-" * 18)
        lines.append(str(report.unallocated_count))
        lines.append("")
        lines.append("Conflicts:")
        lines.append("-" * 10)
        lines.append(str(report.conflicts_count))
        lines.append("")
        lines.append("-" * W)
        lines.append("")
        lines.append("FINAL RESOURCE ALLOCATION")
        lines.append("")
        shown = report.allocation_lines[:max_lines]
        for line in shown:
            unit_str = line.unit_range_str(problem.unit_label)
            lines.append(f"{line.resource:<12} @ {line.timeslot:<14} --> {unit_str}")
        if len(report.allocation_lines) > max_lines:
            remaining = len(report.allocation_lines) - max_lines
            lines.append(f"... and {remaining} more allocation line(s)")
        lines.append("")
        lines.append("-" * W)
        lines.append("")
        lines.append("RESOURCE UTILIZATION")
        lines.append("")
        for resource, pct in report.resource_utilization.items():
            lines.append(f"{resource:<15} : {pct:>5.1f}%")
        lines.append("")
        lines.append("-" * W)
        lines.append("")
        lines.append("FINAL STATUS")
        lines.append("")
        for label, passed in report.status_checks:
            mark = "\u2713" if passed else "\u2717"
            lines.append(f"{mark} {label}")
        lines.append("")
        lines.append("=" * W)
        return "\n".join(lines)


# ---------------- Quick self-test ----------------
if __name__ == "__main__":
    from core.problem_model import Problem, Resource
    from core.planning_engine import SolutionGenerator
    from core.optimization_engine import OptimizationEngine, AdaptiveDecisionSystem, StrategyRankingModule

    p = Problem(
        title="Decision Report Test", unit_label="Student", num_units=100,
        resources=[Resource(f"Lab-{i+1}", capacity=10) for i in range(10)],
        timeslots=["9AM", "10AM", "11AM", "1PM"],
    )
    solutions = SolutionGenerator().generate_all(p)
    metrics = OptimizationEngine().compute_all(p, solutions)
    scored = AdaptiveDecisionSystem(mode="balanced").score(metrics)
    ranked = StrategyRankingModule().rank(solutions, scored)

    report = DecisionEngine().build(p, ranked)
    print(DecisionEngine.format_text_report(p, report))
