#!/usr/bin/env python3
"""Regenerate results.db by running all algorithms on all grids.

Usage:
    For python 3.8+:
    python3 regenerate_benchmarks.py
    python3 regenerate_benchmarks.py --skip-brute   # skip brute force (slow, 30s timeout)
    For anaconda env:
    python regenerate_benchmarks.py
    python regenerate_benchmarks.py --skip-brute
"""

# =============================================================================
# CLI tool to re-run all algorithms on all grids and populate results.db
# =============================================================================

import os
import sys
import time

from solver import run_all_benchmarks, DB_PATH, ALGORITHMS

GRIDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "grids")


def main():
    """Run all algorithms on every grid file and save results to SQLite."""
    skip_brute = "--skip-brute" in sys.argv

    print(f"Database: {DB_PATH}")
    print(f"Algorithms: {len(ALGORITHMS)}")
    if skip_brute:
        print("(skipping brute force)")
    print()

    total_start = time.perf_counter()

    def on_progress(grid_file, algo_name, done, total):
        if grid_file:
            print(f"  [{done + 1}/{total}] {algo_name:20s} on {grid_file}...", flush=True)

    results = run_all_benchmarks(
        GRIDS_DIR,
        skip_brute=skip_brute,
        progress_callback=on_progress,
    )

    for r in results:
        status = "OK" if r["solved"] else "FAIL"
        print(
            f"  {r['algo']:20s} {r['time_ms']:10.2f} ms  "
            f"{r['iterations']:8d} iter  [{status}]"
        )

    elapsed = time.perf_counter() - total_start
    print(f"\nDone in {elapsed:.2f}s. {len(results)} results saved to {DB_PATH}")


if __name__ == "__main__":
    main()
