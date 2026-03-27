#!/usr/bin/env python3
"""Regenerate results.db by running all algorithms on all grids.

Usage:
    python3 regenerate_benchmarks.py
    python3 regenerate_benchmarks.py --skip-brute   # skip brute force (slow, 30s timeout)
"""

import os
import sys
import time

from script import SudokuGrid
from benchmark import run_benchmark, DB_PATH

GRIDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "grids")

# Algorithm registry: (name, method_name)
ALGORITHMS = [
    ("brute", "solve_brute_force"),
    ("backtrack", "solve_backtracking"),
    ("backtrack_mrv", "solve_backtracking_mrv"),
    ("propagation", "solve_propagation"),
    ("propagation_mrv", "solve_propagation_mrv"),
]


def main():
    skip_brute = "--skip-brute" in sys.argv

    grid_files = sorted(
        f for f in os.listdir(GRIDS_DIR) if f.endswith(".txt")
    )

    if not grid_files:
        print("No grid files found in", GRIDS_DIR)
        sys.exit(1)

    print(f"Database: {DB_PATH}")
    print(f"Grids: {len(grid_files)} | Algorithms: {len(ALGORITHMS)}")
    if skip_brute:
        print("(skipping brute force)")
    print()

    total_start = time.perf_counter()

    for grid_file in grid_files:
        filepath = os.path.join(GRIDS_DIR, grid_file)
        print(f"--- {grid_file} ---")

        for algo_name, method_name in ALGORITHMS:
            if skip_brute and algo_name == "brute":
                print(f"  {algo_name:20s} [SKIPPED]")
                continue

            print(f"  {algo_name:20s} running...", flush=True)

            # Reload a fresh grid for each algorithm
            sg = SudokuGrid(filepath)
            solve_func = getattr(sg, method_name)

            result = run_benchmark(sg.original, algo_name, solve_func, grid_file)

            status = "OK" if result["solved"] else "FAIL"
            print(
                f"  {algo_name:20s} {result['time_ms']:10.2f} ms  "
                f"{result['iterations']:8d} iter  [{status}]"
            )

        print()

    elapsed = time.perf_counter() - total_start
    print(f"Done in {elapsed:.2f}s. Results saved to {DB_PATH}")


if __name__ == "__main__":
    main()
