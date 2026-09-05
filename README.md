# ATHENA
### Artificial Thinking Engine for Intelligent Planning, Optimization and Adaptive Decision Making

ATHENA is not a single-purpose predictor or classifier. Given a constraint-driven
planning problem (allocate N units to limited resources across timeslots),
it genuinely **understands** the problem, **generates multiple competing
strategies** using different real algorithms, **optimizes and adaptively
ranks** them, **explains** why the winner was chosen, **remembers** every
past decision, and **visualizes** the results.

```
User Problem
      ↓
Problem Understanding Engine   (Module 1)
      ↓
Constraint & Resource Analysis (Module 1)
      ↓
Strategic Planning Engine      (Module 2)  →  Greedy, Priority-Weighted,
      ↓                                        Backtracking CSP, A* Search
Solution Ranking + Optimization (Module 3)
      ↓
Adaptive Decision Engine       (Module 3)
      ↓
Explainable AI Engine          (Module 4)
      ↓
Knowledge Repository           (Module 4)
      ↓
Performance Analytics          (Module 4)
      ↓
Optimal Solution + Explanation
```

---

## 1. Project Structure

```
athena_project/
│
├── main.py                    # Rich-based terminal experience — start here
├── gui_app.py                  # CustomTkinter graphical dashboard
├── athena_engine.py             # Orchestrator — runs all 4 modules in sequence
├── scenarios.py                  # Document's Scenario 1 & 2, + custom problem builder
│
├── core/
│   ├── problem_model.py           # MODULE 1 — Constraint/Resource/Conflict analysis
│   ├── planning_engine.py         # MODULE 2 — Greedy, Priority, CSP, A* strategies
│   ├── optimization_engine.py     # MODULE 3 — Metrics, adaptive scoring, ranking
│   ├── explainable_ai.py          # MODULE 4a — "Why was this selected?" explanations
│   ├── knowledge_repository.py    # MODULE 4b — JSON-backed decision history
│   └── analytics.py               # MODULE 4c — matplotlib charts + performance table
│
├── data/                      # knowledge_base.json is created here at runtime
├── outputs/                   # generated charts (.png) are saved here
├── requirements.txt
└── README.md                  # this file
```

---

## 2. What Makes This "Intelligent" (Not a Toy)

| Requirement from the brief | How it's really implemented |
|---|---|
| Multiple intelligent strategies | 4 **different algorithms**, not 4 variations of the same loop: first-fit greedy, priority + load-balancing, true CSP backtracking with forward checking, and A* best-first search with an admissible heuristic |
| Adaptive decision making | 5 selectable scoring modes (`balanced`, `maximize_utilization`, `minimize_conflicts`, `priority_first`, `fastest`) that **genuinely change which strategy wins** — verified during development, not just labeled differently |
| Explainable AI | Generates a real natural-language paragraph comparing the winner against the runner-up on the specific metric that decided it |
| Knowledge repository | Actual JSON persistence across runs, with historical stats (average score, best score, most frequent winning strategy) |
| Performance analytics | 4 real matplotlib charts: strategy comparison, resource utilization, constraint heatmap, and score trend over time |

Every one of these was tested during development against the document's own
Scenario 1 (500 students / 20 labs / 50 unavailable systems / 6 timings) and
Scenario 2 (100 employees / 40 tasks), plus deliberately over-subscribed
edge cases, to confirm the numbers are real and the algorithms never violate
a resource's capacity.

---

## 3. Requirements

- **Python 3.9+** (3.10–3.12 recommended)
- Packages in `requirements.txt`: numpy, pandas, matplotlib, networkx, rich,
  customtkinter, Pillow

---

## 4. Setup in VS Code

