# =============================================================================
# benchmark.py -- Benchmarking and result persistence (SQLite)
# =============================================================================
# This file handles algorithm timing, iteration counting,
# and saving/loading results from a SQLite database (results.db).
# =============================================================================

import time
import sqlite3
import os

# Database path (at the project root, next to main.py)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results.db")


def _init_db():
    """Create the 'benchmarks' table if it doesn't exist yet.
    Called automatically before each read/write operation."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS benchmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT (datetime('now')),
            grid_file TEXT NOT NULL,
            algo TEXT NOT NULL,
            time_ms REAL NOT NULL,
            iterations INTEGER NOT NULL,
            cells_empty INTEGER NOT NULL,
            solved INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def run_benchmark(grid, original, algo_name, solve_func, grid_file):
    """Run a benchmark: measure execution time and iterations of an algorithm.

    Parameters:
        grid        -- the 9x9 grid (will be modified in-place by solve_func)
        original    -- the original grid (to count empty cells)
        algo_name   -- algorithm name (e.g. "brute", "backtrack", "propagation_mrv")
        solve_func  -- callable(callback) -> bool. Must accept a callback.
        grid_file   -- grid file name (e.g. "grid_1.txt") for the database

    Returns a dict with the benchmark results."""
    # Count empty cells in the original grid
    cells_empty = sum(1 for r in range(9) for c in range(9) if original[r][c] == 0)

    # Iteration counter via callback
    counter = {"n": 0}

    def count_callback(row, col, num, action):
        """Callback that counts each call (= 1 iteration)."""
        counter["n"] += 1

    # Measure execution time
    start = time.perf_counter()
    solved = solve_func(count_callback)
    elapsed_ms = (time.perf_counter() - start) * 1000

    result = {
        "algo": algo_name,
        "time_ms": round(elapsed_ms, 2),
        "iterations": counter["n"],
        "cells_empty": cells_empty,
        "solved": solved
    }

    # Save to SQLite
    _init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO benchmarks (grid_file, algo, time_ms, iterations, cells_empty, solved) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (grid_file, algo_name, result["time_ms"], result["iterations"],
         cells_empty, int(solved))
    )
    conn.commit()
    conn.close()

    return result


def get_all_results():
    """Load all benchmark results from SQLite.
    Returns a list of dicts, sorted by timestamp descending."""
    _init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM benchmarks ORDER BY timestamp DESC"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_results_by_grid(grid_file):
    """Load benchmark results for a specific grid.
    Returns a list of dicts, sorted by timestamp descending."""
    _init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM benchmarks WHERE grid_file = ? ORDER BY timestamp DESC",
        (grid_file,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_latest_results():
    """Load the most recent result for each (grid_file, algo) pair.
    Useful for comparison charts: we only want the latest run.
    Returns a list of dicts."""
    _init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT b.* FROM benchmarks b
        INNER JOIN (
            SELECT grid_file, algo, MAX(timestamp) as max_ts
            FROM benchmarks
            GROUP BY grid_file, algo
        ) latest ON b.grid_file = latest.grid_file
                  AND b.algo = latest.algo
                  AND b.timestamp = latest.max_ts
        ORDER BY b.grid_file, b.algo
    """).fetchall()
    conn.close()
    return [dict(row) for row in rows]
