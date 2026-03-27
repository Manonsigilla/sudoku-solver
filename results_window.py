# =============================================================================
# results_window.py -- Results display with matplotlib charts
# =============================================================================
# Shows benchmark results stored in SQLite as charts:
# - Grouped bars: time per algorithm per grid
# - Grouped bars: iterations per algorithm per grid
# - Curves: time vs difficulty (number of empty cells)
# - LaTeX algorithmic complexity formulas
# =============================================================================

import os
import sys
import subprocess
import tempfile
import matplotlib.pyplot as plt
import numpy as np
from benchmark import get_latest_results


# Colors for each algorithm (consistent with the pygame display)
ALGO_COLORS = {
    "brute": "#e74c3c",           # Red
    "backtrack": "#3498db",       # Blue
    "backtrack_mrv": "#2ecc71",   # Green
    "propagation": "#9b59b6",     # Purple
    "propagation_mrv": "#f39c12", # Orange
}

# Readable names for legends
ALGO_LABELS = {
    "brute": "Brute Force",
    "backtrack": "Backtracking",
    "backtrack_mrv": "Backtrack+MRV",
    "propagation": "AC-3",
    "propagation_mrv": "AC-3+MRV",
}

# Display order for algorithms
ALGO_ORDER = ["brute", "backtrack", "backtrack_mrv", "propagation", "propagation_mrv"]


def _plot_time_bars(ax, results):
    """Grouped bars: execution time (ms) per algorithm, grouped by grid.
    Each group of bars represents a grid, each bar an algorithm."""
    # Organize data by grid and by algorithm
    grids = sorted(set(r["grid_file"] for r in results))
    algos = [a for a in ALGO_ORDER if any(r["algo"] == a for r in results)]

    if not grids or not algos:
        ax.text(0.5, 0.5, "No data", ha="center", va="center",
                transform=ax.transAxes, fontsize=12)
        return

    # Bar positions
    x = np.arange(len(grids))
    width = 0.8 / len(algos)  # Width of each bar

    for i, algo in enumerate(algos):
        times = []
        for grid in grids:
            # Find the result for this (grid, algo) pair
            matching = [r for r in results
                        if r["grid_file"] == grid and r["algo"] == algo]
            times.append(matching[0]["time_ms"] if matching else 0)
        # Draw bars for this algorithm
        offset = (i - len(algos) / 2 + 0.5) * width
        ax.bar(x + offset, times, width, label=ALGO_LABELS.get(algo, algo),
               color=ALGO_COLORS.get(algo, "#999"))

    ax.set_xlabel("Grid")
    ax.set_ylabel("Time (ms)")
    ax.set_title("Execution time per algorithm")
    ax.set_xticks(x)
    ax.set_xticklabels([g.replace(".txt", "") for g in grids], rotation=45, ha="right")
    ax.legend(fontsize=8)
    ax.set_yscale("log")  # Log scale because the gaps are huge


def _plot_iteration_bars(ax, results):
    """Grouped bars: number of iterations per algorithm, grouped by grid."""
    grids = sorted(set(r["grid_file"] for r in results))
    algos = [a for a in ALGO_ORDER if any(r["algo"] == a for r in results)]

    if not grids or not algos:
        ax.text(0.5, 0.5, "No data", ha="center", va="center",
                transform=ax.transAxes, fontsize=12)
        return

    x = np.arange(len(grids))
    width = 0.8 / len(algos)

    for i, algo in enumerate(algos):
        iterations = []
        for grid in grids:
            matching = [r for r in results
                        if r["grid_file"] == grid and r["algo"] == algo]
            iterations.append(matching[0]["iterations"] if matching else 0)
        offset = (i - len(algos) / 2 + 0.5) * width
        ax.bar(x + offset, iterations, width, label=ALGO_LABELS.get(algo, algo),
               color=ALGO_COLORS.get(algo, "#999"))

    ax.set_xlabel("Grid")
    ax.set_ylabel("Iterations")
    ax.set_title("Number of iterations per algorithm")
    ax.set_xticks(x)
    ax.set_xticklabels([g.replace(".txt", "") for g in grids], rotation=45, ha="right")
    ax.legend(fontsize=8)
    ax.set_yscale("log")  # Log scale


