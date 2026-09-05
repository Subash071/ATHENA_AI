"""
gui_app.py
----------------------------------------------------------------------
ATHENA — Interactive Desktop Dashboard (CustomTkinter)

Run this file for the graphical experience:
    python gui_app.py

Tabs:
    1. Problem Setup   - choose a scenario or build a custom problem
    2. Analysis        - Module 1 output (constraints, resources, conflicts)
    3. Solutions       - Module 2 + 3 ranked strategy table
    4. Explainability  - Module 4 plain-English explanation
    5. Analytics       - embedded charts (strategy comparison, utilization, heatmap)
    6. Knowledge Base  - history of every past run
"""

import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import threading

# ---- Friendly dependency check ----------------------------------------
# Two distinct failure modes are common here:
#  1. tkinter itself missing (it's a SYSTEM package, not something pip
#     installs) — common on minimal Linux installs.
#  2. customtkinter / matplotlib / Pillow not installed via requirements.txt.
try:
    import tkinter  # noqa: F401 — presence check only
except ModuleNotFoundError:
    print("=" * 70)
    print("ATHENA's GUI could not start: Python's built-in 'tkinter' module")
    print("is missing. This is a SYSTEM package, not something 'pip install'")
    print("can add. Install it with:")
    print("    Windows/macOS: reinstall Python from python.org and make sure")
    print("                   'tcl/tk' is checked during setup (it usually is")
    print("                   by default).")
    print("    Ubuntu/Debian: sudo apt-get install python3-tk")
    print("=" * 70)
    raise SystemExit(1)

try:
    import customtkinter as ctk
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import matplotlib.pyplot as plt
    from PIL import Image
except ModuleNotFoundError as e:
    import sys as _sys
    print("=" * 70)
    print("ATHENA's GUI could not start because a required package is missing:")
    print(f"    {e}")
    print()
    print("Fix: open a terminal in this project folder and run:")
    print(f"    {_sys.executable} -m pip install -r requirements.txt")
    print("=" * 70)
    raise SystemExit(1)

from athena_engine import AthenaEngine
from scenarios import scenario_lab_allocation, scenario_workforce_allocation, build_custom_problem
from core.optimization_engine import DECISION_MODES

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

NAVY = "#141A33"
PANEL = "#1E2547"
PURPLE = "#8B5CF6"
TEAL = "#2DD4BF"
ORANGE = "#FF8A3D"
TEXT_MUTED = "#9AA3C7"


class AthenaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ATHENA \u2014 Artificial Thinking Engine")
        self.geometry("1200x780")
        self.minsize(900, 560)
        self.configure(fg_color=NAVY)

        self.engine = AthenaEngine()
        self.result = None

        self._build_header()
        self._build_tabs()

    # ---------------- Header ----------------
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=0, height=80)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="ATHENA", font=ctk.CTkFont(family="Georgia", size=28, weight="bold"),
            text_color=PURPLE,
        ).pack(side="left", padx=(24, 8), pady=10)
        ctk.CTkLabel(
            header, text="Artificial Thinking Engine for Intelligent Planning,\n"
                          "Optimization and Adaptive Decision Making",
            font=ctk.CTkFont(size=11), text_color=TEXT_MUTED, justify="left",
        ).pack(side="left", padx=8)

    # ---------------- Tabs ----------------
    def _build_tabs(self):
        self.tabs = ctk.CTkTabview(self, fg_color=PANEL, segmented_button_selected_color=PURPLE)
        self.tabs.pack(fill="both", expand=True, padx=14, pady=14)

        for name in ["Problem Setup", "Analysis", "Solutions", "Decision Report", "Explainability", "Analytics", "Knowledge Base"]:
            self.tabs.add(name)

        self._build_setup_tab(self.tabs.tab("Problem Setup"))
        self._build_analysis_tab(self.tabs.tab("Analysis"))
        self._build_solutions_tab(self.tabs.tab("Solutions"))
        self._build_decision_report_tab(self.tabs.tab("Decision Report"))
        self._build_explain_tab(self.tabs.tab("Explainability"))
        self._build_analytics_tab(self.tabs.tab("Analytics"))
        self._build_knowledge_tab(self.tabs.tab("Knowledge Base"))

    # ---------------- Tab 1: Problem Setup ----------------
    def _build_setup_tab(self, tab):
        left = ctk.CTkScrollableFrame(tab, fg_color="transparent", width=420)
        left.pack(side="left", fill="both", expand=False, padx=16, pady=16)

        ctk.CTkLabel(left, text="1. Choose a Problem", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 8))
        self.scenario_var = ctk.StringVar(value="lab")
        for value, label in [
            ("lab", "Scenario 1 \u2014 Laboratory Allocation (500 students, 20 labs)"),
            ("workforce", "Scenario 2 \u2014 Workforce Task Allocation (100 employees, 40 tasks)"),
            ("custom", "Custom Problem (define below)"),
        ]:
            ctk.CTkRadioButton(left, text=label, variable=self.scenario_var, value=value).pack(anchor="w", pady=4)

        ctk.CTkLabel(left, text="\n2. Custom Problem Parameters", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(12, 8))

        self.entries = {}
        fields = [
            ("title", "Problem Title", "Custom Allocation Problem"),
            ("unit_label", "Unit Label", "Unit"),
            ("num_units", "Number of Units", "100"),
            ("num_resources", "Number of Resources", "10"),
            ("resource_capacity", "Capacity per Resource", "10"),
            ("num_unavailable", "Unavailable Resources", "0"),
            ("num_timeslots", "Number of Timeslots", "4"),
        ]
        for key, label, default in fields:
            row = ctk.CTkFrame(left, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=label, width=170, anchor="w").pack(side="left")
            entry = ctk.CTkEntry(row, width=140)
            entry.insert(0, default)
            entry.pack(side="left")
            self.entries[key] = entry

        ctk.CTkLabel(left, text="\n3. Decision Mode", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(12, 8))
        self.mode_var = ctk.StringVar(value="balanced")
        mode_menu = ctk.CTkOptionMenu(left, variable=self.mode_var, values=list(DECISION_MODES.keys()), width=260)
        mode_menu.pack(anchor="w")

        self.run_button = ctk.CTkButton(
            left, text="\u25b6  Run ATHENA", command=self._run_athena_async,
            fg_color=PURPLE, hover_color="#7C3AED", height=42, width=260,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.run_button.pack(anchor="w", pady=(20, 6))

        self.status_label = ctk.CTkLabel(left, text="Ready.", text_color=TEXT_MUTED)
        self.status_label.pack(anchor="w")

        # Right side — live pipeline log
        right = ctk.CTkFrame(tab, fg_color=NAVY, corner_radius=10)
        right.pack(side="left", fill="both", expand=True, padx=16, pady=16)
        ctk.CTkLabel(right, text="Pipeline Log", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=12, pady=(12, 4))
        self.log_box = ctk.CTkTextbox(right, fg_color="#0F1430", text_color=TEAL, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_box.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def _log(self, message):
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")

    # ---------------- Tab 2: Analysis ----------------
    def _build_analysis_tab(self, tab):
        self.analysis_box = ctk.CTkTextbox(tab, font=ctk.CTkFont(family="Consolas", size=13))
        self.analysis_box.pack(fill="both", expand=True, padx=12, pady=12)
        self.analysis_box.insert("end", "Run ATHENA from the 'Problem Setup' tab to see Module 1 analysis here.")
        self.analysis_box.configure(state="disabled")

    # ---------------- Tab 3: Solutions ----------------
    def _build_solutions_tab(self, tab):
        self.solutions_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.solutions_frame.pack(fill="both", expand=True, padx=12, pady=12)
        ctk.CTkLabel(self.solutions_frame, text="Run ATHENA to see ranked strategies here.",
                     text_color=TEXT_MUTED).pack(pady=20)

    # ---------------- Tab 3b: Decision Report (the actual allocation) ----------------
    def _build_decision_report_tab(self, tab):
        self.decision_scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.decision_scroll.pack(fill="both", expand=True, padx=12, pady=12)
        ctk.CTkLabel(
            self.decision_scroll,
            text="Run ATHENA to see the actual final allocation \u2014 which unit went "
                 "to which resource, in which timeslot.",
            text_color=TEXT_MUTED, wraplength=800, justify="left",
        ).pack(pady=20, anchor="w")

    # ---------------- Tab 4: Explainability ----------------
    def _build_explain_tab(self, tab):
        self.explain_box = ctk.CTkTextbox(tab, font=ctk.CTkFont(size=14))
        self.explain_box.pack(fill="both", expand=True, padx=12, pady=12)
        self.explain_box.insert("end", "Run ATHENA to see why a strategy was selected.")
        self.explain_box.configure(state="disabled")

    # ---------------- Tab 5: Analytics ----------------
    def _build_analytics_tab(self, tab):
        self.analytics_scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.analytics_scroll.pack(fill="both", expand=True, padx=12, pady=12)
        ctk.CTkLabel(self.analytics_scroll, text="Run ATHENA to generate charts here.",
                     text_color=TEXT_MUTED).pack(pady=20)

    # ---------------- Tab 6: Knowledge Base ----------------
    def _build_knowledge_tab(self, tab):
        self.knowledge_box = ctk.CTkTextbox(tab, font=ctk.CTkFont(family="Consolas", size=12))
        self.knowledge_box.pack(fill="both", expand=True, padx=12, pady=12)
        self._refresh_knowledge_tab()

    def _refresh_knowledge_tab(self):
        self.knowledge_box.configure(state="normal")
        self.knowledge_box.delete("1.0", "end")
        history = self.engine.repository.load_history()
        stats = self.engine.repository.get_stats()
        if stats.get("total_runs", 0) == 0:
            self.knowledge_box.insert("end", "No runs recorded yet.")
        else:
            self.knowledge_box.insert("end", f"Total runs: {stats['total_runs']}\n")
            self.knowledge_box.insert("end", f"Average winning score: {stats['average_winner_score']}%\n")
            self.knowledge_box.insert("end", f"Best score ever: {stats['best_score_ever']}%\n")
            self.knowledge_box.insert("end", f"Most frequent winner: {stats['most_frequent_winner']}\n\n")
            self.knowledge_box.insert("end", "-" * 90 + "\n")
            for run in reversed(history):
                self.knowledge_box.insert(
                    "end",
                    f"[{run['timestamp']}] {run['problem_title']} | "
                    f"winner={run['winner_strategy']} ({run['winner_score']}%) | "
                    f"mode={run['decision_mode']} | run_id={run['run_id']}\n"
                )
        self.knowledge_box.configure(state="disabled")

    # ---------------- Run pipeline ----------------
    def _get_problem(self):
        choice = self.scenario_var.get()
        if choice == "lab":
            return scenario_lab_allocation()
        elif choice == "workforce":
            return scenario_workforce_allocation()
        else:
            e = self.entries
            timeslots = [f"Slot-{i+1}" for i in range(int(e["num_timeslots"].get()))]
            return build_custom_problem(
                title=e["title"].get(),
                unit_label=e["unit_label"].get(),
                num_units=int(e["num_units"].get()),
                num_resources=int(e["num_resources"].get()),
                resource_capacity=int(e["resource_capacity"].get()),
                num_unavailable=int(e["num_unavailable"].get()),
                timeslots=timeslots,
            )

    def _run_athena_async(self):
        self.run_button.configure(state="disabled", text="Running...")
        self.status_label.configure(text="Running ATHENA pipeline...")
        self.log_box.delete("1.0", "end")
        thread = threading.Thread(target=self._run_athena, daemon=True)
        thread.start()

    def _run_athena(self):
        try:
            problem = self._get_problem()
            steps = [
                "Understanding problem...", "Analyzing constraints...", "Analyzing resources...",
                "Detecting conflicts...", "Generating Greedy strategy...",
                "Generating Priority-Weighted strategy...", "Generating Backtracking CSP strategy...",
                "Generating A* Search strategy...", "Optimizing & scoring solutions...",
                "Ranking strategies...", "Generating explanation...",
                "Saving to knowledge repository...", "Rendering analytics charts...",
            ]
            for step in steps:
                self.after(0, self._log, f"\u2022 {step}")

            mode = self.mode_var.get()
            result = self.engine.run(problem, decision_mode=mode)
            self.result = result

            self.after(0, self._populate_results, result)
        except Exception as e:
            import traceback
            full_trace = traceback.format_exc()
            self.after(0, self._show_error, str(e), full_trace)
        finally:
            self.after(0, self.run_button.configure, {"state": "normal", "text": "\u25b6  Run ATHENA"})

    def _show_error(self, short_message, full_trace):
        """Errors must never be silently buried in a log box on a tab the
        user isn't looking at — pop a real modal dialog, log the full
        traceback for debugging, and jump back to where the log lives."""
        from tkinter import messagebox

        self._log(f"\nERROR: {short_message}\n{'-'*60}\n{full_trace}")
        self.status_label.configure(text=f"Error: {short_message}")
        self.tabs.set("Problem Setup")

        hint = ""
        if "No module named" in short_message:
            missing_pkg = short_message.split("'")[1] if "'" in short_message else "a required package"
            hint = (
                f"\n\nThis usually means dependencies haven't been installed yet.\n"
                f"Open a terminal in the project folder and run:\n\n"
                f"    pip install -r requirements.txt\n\n"
                f"(missing package: {missing_pkg})"
            )
        messagebox.showerror("ATHENA \u2014 Run Failed", f"{short_message}{hint}")

    # ---------------- Populate UI after a run ----------------
    def _populate_results(self, result):
        self.status_label.configure(text=f"Done. Run ID: {result.run_id}")
        self._log("\nATHENA has completed its decision cycle.")

        # Analysis tab
        a = result.analysis
        c, r = a.constraints, a.resources
        text = (
            f"PROBLEM: {result.problem.title}\n"
            f"{'=' * 70}\n\n"
            f"CONSTRAINT ANALYSIS\n"
            f"  Demand: {c['demand']}\n"
            f"  Capacity per slot: {c['capacity_per_slot']}\n"
            f"  Total capacity (all slots): {c['total_capacity_all_slots']}\n"
            f"  Capacity deficit: {c['capacity_deficit']}\n"
            f"  Fully satisfiable: {c['fully_satisfiable']}\n\n"
            f"RESOURCE ANALYSIS\n"
            f"  Total resources: {r['total_resources']}\n"
            f"  Available resources: {r['available_resources_count']}\n"
            f"  Unavailable resources: {r['unavailable_resources_count']}\n"
            f"  Total available capacity/slot: {r['total_available_capacity_per_slot']}\n\n"
            f"CONFLICTS DETECTED: {len(a.conflicts)}\n"
        )
        for conflict in a.conflicts:
            text += f"  [{conflict['severity']}] {conflict['message']}\n"
        if not a.conflicts:
            text += "  None \u2014 problem is structurally clean.\n"

        self.analysis_box.configure(state="normal")
        self.analysis_box.delete("1.0", "end")
        self.analysis_box.insert("end", text)
        self.analysis_box.configure(state="disabled")

        # Solutions tab
        for widget in self.solutions_frame.winfo_children():
            widget.destroy()
        for row in result.performance_summary:
            is_winner = row["Rank"] == 1
            card = ctk.CTkFrame(
                self.solutions_frame, fg_color=(PURPLE if is_winner else NAVY), corner_radius=10,
            )
            card.pack(fill="x", pady=6, padx=4)
            header = f"#{row['Rank']}  {row['Strategy']}" + ("  \u2605 WINNER" if is_winner else "")
            ctk.CTkLabel(card, text=header, font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=14, pady=(10, 2))
            details = (
                f"Score: {row['Score (%)']}%   |   Satisfaction: {row['Satisfaction (%)']}%   |   "
                f"Utilization: {row['Utilization (%)']}%   |   Load Balance: {row['Load Balance (%)']}%   |   "
                f"Fairness: {row['Fairness (%)']}%   |   Conflicts: {row['Conflicts']}   |   Time: {row['Time (ms)']}ms"
            )
            ctk.CTkLabel(card, text=details, text_color=TEXT_MUTED, font=ctk.CTkFont(size=12)).pack(anchor="w", padx=14, pady=(0, 10))

        # Decision Report tab — the actual final allocation, not just the algorithm comparison
        for widget in self.decision_scroll.winfo_children():
            widget.destroy()
        r = result.final_report

        summary_card = ctk.CTkFrame(self.decision_scroll, fg_color=PURPLE, corner_radius=10)
        summary_card.pack(fill="x", pady=(0, 12), padx=4)
        ctk.CTkLabel(summary_card, text="FINAL DECISION REPORT", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=16, pady=(12, 4))
        summary_text = (
            f"Selected Algorithm: {r.algorithm_name}\n"
            f"Optimization Score: {r.optimization_score:.1f}%\n"
            f"Resources Used: {r.resources_used} / {r.total_resources}\n"
            f"Unallocated Units: {r.unallocated_count}\n"
            f"Conflicts: {r.conflicts_count}\n"
            f"Completion: {r.completion_pct:.1f}%"
        )
        ctk.CTkLabel(summary_card, text=summary_text, justify="left", font=ctk.CTkFont(size=13)).pack(anchor="w", padx=16, pady=(0, 14))

        ctk.CTkLabel(self.decision_scroll, text="Final Resource Allocation",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", pady=(6, 6))
        alloc_frame = ctk.CTkFrame(self.decision_scroll, fg_color=NAVY, corner_radius=8)
        alloc_frame.pack(fill="x", pady=(0, 14), padx=4)
        shown_lines = r.allocation_lines[:60]
        alloc_text = "\n".join(
            f"{line.resource:<12} @ {line.timeslot:<14} \u2192 {line.unit_range_str(result.problem.unit_label)}"
            for line in shown_lines
        )
        if len(r.allocation_lines) > 60:
            alloc_text += f"\n... and {len(r.allocation_lines) - 60} more allocation line(s)"
        alloc_box = ctk.CTkTextbox(alloc_frame, height=min(400, 24 * max(1, len(shown_lines))), font=ctk.CTkFont(family="Consolas", size=12))
        alloc_box.pack(fill="both", expand=True, padx=10, pady=10)
        alloc_box.insert("end", alloc_text or "No units were allocated.")
        alloc_box.configure(state="disabled")

        ctk.CTkLabel(self.decision_scroll, text="Resource Utilization",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", pady=(6, 6))
        util_frame = ctk.CTkFrame(self.decision_scroll, fg_color=NAVY, corner_radius=8)
        util_frame.pack(fill="x", pady=(0, 14), padx=4)
        for resource, pct in r.resource_utilization.items():
            row_f = ctk.CTkFrame(util_frame, fg_color="transparent")
            row_f.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(row_f, text=resource, width=140, anchor="w").pack(side="left")
            bar = ctk.CTkProgressBar(row_f, width=300)
            bar.set(pct / 100)
            bar.pack(side="left", padx=8)
            ctk.CTkLabel(row_f, text=f"{pct:.1f}%").pack(side="left")

        ctk.CTkLabel(self.decision_scroll, text="Final Status",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", pady=(6, 6))
        status_frame = ctk.CTkFrame(self.decision_scroll, fg_color=NAVY, corner_radius=8)
        status_frame.pack(fill="x", pady=(0, 14), padx=4)
        for label, passed in r.status_checks:
            mark = "\u2713" if passed else "\u2717"
            color = TEAL if passed else "#FF6B6B"
            ctk.CTkLabel(status_frame, text=f"{mark}  {label}", text_color=color,
                         font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=14, pady=4)

        # Explainability tab
        self.explain_box.configure(state="normal")
        self.explain_box.delete("1.0", "end")
        self.explain_box.insert("end", result.explanation)
        self.explain_box.configure(state="disabled")

        # Analytics tab
        for widget in self.analytics_scroll.winfo_children():
            widget.destroy()
        for chart_name, path in result.chart_paths.items():
            if os.path.exists(path):
                img = Image.open(path)
                w, h = img.size
                display_w = 900
                display_h = int(h * (display_w / w))
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(display_w, display_h))
                label = ctk.CTkLabel(self.analytics_scroll, image=ctk_img, text="")
                label.pack(pady=10)

        # Knowledge base tab
        self._refresh_knowledge_tab()


if __name__ == "__main__":
    app = AthenaApp()
    app.mainloop()