### Step 1 — Install Python
Get it from [python.org](https://www.python.org/downloads/) if you don't have
it. On Windows, tick **"Add Python to PATH"** during install.

### Step 2 — Open the project folder
Unzip the project, then in VS Code: `File → Open Folder...` → select
`athena_project`.

### Step 3 — Open a terminal in VS Code
`` Ctrl+` `` (backtick), or `Terminal → New Terminal`.

### Step 4 — (Recommended) Create a virtual environment
```bash
python -m venv venv
```
Activate it:
- **Windows:** `venv\Scripts\activate`
- **macOS/Linux:** `source venv/bin/activate`

VS Code may prompt "Select this interpreter for the workspace" — click Yes.

### Step 5 — Install dependencies
```bash
pip install -r requirements.txt
```

---

## 5. Running ATHENA

### Terminal experience (recommended first run)
```bash
python main.py
```
You'll get an interactive menu: choose Scenario 1, Scenario 2, or define a
custom problem, then choose a decision mode. ATHENA will visibly step
through its pipeline (understanding → planning → optimizing → explaining),
then print:
- Constraint & resource analysis
- A ranked strategy comparison table
- A plain-English explanation of the winning strategy
- Knowledge repository stats
- Paths to the generated chart images (saved in `outputs/`)

### Graphical dashboard
```bash
python gui_app.py
```
A 6-tab desktop window: **Problem Setup** (choose/define a problem and run),
**Analysis**, **Solutions**, **Explainability**, **Analytics** (embedded
charts), and **Knowledge Base** (full run history).

### Running an individual module directly (for testing/demo)
Every module file has its own self-test you can run in isolation:
```bash
python -m core.problem_model
python -m core.planning_engine
python -m core.optimization_engine
python -m core.explainable_ai
python -m core.knowledge_repository
python -m core.analytics
python athena_engine.py
```

---

## 6. Troubleshooting

**Every file works independently.** Every file in this project (including
everything inside `core/`) can be run directly, on its own, from any working
directory, or via VS Code's "Run Python File" button — including files
opened straight from inside the `core/` folder. Each file carries a small
path bootstrap at the top that locates the project root and registers it,
so `import core.xxx` always resolves correctly no matter how the file was
launched, and `data/`, `outputs/` always resolve to the actual project
folders rather than wherever your terminal happened to be sitting.

If you still see `ModuleNotFoundError: No module named 'core'`, it almost
always means the `core/` folder was renamed or moved. Make sure the folder
structure matches Section 1 exactly, with `core/` sitting directly inside
the project root next to `main.py`.

**Recommended way to run this project:** open the whole `athena_project`
folder in VS Code (`File → Open Folder`, not just individual files), then
run `main.py` or `gui_app.py` from an integrated terminal (`` Ctrl+` ``) with
`python main.py` / `python gui_app.py`. Files inside `core/` are library
modules — you won't normally need to run them directly, though you now can
for testing (`python -m core.planning_engine`, or just opening the file and
hitting Run, both work).

---

## 7. The Four Planning Strategies, Explained

1. **Greedy First-Fit** — assigns each unit to the first slot with room.
   Fast baseline every other strategy is measured against.
2. **Priority-Weighted Balanced** — processes highest-priority units first,
   always picking the slot with the *most* remaining capacity (load
   balancing). Well suited to workforce/task scheduling.
3. **Backtracking CSP** — a genuine constraint-satisfaction search: each
   unit is a variable, each open slot is a domain value, with forward
   checking pruning slots that hit zero capacity. Bounded by a node budget
   so it stays fast even on large inputs (a standard, honest compromise —
   not a silent approximation).
4. **A\* Heuristic Search** — treats scheduling as a shortest-path problem
   (`g` = unassigned units so far, `h` = units not yet considered, an
   admissible lower bound), expanding the most promising partial schedule
   first. Also node-budgeted for tractability.

## 8. The Five Decision Modes

| Mode | Prioritizes |
|---|---|
| `balanced` | A well-rounded mix of all factors |
| `maximize_utilization` | Squeezing the most use out of available resources |
| `minimize_conflicts` | Leaving as few units unassigned as possible |
| `priority_first` | Serving high-priority units above all else |
| `fastest` | Raw decision speed |

Switching modes **does not re-run the search** — it re-scores the same
candidate solutions with different weights, which is what makes the
decision-making "adaptive" rather than just re-computed from scratch.

---

## 9. Talking Points for Your Review

1. **It's not one algorithm** — show the strategy comparison table and point
   out that Backtracking CSP and A* are genuinely different search
   paradigms from the greedy baseline, not cosmetic renames.
2. **Adaptivity is real** — run the same problem twice with different
   decision modes (e.g. `balanced` vs `priority_first`) and show the winner
   can change.
3. **Explainability is specific** — the explanation names the *exact*
   metric that separated the winner from the runner-up, not a generic
   "this was best" statement.
4. **The knowledge repository grows** — run ATHENA a few times before your
   demo so the "Score Trend Across Past Runs" chart has multiple points.
5. **Everything is measured, not claimed** — nodes explored, execution time,
   load balance, and priority fairness are all computed from the actual
   generated assignments, not hardcoded.

---

## 10. Extending ATHENA

- Add a new strategy: implement a class with a `.solve(problem) -> Solution`
  method in `core/planning_engine.py`, then add it to
  `SolutionGenerator.strategies`.
- Add a new decision mode: add a weight vector to `DECISION_MODES` in
  `core/optimization_engine.py`.
- Add a new scenario: add a builder function to `scenarios.py` following the
  pattern of `scenario_lab_allocation()`.
