"""
core/problem_model.py
----------------------------------------------------------------------
MODULE 1 — Problem Understanding and Constraint Analysis
----------------------------------------------------------------------
Responsibilities:
    - Analyze user inputs
    - Identify constraints
    - Understand available resources
    - Detect conflicts
    - Build a problem representation (graph model)

Features implemented here:
    - ConstraintAnalyzer
    - ResourceAnalyzer
    - ConflictDetectionSystem
    - ProblemModelingEngine
    - ProblemUnderstandingEngine (facade that runs all of the above)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import networkx as nx


# ======================================================================================
# Data model
# ======================================================================================

@dataclass
class Resource:
    """A single allocatable resource (a lab, a machine, an employee, a vehicle, ...)."""
    name: str
    capacity: int              # units it can serve PER timeslot
    available: bool = True     # False = fully unavailable (e.g. under maintenance)

    def effective_capacity(self) -> int:
        return self.capacity if self.available else 0


@dataclass
class Problem:
    """A generalized constraint-driven resource allocation / scheduling problem.

    This single abstraction is deliberately general enough to model every
    scenario ATHENA is meant to solve: laboratory allocation, workforce
    scheduling, transportation slots, hospital scheduling, etc. Each "unit"
    (a student, a task, a patient...) needs to be matched to one
    (resource, timeslot) pair without violating resource capacity.
    """
    title: str
    unit_label: str                    # e.g. "Student", "Task", "Employee Shift"
    num_units: int
    resources: List[Resource]
    timeslots: List[str]
    priorities: Optional[List[int]] = None   # 1 (low) - 5 (critical) per unit
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.priorities is None:
            self.priorities = [1] * self.num_units
        if len(self.priorities) != self.num_units:
            raise ValueError("priorities length must match num_units")

    def total_capacity_per_slot(self) -> int:
        return sum(r.effective_capacity() for r in self.resources)

    def total_capacity_all_slots(self) -> int:
        return self.total_capacity_per_slot() * len(self.timeslots)

    def available_resources(self) -> List[Resource]:
        return [r for r in self.resources if r.available and r.capacity > 0]


# ======================================================================================
# Constraint Analyzer
# ======================================================================================

class ConstraintAnalyzer:
    """Understands the hard limits the problem is operating under."""

    def analyze(self, problem: Problem) -> Dict[str, Any]:
        cap_per_slot = problem.total_capacity_per_slot()
        cap_total = problem.total_capacity_all_slots()
        demand = problem.num_units
        deficit = max(0, demand - cap_total)
        unavailable = [r.name for r in problem.resources if not r.available]

        return {
            "demand": demand,
            "capacity_per_slot": cap_per_slot,
            "total_capacity_all_slots": cap_total,
            "num_timeslots": len(problem.timeslots),
            "capacity_deficit": deficit,
            "fully_satisfiable": deficit == 0,
            "unavailable_resources": unavailable,
            "unavailable_count": len(unavailable),
            "theoretical_min_slots_needed": (
                0 if cap_per_slot == 0 else -(-demand // cap_per_slot)  # ceil div
            ),
        }


# ======================================================================================
# Resource Analyzer
# ======================================================================================

class ResourceAnalyzer:
    """Understands what is actually available to work with."""

    def analyze(self, problem: Problem) -> Dict[str, Any]:
        available = problem.available_resources()
        by_resource = {
            r.name: {
                "capacity": r.capacity,
                "available": r.available,
                "capacity_all_slots": r.effective_capacity() * len(problem.timeslots),
            }
            for r in problem.resources
        }
        total_available_capacity = sum(r.effective_capacity() for r in problem.resources)

        return {
            "total_resources": len(problem.resources),
            "available_resources_count": len(available),
            "unavailable_resources_count": len(problem.resources) - len(available),
            "total_available_capacity_per_slot": total_available_capacity,
            "resource_breakdown": by_resource,
            "largest_resource": max(problem.resources, key=lambda r: r.capacity).name
            if problem.resources else None,
        }


# ======================================================================================
# Conflict Detection System
# ======================================================================================

class ConflictDetectionSystem:
    """Flags structural problems before any solving is attempted."""

    def detect(self, problem: Problem) -> List[Dict[str, Any]]:
        conflicts = []
        cap_total = problem.total_capacity_all_slots()

        if problem.num_units > cap_total:
            conflicts.append({
                "type": "OVER_SUBSCRIPTION",
                "severity": "HIGH",
                "message": (
                    f"Demand ({problem.num_units} {problem.unit_label.lower()}s) exceeds "
                    f"total available capacity ({cap_total}) across all timeslots by "
                    f"{problem.num_units - cap_total}."
                ),
            })

        unavailable = [r for r in problem.resources if not r.available]
        if unavailable:
            conflicts.append({
                "type": "RESOURCE_UNAVAILABLE",
                "severity": "MEDIUM",
                "message": (
                    f"{len(unavailable)} resource(s) unavailable: "
                    f"{', '.join(r.name for r in unavailable)}."
                ),
            })

        if not problem.timeslots:
            conflicts.append({
                "type": "NO_TIMESLOTS",
                "severity": "CRITICAL",
                "message": "No timeslots defined \u2014 no schedule can be built.",
            })

        zero_cap = [r for r in problem.resources if r.available and r.capacity <= 0]
        if zero_cap:
            conflicts.append({
                "type": "ZERO_CAPACITY_RESOURCE",
                "severity": "LOW",
                "message": f"{len(zero_cap)} resource(s) marked available but have zero capacity.",
            })

        return conflicts


# ======================================================================================
# Problem Modeling Engine
# ======================================================================================

class ProblemModelingEngine:
    """Builds an internal graph representation of the problem.

    Nodes:  UNIT_i, RESOURCE_name@TIMESLOT (a "slot instance")
    Edges:  UNIT_i -> slot instance it *could* be assigned to (feasibility edge)

    This graph underpins both the search algorithms in Module 2 (which treat
    slot instances as the domain of each unit) and the visual analytics in
    Module 4 (constraint heatmaps, utilization graphs).
    """

    def build_model(self, problem: Problem) -> nx.Graph:
        g = nx.Graph()

        for i in range(problem.num_units):
            g.add_node(f"UNIT_{i}", kind="unit", priority=problem.priorities[i])

        slot_instances = []
        for r in problem.available_resources():
            for t in problem.timeslots:
                slot_id = f"{r.name}@{t}"
                g.add_node(slot_id, kind="slot", resource=r.name, timeslot=t, capacity=r.capacity)
                slot_instances.append(slot_id)

        # Every unit can feasibly go into every open slot instance (fully-connected
        # feasibility graph) — later modules decide which edge is actually used.
        for i in range(problem.num_units):
            for slot_id in slot_instances:
                g.add_edge(f"UNIT_{i}", slot_id)

        return g

    @staticmethod
    def slot_instances(problem: Problem) -> List[str]:
        return [f"{r.name}@{t}" for r in problem.available_resources() for t in problem.timeslots]


# ======================================================================================
# Facade
# ======================================================================================

@dataclass
class ProblemAnalysisReport:
    problem: Problem
    constraints: Dict[str, Any]
    resources: Dict[str, Any]
    conflicts: List[Dict[str, Any]]
    graph: nx.Graph


class ProblemUnderstandingEngine:
    """Module 1 facade — runs the full understanding pipeline in one call."""

    def __init__(self):
        self.constraint_analyzer = ConstraintAnalyzer()
        self.resource_analyzer = ResourceAnalyzer()
        self.conflict_detector = ConflictDetectionSystem()
        self.modeling_engine = ProblemModelingEngine()

    def process(self, problem: Problem) -> ProblemAnalysisReport:
        return ProblemAnalysisReport(
            problem=problem,
            constraints=self.constraint_analyzer.analyze(problem),
            resources=self.resource_analyzer.analyze(problem),
            conflicts=self.conflict_detector.detect(problem),
            graph=self.modeling_engine.build_model(problem),
        )


# ---------------- Quick self-test ----------------
if __name__ == "__main__":
    p = Problem(
        title="Demo Lab Allocation",
        unit_label="Student",
        num_units=120,
        resources=[Resource(f"Lab-{i+1}", capacity=10) for i in range(10)],
        timeslots=["9AM", "11AM", "1PM"],
    )
    report = ProblemUnderstandingEngine().process(p)
    print("Constraints:", report.constraints)
    print("Resources:", report.resources["available_resources_count"], "available")
    print("Conflicts:", report.conflicts)
    print("Graph nodes:", report.graph.number_of_nodes(), "edges:", report.graph.number_of_edges())
