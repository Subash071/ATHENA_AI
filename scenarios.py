"""
scenarios.py
----------------------------------------------------------------------
Ready-made problem instances matching the two example scenarios from
the ATHENA project brief, plus a helper for building custom problems
(used by both the CLI and the GUI).
"""

import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import random
from typing import List, Optional

from core.problem_model import Problem, Resource


def scenario_lab_allocation() -> Problem:
    """Document Scenario 1: 500 students, 20 laboratories, 50 systems
    unavailable, 6 available timings."""
    resources = [Resource(f"Lab-{i+1}", capacity=30) for i in range(20)]
    # Remove capacity equivalent to 50 unavailable systems, spread realistically
    knock_out = [15, 15, 10, 10]
    for i, amount in enumerate(knock_out):
        resources[i].capacity -= amount

    random.seed(42)
    priorities = [random.choice([1, 1, 2, 2, 3, 4, 5]) for _ in range(500)]

    return Problem(
        title="Scenario 1 \u2014 Laboratory Allocation",
        unit_label="Student",
        num_units=500,
        resources=resources,
        timeslots=["9:00 AM", "10:00 AM", "11:00 AM", "1:00 PM", "2:00 PM", "3:00 PM"],
        priorities=priorities,
        metadata={"domain": "Smart Campus Planning"},
    )


def scenario_workforce_allocation() -> Problem:
    """Document Scenario 2: 100 employees, 40 tasks, limited resources,
    multiple priorities. Modeled as 40 tasks (units) needing an
    (employee, shift) slot from a pool of 100 employees across 3 shifts,
    with each employee handling at most 1 task per shift."""
    resources = [Resource(f"Employee-{i+1}", capacity=1) for i in range(100)]

    random.seed(7)
    priorities = [random.choice([1, 2, 2, 3, 3, 4, 5, 5]) for _ in range(40)]

    return Problem(
        title="Scenario 2 \u2014 Workforce Task Allocation",
        unit_label="Task",
        num_units=40,
        resources=resources,
        timeslots=["Morning Shift", "Afternoon Shift", "Evening Shift"],
        priorities=priorities,
        metadata={"domain": "Workforce Management"},
    )


def build_custom_problem(
    title: str,
    unit_label: str,
    num_units: int,
    num_resources: int,
    resource_capacity: int,
    num_unavailable: int,
    timeslots: List[str],
    priorities: Optional[List[int]] = None,
) -> Problem:
    """General-purpose builder used by the GUI's custom-problem form."""
    resources = [Resource(f"Resource-{i+1}", capacity=resource_capacity) for i in range(num_resources)]
    for i in range(min(num_unavailable, num_resources)):
        resources[i].available = False

    return Problem(
        title=title,
        unit_label=unit_label,
        num_units=num_units,
        resources=resources,
        timeslots=timeslots,
        priorities=priorities,
    )


SCENARIOS = {
    "1": ("Laboratory Allocation (500 students, 20 labs)", scenario_lab_allocation),
    "2": ("Workforce Task Allocation (100 employees, 40 tasks)", scenario_workforce_allocation),
}
