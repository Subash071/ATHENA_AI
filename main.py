"""
main.py
----------------------------------------------------------------------
ATHENA — Artificial Thinking Engine for Intelligent Planning,
Optimization and Adaptive Decision Making

Run this file for the full interactive terminal experience:
    python main.py
"""

import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import time

# ---- Friendly dependency check ----------------------------------------
# If requirements.txt hasn't been installed (or was installed into a
# different Python interpreter than the one running this file), importing
# `rich` crashes with a raw traceback that looks like the program is
# broken. Catch that specific case and explain exactly what to do instead.
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
    from rich.prompt import Prompt, IntPrompt
    from rich.align import Align
    from rich import box
except ModuleNotFoundError as e:
    print("=" * 70)
    print("ATHENA could not start because a required package is missing:")
    print(f"    {e}")
    print()
    print("Fix: open a terminal in this project folder and run:")
    print(f"    {sys.executable} -m pip install -r requirements.txt")
    print()
    print("If you're using a virtual environment, make sure it's activated")
    print("first (VS Code should show its name in the terminal prompt).")
    print("=" * 70)
    sys.exit(1)

from athena_engine import AthenaEngine
from scenarios import scenario_lab_allocation, scenario_workforce_allocation, build_custom_problem
from core.optimization_engine import DECISION_MODES

console = Console()

BANNER = r"""
[bold magenta] █████╗ ████████╗██╗  ██╗███████╗███╗   ██╗ █████╗ [/bold magenta]
[bold magenta]██╔══██╗╚══██╔══╝██║  ██║██╔════╝████╗  ██║██╔══██╗[/bold magenta]
[bold magenta]███████║   ██║   ███████║█████╗  ██╔██╗ ██║███████║[/bold magenta]
[bold magenta]██╔══██║   ██║   ██╔══██║██╔══╝  ██║╚██╗██║██╔══██║[/bold magenta]
[bold magenta]██║  ██║   ██║   ██║  ██║███████╗██║ ╚████║██║  ██║[/bold magenta]
[bold magenta]╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝[/bold magenta]
"""


def print_banner():
    console.clear()
    console.print(Align.center(BANNER))
    console.print(Align.center(
        "[bold white]Artificial Thinking Engine for Intelligent Planning,[/bold white]\n"
        "[bold white]Optimization and Adaptive Decision Making[/bold white]"
    ))
    console.print()