def _plot_time_vs_difficulty(ax, results):
    """Curves: execution time vs number of empty cells (difficulty).
    One line per algorithm, X axis is the number of empty cells."""
    algos = [a for a in ALGO_ORDER if any(r["algo"] == a for r in results)]

    if not algos:
        ax.text(0.5, 0.5, "No data", ha="center", va="center",
                transform=ax.transAxes, fontsize=12)
        return

    for algo in algos:
        # Filter results for this algorithm
        algo_results = [r for r in results if r["algo"] == algo]
        if not algo_results:
            continue
        # Sort by number of empty cells (difficulty)
        algo_results.sort(key=lambda r: r["cells_empty"])
        x_vals = [r["cells_empty"] for r in algo_results]
        y_vals = [r["time_ms"] for r in algo_results]
        ax.plot(x_vals, y_vals, marker="o", linewidth=2, markersize=5,
                label=ALGO_LABELS.get(algo, algo),
                color=ALGO_COLORS.get(algo, "#999"))

    ax.set_xlabel("Empty cells (difficulty)")
    ax.set_ylabel("Time (ms)")
    ax.set_title("Time vs grid difficulty")
    ax.legend(fontsize=8)
    ax.set_yscale("log")  # Log scale to see small values


def _plot_formulas(ax):
    """Display algorithmic complexity formulas in LaTeX.
    Uses matplotlib's native LaTeX rendering."""
    ax.axis("off")
    ax.set_title("Algorithmic complexity", fontsize=14, fontweight="bold")

    # List of formulas: (algo name, complexity, key formula)
    formulas = [
        ("Brute Force",
         r"$O(9^m)$, $m$ = empty cells",
         r"Validation only on complete grid"),
        ("Backtracking",
         r"$O(9^m)$ worst case",
         r"Pruning: $\mathrm{is\_valid}$ before placement"),
        ("Backtracking + MRV",
         r"$O(9^m)$ worst case, better in practice",
         r"Heuristic: $\min(|\mathrm{candidates}|)$"),
        ("AC-3 Propagation",
         r"$O(d \cdot n)$, $d$ = domain, $n$ = cells",
         r"Naked: $|D(c)|=1$ / Hidden: unique in unit"),
        ("AC-3 + MRV",
         r"$O(d \cdot n)$ + residual search",
         r"Propagation + MRV backtracking if stalled"),
    ]

    # Position formulas vertically
    y = 0.92
    for name, complexity, detail in formulas:
        ax.text(0.02, y, name, fontsize=11, fontweight="bold",
                transform=ax.transAxes, verticalalignment="top",
                color=ALGO_COLORS.get(name.lower().replace(" ", "_").replace("+", "").replace("ac-3", "propagation").strip(), "#333"))
        ax.text(0.02, y - 0.05, complexity, fontsize=10,
                transform=ax.transAxes, verticalalignment="top")
        ax.text(0.02, y - 0.10, detail, fontsize=9, color="#666",
                transform=ax.transAxes, verticalalignment="top")
        y -= 0.20


def show_results():
    """Open a results window with 4 matplotlib subplots.
    Loads data from SQLite (the most recent run per grid/algo pair).
    Saves chart to a temp file and opens with the system viewer to
    avoid conflicts with Pygame's display ownership."""
    results = get_latest_results()

    if not results:
        print("[WARN] No benchmark results in database. "
              "Run first: python3 main.py grids/grid_1.txt --benchmark")
        return

    # Create the figure with 4 subplots (2x2 layout)
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Sudoku Solver -- Comparative Results", fontsize=16, fontweight="bold")

    # Top-left: time bars
    _plot_time_bars(axes[0, 0], results)
    # Top-right: iteration bars
    _plot_iteration_bars(axes[0, 1], results)
    # Bottom-left: evolution curves
    _plot_time_vs_difficulty(axes[1, 0], results)
    # Bottom-right: LaTeX formulas
    _plot_formulas(axes[1, 1])

    plt.tight_layout()

    # Save chart to temp file and open with system viewer
    # (plt.show() conflicts with Pygame's display ownership)
    tmp_path = os.path.join(tempfile.gettempdir(), "sudoku_results.png")
    fig.savefig(tmp_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("[OK] Results chart saved to {}".format(tmp_path))

    # Open with the system default image viewer (cross-platform)
    try:
        if sys.platform == "win32":
            os.startfile(tmp_path)  # Windows
        else:
            subprocess.Popen(["xdg-open", tmp_path])  # Linux/Mac
    except (FileNotFoundError, AttributeError):
        print("[WARN] Could not open image viewer. Open manually: " + tmp_path)