def thinking_steps(steps):
    """Visualizes ATHENA's pipeline stages as a live progress sequence —
    turns the module pipeline into something that FEELS like an engine
    thinking, not just a silent function call."""
    with Progress(
        SpinnerColumn(style="magenta"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=30, style="grey35", complete_style="magenta"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("", total=len(steps))
        for step in steps:
            progress.update(task, description=f"[cyan]{step}[/cyan]")
            time.sleep(0.25)
            progress.advance(task)


def choose_problem():
    console.print(Panel(
        "[bold]1[/bold]  Scenario 1 \u2014 Laboratory Allocation (500 students, 20 labs)\n"
        "[bold]2[/bold]  Scenario 2 \u2014 Workforce Task Allocation (100 employees, 40 tasks)\n"
        "[bold]3[/bold]  Custom Problem \u2014 define your own",
        title="[bold magenta]Choose a Problem[/bold magenta]", box=box.ROUNDED, border_style="magenta",
    ))
    choice = Prompt.ask("Enter choice", choices=["1", "2", "3"], default="1")

    if choice == "1":
        return scenario_lab_allocation()
    elif choice == "2":
        return scenario_workforce_allocation()
    else:
        console.print("\n[bold]Define your custom problem:[/bold]")
        title = Prompt.ask("Problem title", default="Custom Allocation Problem")
        unit_label = Prompt.ask("Unit label (e.g. Student, Task, Patient)", default="Unit")
        num_units = IntPrompt.ask("Number of units (demand)", default=100)
        num_resources = IntPrompt.ask("Number of resources", default=10)
        resource_capacity = IntPrompt.ask("Capacity per resource per timeslot", default=10)
        num_unavailable = IntPrompt.ask("Number of unavailable resources", default=0)
        num_timeslots = IntPrompt.ask("Number of timeslots", default=4)
        timeslots = [f"Slot-{i+1}" for i in range(num_timeslots)]
        return build_custom_problem(
            title, unit_label, num_units, num_resources,
            resource_capacity, num_unavailable, timeslots,
        )


def choose_decision_mode():
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold magenta")
    table.add_column("Mode")
    table.add_column("Prioritizes")
    descriptions = {
        "balanced": "A well-rounded mix of all factors",
        "maximize_utilization": "Squeezing the most use out of available resources",
        "minimize_conflicts": "Leaving as few units unassigned as possible",
        "priority_first": "Serving high-priority units above all else",
        "fastest": "Raw decision speed",
    }
    for mode in DECISION_MODES:
        table.add_row(mode, descriptions[mode])
    console.print(table)
    return Prompt.ask("Choose a decision mode", choices=list(DECISION_MODES), default="balanced")


def render_module1(result):
    a = result.analysis
    c, r = a.constraints, a.resources

    left = Table(box=box.SIMPLE, show_header=False)
    left.add_row("Demand", str(c["demand"]))
    left.add_row("Capacity / slot", str(c["capacity_per_slot"]))
    left.add_row("Total capacity (all slots)", str(c["total_capacity_all_slots"]))
    left.add_row("Capacity deficit", str(c["capacity_deficit"]))
    left.add_row("Fully satisfiable?", "[green]Yes[/green]" if c["fully_satisfiable"] else "[red]No[/red]")

    right = Table(box=box.SIMPLE, show_header=False)
    right.add_row("Total resources", str(r["total_resources"]))
    right.add_row("Available resources", str(r["available_resources_count"]))
    right.add_row("Unavailable resources", str(r["unavailable_resources_count"]))
    right.add_row("Total available capacity/slot", str(r["total_available_capacity_per_slot"]))

    console.print(Panel.fit(left, title="[bold]Constraint Analysis[/bold]", border_style="cyan"))
    console.print(Panel.fit(right, title="[bold]Resource Analysis[/bold]", border_style="cyan"))

    if a.conflicts:
        conflict_table = Table(box=box.SIMPLE, header_style="bold red")
        conflict_table.add_column("Severity")
        conflict_table.add_column("Message")
        for conflict in a.conflicts:
            conflict_table.add_row(conflict["severity"], conflict["message"])
        console.print(Panel(conflict_table, title="[bold red]Conflicts Detected[/bold red]", border_style="red"))
    else:
        console.print(Panel("[green]No structural conflicts detected.[/green]", border_style="green"))


SHORT_NAMES = {
    "Greedy First-Fit": "Greedy",
    "Priority-Weighted Balanced": "Priority-Weighted",
    "Backtracking CSP": "Backtracking CSP",
    "A* Heuristic Search": "A* Search",
}


def render_ranking(result):
    table = Table(
        title="Module 2 + 3 \u2014 Generated Strategies, Ranked",
        box=box.ROUNDED, header_style="bold magenta", expand=True,
    )
    table.add_column("Rank", justify="right", width=5)
    table.add_column("Strategy", justify="left", no_wrap=True, min_width=18)
    table.add_column("Score", justify="right")
    table.add_column("Satisfaction", justify="right")
    table.add_column("Utilization", justify="right")
    table.add_column("Load Bal.", justify="right")
    table.add_column("Fairness", justify="right")
    table.add_column("Conflicts", justify="right")
    table.add_column("Time (ms)", justify="right")

    for row in result.performance_summary:
        rank_style = "bold gold3" if row["Rank"] == 1 else "white"
        short = SHORT_NAMES.get(row["Strategy"], row["Strategy"])
        table.add_row(
            f"[{rank_style}]#{row['Rank']}[/{rank_style}]",
            f"[{rank_style}]{short}[/{rank_style}]",
            f"{row['Score (%)']}%",
            f"{row['Satisfaction (%)']}%",
            f"{row['Utilization (%)']}%",
            f"{row['Load Balance (%)']}%",
            f"{row['Fairness (%)']}%",
            str(row["Conflicts"]),
            str(row["Time (ms)"]),
        )
    console.print(table)


def render_explanation(result):
    console.print(Panel(result.explanation, title="[bold]Module 4 \u2014 Explainable AI[/bold]", border_style="green", box=box.ROUNDED))


def render_repository_stats(engine):
    stats = engine.repository.get_stats()
    if stats["total_runs"] == 0:
        return
    table = Table(box=box.SIMPLE, show_header=False)
    table.add_row("Total runs recorded", str(stats["total_runs"]))
    table.add_row("Average winning score", f"{stats['average_winner_score']}%")
    table.add_row("Best score ever", f"{stats['best_score_ever']}%")
    table.add_row("Most frequent winning strategy", stats["most_frequent_winner"])
    console.print(Panel.fit(table, title="[bold]Knowledge Repository \u2014 All-Time Stats[/bold]", border_style="blue"))


def render_final_report(result):
    r = result.final_report
    header = Table(box=box.SIMPLE, show_header=False)
    header.add_row("Selected Algorithm", f"[bold gold3]{r.algorithm_name}[/bold gold3]")
    header.add_row("Optimization Score", f"{r.optimization_score:.1f}%")
    header.add_row("Resources Used", f"{r.resources_used} / {r.total_resources}")
    header.add_row("Unallocated Units", str(r.unallocated_count))
    header.add_row("Conflicts", str(r.conflicts_count))
    header.add_row("Completion", f"{r.completion_pct:.1f}%")
    console.print(Panel(header, title="[bold]Final Decision Report[/bold]", border_style="gold3", box=box.DOUBLE))

    alloc_table = Table(title="Final Resource Allocation", box=box.ROUNDED, header_style="bold cyan")
    alloc_table.add_column("Resource")
    alloc_table.add_column("Timeslot")
    alloc_table.add_column(f"{result.problem.unit_label}(s) Assigned")
    alloc_table.add_column("Count", justify="right")
    shown = r.allocation_lines[:40]
    for line in shown:
        alloc_table.add_row(line.resource, line.timeslot, line.unit_range_str(result.problem.unit_label), str(line.count))
    console.print(alloc_table)
    if len(r.allocation_lines) > 40:
        console.print(f"[dim]... and {len(r.allocation_lines) - 40} more allocation line(s) "
                       f"(full list saved in the knowledge base / report file)[/dim]")

    util_table = Table(title="Resource Utilization", box=box.SIMPLE, header_style="bold cyan")
    util_table.add_column("Resource")
    util_table.add_column("Utilization", justify="right")
    for resource, pct in r.resource_utilization.items():
        util_table.add_row(resource, f"{pct:.1f}%")
    console.print(util_table)

    status_lines = "\n".join(
        f"[green]\u2713[/green] {label}" if passed else f"[red]\u2717[/red] {label}"
        for label, passed in r.status_checks
    )
    console.print(Panel(status_lines, title="[bold]Final Status[/bold]", border_style="green"))


def main():
    print_banner()
    problem = choose_problem()
    mode = choose_decision_mode()

    console.print()
    thinking_steps([
        "Understanding problem...",
        "Analyzing constraints...",
        "Analyzing available resources...",
        "Detecting conflicts...",
        "Generating strategies (Greedy)...",
        "Generating strategies (Priority-Weighted)...",
        "Generating strategies (Backtracking CSP)...",
        "Generating strategies (A* Search)...",
        "Optimizing resource utilization...",
        "Scoring solutions adaptively...",
        "Ranking strategies...",
        "Generating explanation...",
        "Saving to knowledge repository...",
        "Rendering analytics dashboard...",
    ])

    engine = AthenaEngine()
    result = engine.run(problem, decision_mode=mode)

    console.print(Panel.fit(
        f"[bold]{problem.title}[/bold]\n"
        f"{problem.num_units} {problem.unit_label}(s)  |  "
        f"{len(problem.resources)} resources  |  {len(problem.timeslots)} timeslots  |  "
        f"decision mode: [magenta]{mode}[/magenta]",
        border_style="white",
    ))

    render_module1(result)
    render_ranking(result)
    render_final_report(result)
    render_explanation(result)
    render_repository_stats(engine)

    console.print()
    console.print(Panel(
        "\n".join(f"\u2022 {os.path.abspath(p)}" for p in result.chart_paths.values()),
        title="[bold]Analytics Charts Saved[/bold]", border_style="cyan",
    ))
    console.print(f"\n[dim]Run ID: {result.run_id}  |  Knowledge base: "
                  f"{os.path.abspath(engine.repository.path)}[/dim]\n")

    console.print("[bold magenta]ATHENA has completed its decision cycle: "
                  "Understand \u2192 Analyze \u2192 Plan \u2192 Optimize \u2192 Decide \u2192 Explain \u2192 Remember.[/bold magenta]\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted. Goodbye![/yellow]")
