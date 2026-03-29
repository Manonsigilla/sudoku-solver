"""Sudoku solving algorithms and benchmark persistence.

Provides 5 solvers (brute force, backtracking, backtracking+MRV, constraint
propagation, propagation+MRV) sharing a common interface, plus SQLite-backed
benchmark storage for timing and iteration counts.
"""

# =============================================================================
# solver.py -- All solving algorithms for the Sudoku grid
# =============================================================================
# Contains 5 algorithms, all with the same interface:
#   (grid, is_valid_func, callback=None) -> bool
#
# Callback protocol:
#   callback(row, col, num, action)
#   action: "place" (digit placed) or "remove" (digit removed / backtrack)
#
# All algorithms modify grid in-place.
# =============================================================================

from collections.abc import Callable
import copy
import os
import sqlite3
import time


class BenchmarkCancelled(Exception):
    """Raised inside a benchmark callback when the user cancels via ESC."""
    pass


# =============================================================================
# Public helpers
# =============================================================================

def find_empty(grid: list[list[int]]) -> tuple[int, int] | None:
    """Find the first empty cell (value 0), scanning top-to-bottom,
    left-to-right. Returns (row, col) or None if no empty cell."""
    for row in range(9):
        for col in range(9):
            if grid[row][col] == 0:
                return (row, col)
    return None


def get_all_empty(grid: list[list[int]]) -> list[tuple[int, int]]:
    """Return a list of all empty cell positions (row, col)."""
    empty = []
    for row in range(9):
        for col in range(9):
            if grid[row][col] == 0:
                empty.append((row, col))
    return empty


def is_grid_valid(grid: list[list[int]]) -> bool:
    """Check if a fully completed grid is a valid sudoku solution.
    Verifies all 9 rows, 9 columns, and 9 blocks for duplicates."""
    # Check each row
    for row in range(9):
        seen = set()
        for col in range(9):
            num = grid[row][col]
            if num == 0 or num in seen:
                return False
            seen.add(num)
    # Check each column
    for col in range(9):
        seen = set()
        for row in range(9):
            num = grid[row][col]
            if num == 0 or num in seen:
                return False
            seen.add(num)
    # Check each 3x3 block
    for block_row in range(3):
        for block_col in range(3):
            seen = set()
            for row in range(block_row * 3, block_row * 3 + 3):
                for col in range(block_col * 3, block_col * 3 + 3):
                    num = grid[row][col]
                    if num == 0 or num in seen:
                        return False
                    seen.add(num)
    return True


# =============================================================================
# Private helpers for constraint propagation / MRV
# =============================================================================

def _get_peers(row, col):
    """Return the set of 20 peer cells of (row, col):
    same row, same column, same 3x3 block (excluding the cell itself).
    Peers are cells that share a constraint with (row, col)."""
    peers = set()
    # Same row
    for c in range(9):
        if c != col:
            peers.add((row, c))
    # Same column
    for r in range(9):
        if r != row:
            peers.add((r, col))
    # Same 3x3 block
    start_row = (row // 3) * 3
    start_col = (col // 3) * 3
    for r in range(start_row, start_row + 3):
        for c in range(start_col, start_col + 3):
            if (r, c) != (row, col):
                peers.add((r, c))
    return peers


# Pre-compute peers for each cell (optimization: computed once at import time)
# PEERS[(r, c)] = set of 20 cells sharing a constraint with (r, c)
PEERS = {}
for _r in range(9):
    for _c in range(9):
        PEERS[(_r, _c)] = _get_peers(_r, _c)

# Pre-compute the 27 units (9 rows + 9 columns + 9 blocks)
UNITS = []
for _r in range(9):
    UNITS.append([(_r, _c) for _c in range(9)])
for _c in range(9):
    UNITS.append([(_r, _c) for _r in range(9)])
for _br in range(3):
    for _bc in range(3):
        UNITS.append([(_r, _c) for _r in range(_br * 3, _br * 3 + 3)
                                for _c in range(_bc * 3, _bc * 3 + 3)])


def build_candidates(grid: list[list[int]]) -> dict[tuple[int, int], set[int]]:
    """Build the candidate dictionary for each empty cell.
    For each empty cell (r, c), compute the set of digits 1-9 that are
    not already present in the same row, column, or block.

    Returns dict[(row, col)] -> set(int) for empty cells only."""
    candidates = {}
    for row in range(9):
        for col in range(9):
            if grid[row][col] == 0:
                # Start with all possible digits
                possible = set(range(1, 10))
                # Eliminate digits already present in peers
                for (pr, pc) in PEERS[(row, col)]:
                    val = grid[pr][pc]
                    if val != 0:
                        possible.discard(val)
                candidates[(row, col)] = possible
    return candidates


def _find_mrv_cell(candidates):
    """Find the empty cell with the Minimum Remaining Values (MRV),
    i.e. the cell with the fewest possible candidates.
    Returns (row, col) or None if candidates is empty."""
    if not candidates:
        return None
    # Pick the cell with the smallest number of candidates
    best_cell = None
    best_count = 10  # Larger than the max possible (9)
    for cell, cands in candidates.items():
        if len(cands) < best_count:
            best_count = len(cands)
            best_cell = cell
    # A cell with 0 candidates means contradiction
    if best_count == 0:
        return None
    return best_cell


# =============================================================================
# Helpers for constraint propagation (AC-3)
# =============================================================================

def _propagate(candidates, grid, callback=None):
    """Apply constraint propagation rules iteratively:
    1. Naked Single: if a cell has only one candidate, place it
    2. Hidden Single: if a digit can only go in one place
       within a unit (row/column/block), place it there

    Modifies grid and candidates in-place.
    Returns True if no contradiction, False if a contradiction is detected
    (a cell ends up with 0 candidates)."""
    changed = True
    # Loop as long as progress is made (cascading propagation)
    while changed:
        changed = False

        # --- Rule 1: Naked Singles ---
        # Find cells with exactly 1 candidate
        naked_singles = [(cell, cands) for cell, cands in candidates.items()
                         if len(cands) == 1]
        for cell, cands in naked_singles:
            row, col = cell
            num = next(iter(cands))  # The only candidate
            # Place the digit on the grid
            grid[row][col] = num
            # Notify callback if present
            if callback:
                callback(row, col, num, "place")
            # Remove this cell from candidates (it's solved)
            del candidates[cell]
            changed = True
            # Eliminate this digit from all peers' candidates
            for peer in PEERS[cell]:
                if peer in candidates:
                    candidates[peer].discard(num)
                    # Contradiction detection: peer with 0 candidates
                    if len(candidates[peer]) == 0:
                        return False

        # --- Rule 2: Hidden Singles ---
        # For each unit (row, column, block), check if a digit
        # can only go in one place
        for unit in UNITS:
            # For each digit 1-9, count how many cells in this unit
            # have it as a candidate
            for num in range(1, 10):
                # Cells in this unit where num is a candidate
                positions = [cell for cell in unit
                             if cell in candidates and num in candidates[cell]]
                if len(positions) == 0:
                    # This digit is already placed in the unit, or contradiction
                    # Check if it's already placed
                    placed = any(grid[r][c] == num for (r, c) in unit)
                    if not placed:
                        # Contradiction: digit impossible to place in this unit
                        return False
                elif len(positions) == 1:
                    # Hidden single: num can only go in one place
                    cell = positions[0]
                    row, col = cell
                    if len(candidates[cell]) > 1:
                        # Place the digit
                        grid[row][col] = num
                        if callback:
                            callback(row, col, num, "place")
                        del candidates[cell]
                        changed = True
                        # Eliminate from peers
                        for peer in PEERS[cell]:
                            if peer in candidates:
                                candidates[peer].discard(num)
                                if len(candidates[peer]) == 0:
                                    return False

    # No contradiction detected
    return True


# =============================================================================
# Algorithm 1: Brute Force with callback and timeout
# =============================================================================

def brute_force_with_callback(
    grid: list[list[int]],
    is_valid_func: Callable,
    callback: Callable | None = None,
) -> bool:
    """Brute force with callback for animation and 30-second timeout.
    Reproduces the logic of the original brute_force: fills all cells
    without checking validity, then validates the complete grid at the end.
    The is_valid_func parameter is accepted for interface uniformity
    but is NOT used (same behavior as the original brute_force).

    Returns True if a solution is found, False if timeout or failure."""
    # Collect all empty cells upfront
    empty_cells = get_all_empty(grid)
    # Save grid state for restoration on failure (BUG 2 fix)
    grid_copy = [r[:] for r in grid]
    # Start timestamp for timeout
    start_time = time.time()
    # Counter to check timeout only every 1000 iterations
    iteration_count = [0]
    # Timeout in seconds
    TIMEOUT = 30

    def try_fill(index):
        """Internal recursive function: try to fill cells one by one."""
        # Check timeout every 1000 iterations
        iteration_count[0] += 1
        if iteration_count[0] % 1000 == 0:
            if time.time() - start_time > TIMEOUT:
                return False

        # Base case: all cells filled, validate the grid
        if index == len(empty_cells):
            return is_grid_valid(grid)

        row, col = empty_cells[index]

        # Try each digit 1-9 without checking validity
        for num in range(1, 10):
            grid[row][col] = num
            # Notify callback (placement)
            if callback:
                callback(row, col, num, "place")
            # Continue with the next cell
            if try_fill(index + 1):
                return True

        # No digit worked, reset and backtrack
        grid[row][col] = 0
        if callback:
            callback(row, col, 0, "remove")
        return False

    result = try_fill(0)
    # Restore grid on failure or timeout (BUG 2 fix)
    if not result:
        for r in range(9):
            for c in range(9):
                grid[r][c] = grid_copy[r][c]
    return result


# =============================================================================
# Algorithm 2: Backtracking with callback
# =============================================================================

def backtracking_with_callback(
    grid: list[list[int]],
    is_valid_func: Callable,
    callback: Callable | None = None,
) -> bool:
    """Classic backtracking with callback for animation.
    Reproduces the logic of the original backtracking: finds the first empty
    cell, tries digits 1-9 checking validity BEFORE placement.

    Returns True if a solution is found, False otherwise."""
    # Find the next empty cell
    empty = find_empty(grid)
    # No empty cell = grid solved
    if empty is None:
        return True

    row, col = empty

    # Try each digit 1-9
    for num in range(1, 10):
        # Check validity BEFORE placing (pruning)
        if is_valid_func(row, col, num):
            grid[row][col] = num
            # Notify callback (valid placement)
            if callback:
                callback(row, col, num, "place")
            # Continue recursively
            if backtracking_with_callback(grid, is_valid_func, callback):
                return True
            # Failure: reset to 0 (backtrack)
            grid[row][col] = 0
            if callback:
                callback(row, col, 0, "remove")

    # No valid digit for this cell, backtrack
    return False


# =============================================================================
# Algorithm 3: Backtracking + MRV (Minimum Remaining Values)
# =============================================================================

def backtracking_mrv(
    grid: list[list[int]],
    is_valid_func: Callable,
    callback: Callable | None = None,
) -> bool:
    """Improved backtracking with MRV heuristic.
    Instead of picking the first empty cell (top-left as in classic
    backtracking), picks the cell with the FEWEST valid candidates.
    This drastically reduces the search tree.

    Complexity: O(9^m) worst case, but much better in practice thanks to MRV.
    Returns True if a solution is found, False otherwise."""
    # Compute candidates for all empty cells
    candidates = {}
    for row in range(9):
        for col in range(9):
            if grid[row][col] == 0:
                # Compute valid digits for this cell
                valid = set()
                for num in range(1, 10):
                    if is_valid_func(row, col, num):
                        valid.add(num)
                candidates[(row, col)] = valid

    def solve(candidates):
        """Internal recursive function with MRV."""
        # No empty cell = grid solved
        if not candidates:
            return True

        # Pick the cell with the fewest candidates (MRV)
        best_cell = _find_mrv_cell(candidates)
        if best_cell is None:
            return False

        row, col = best_cell
        cands = candidates[best_cell]

        # If a cell has 0 candidates, contradiction
        if len(cands) == 0:
            return False

        # Try each candidate (iterate over a copy: cands is mutated during backtrack)
        for num in list(cands):
            grid[row][col] = num
            if callback:
                callback(row, col, num, "place")

            # Update affected peers' candidates
            # (remove num from peers' candidates)
            removed_from = []
            contradiction = False
            for peer in PEERS[best_cell]:
                if peer in candidates and num in candidates[peer]:
                    candidates[peer].discard(num)
                    removed_from.append(peer)
                    # Contradiction detection
                    if len(candidates[peer]) == 0:
                        contradiction = True
                        break

            # Remove current cell from candidates (it's filled)
            saved_cands = candidates.pop(best_cell)

            if not contradiction and solve(candidates):
                return True

            # Backtrack: restore state
            candidates[best_cell] = saved_cands
            for peer in removed_from:
                candidates[peer].add(num)
            grid[row][col] = 0
            if callback:
                callback(row, col, 0, "remove")

        return False

    return solve(candidates)


# =============================================================================
# Algorithm 4: Constraint Propagation AC-3 (without search)
# =============================================================================

def constraint_propagation(
    grid: list[list[int]],
    is_valid_func: Callable,
    callback: Callable | None = None,
) -> bool:
    """Solve by constraint propagation (AC-3) WITHOUT backtracking.
    Iteratively applies Naked Single and Hidden Single rules until
    stabilization. Does NOT search if propagation alone is insufficient.

    The is_valid_func parameter is accepted for interface uniformity
    but is not used (propagation has its own mechanism).

    LIMITATION: this algorithm does NOT solve all grids. Hard grids
    require a search phase (see propagation_mrv).

    Returns True if the grid is fully solved, False otherwise."""
    # Build initial candidates
    candidates = build_candidates(grid)

    # Save grid state before propagation (BUG 1 fix)
    grid_copy = [r[:] for r in grid]

    # Propagate constraints
    no_contradiction = _propagate(candidates, grid, callback)

    if not no_contradiction:
        # Contradiction: restore grid to its original state
        for r in range(9):
            for c in range(9):
                grid[r][c] = grid_copy[r][c]
        return False

    # Check if the grid is fully solved
    # (no remaining cells in candidates = all solved)
    return len(candidates) == 0


# =============================================================================
# Algorithm 5: AC-3 Propagation + Backtracking MRV (full Norvig)
# =============================================================================

def propagation_mrv(
    grid: list[list[int]],
    is_valid_func: Callable,
    callback: Callable | None = None,
) -> bool:
    """Solve by constraint propagation + MRV backtracking.
    This is Peter Norvig's approach ("Solving Every Sudoku Puzzle").

    Phase 1: AC-3 propagation (naked + hidden singles)
    Phase 2: If propagation stalls, pick the MRV cell and try
             each candidate with deep copy + recursive propagation.

    Complexity: O(d * n) for propagation + residual search.
    Solves virtually any valid grid in under 1 ms.

    Returns True if a solution is found, False otherwise."""
    # Build initial candidates
    candidates = build_candidates(grid)

    def solve(candidates, grid):
        """Recursive function: propagate then search if needed."""
        # Phase 1: Propagation
        if not _propagate(candidates, grid, callback):
            return False  # Contradiction

        # Check if solved
        if len(candidates) == 0:
            return True  # All cells are filled

        # Phase 2: Search -- pick the MRV cell
        cell = _find_mrv_cell(candidates)
        if cell is None:
            return True
        row, col = cell

        # Try each candidate with deep copy of state
        for num in list(candidates[cell]):
            # Save complete state before attempt
            grid_copy = [r[:] for r in grid]
            candidates_copy = copy.deepcopy(candidates)

            # Place the digit
            grid[row][col] = num
            if callback:
                callback(row, col, num, "place")
            # Update candidates: remove cell and propagate
            del candidates[cell]
            # Eliminate num from peers
            for peer in PEERS[cell]:
                if peer in candidates:
                    candidates[peer].discard(num)

            # Recurse
            if solve(candidates, grid):
                return True

            # Backtrack: send "remove" for ALL cells changed by propagation
            # before restoring grid state (BUG 3 fix)
            if callback:
                for r in range(9):
                    for c in range(9):
                        if grid[r][c] != grid_copy[r][c]:
                            callback(r, c, 0, "remove")
            # Restore complete state
            for r in range(9):
                for c in range(9):
                    grid[r][c] = grid_copy[r][c]
            candidates.clear()
            candidates.update(candidates_copy)

        return False

    return solve(candidates, grid)


# =============================================================================
# Benchmark / SQLite persistence
# =============================================================================

DB_PATH: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results.db")


def _init_db() -> None:
    """Create the 'benchmarks' table if it doesn't exist yet.
    Called automatically before each read/write operation."""
    conn = sqlite3.connect(DB_PATH)
    try:
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
    finally:
        conn.close()


def run_benchmark(
    original: list[list[int]],
    algo_name: str,
    solve_func,
    grid_file: str,
    cancel_check: Callable | None = None,
) -> dict | None:
    """Run a benchmark: measure execution time and iterations of an algorithm.

    Parameters:
        original      -- the original grid (to count empty cells)
        algo_name     -- algorithm name (e.g. "brute", "backtrack", "propagation_mrv")
        solve_func    -- callable(callback) -> bool. Must accept a callback.
        grid_file     -- grid file name (e.g. "grid_1.txt") for the database
        cancel_check  -- optional callable() -> bool; checked every 500 iterations

    Returns a dict with the benchmark results, or None if cancelled."""
    cells_empty = len(get_all_empty(original))

    # Iteration counter via callback
    counter = {"n": 0}

    def count_callback(row, col, num, action):
        """Callback that counts each call (= 1 iteration)."""
        counter["n"] += 1
        if cancel_check and counter["n"] % 500 == 0 and cancel_check():
            raise BenchmarkCancelled()

    # Measure execution time
    start = time.perf_counter()
    try:
        solved = solve_func(count_callback)
    except BenchmarkCancelled:
        return None
    elapsed_ms = (time.perf_counter() - start) * 1000

    result = {
        "algo": algo_name,
        "time_ms": round(elapsed_ms, 2),
        "iterations": counter["n"],
        "cells_empty": cells_empty,
        "solved": solved,
    }

    # Save to SQLite (BUG B2 fix: int(bool(solved)) handles None)
    save_result(grid_file, algo_name, result["time_ms"],
                result["iterations"], cells_empty, int(bool(solved)))

    return result


def save_result(
    grid_file: str,
    algo: str,
    time_ms: float,
    iterations: int,
    cells_empty: int,
    solved: int,
) -> None:
    """Save a single benchmark result to SQLite."""
    _init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "INSERT INTO benchmarks "
            "(grid_file, algo, time_ms, iterations, cells_empty, solved) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (grid_file, algo, time_ms, iterations, cells_empty, int(bool(solved))),
        )
        conn.commit()
    except sqlite3.OperationalError as e:
        print(f"[WARN] Could not save benchmark result: {e}")
    finally:
        conn.close()


def get_all_results() -> list[dict]:
    """Load all benchmark results from SQLite.
    Returns a list of dicts, sorted by timestamp descending."""
    _init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM benchmarks ORDER BY timestamp DESC"
        ).fetchall()
        return [dict(row) for row in rows]
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()


def get_results_by_grid(grid_file: str) -> list[dict]:
    """Load benchmark results for a specific grid.
    Returns a list of dicts, sorted by timestamp descending."""
    _init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM benchmarks WHERE grid_file = ? ORDER BY timestamp DESC",
            (grid_file,),
        ).fetchall()
        return [dict(row) for row in rows]
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()


def get_latest_results() -> list[dict]:
    """Load the most recent result for each (grid_file, algo) pair.
    Useful for comparison charts: we only want the latest run.
    Returns a list of dicts."""
    _init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.row_factory = sqlite3.Row
        # BUG B3 fix: use MAX(timestamp) instead of MAX(id)
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
        return [dict(row) for row in rows]
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()


# =============================================================================
# CRUD -- Delete & Update
# =============================================================================


def delete_result(result_id: int) -> bool:
    """Delete a single benchmark result by its ID.
    Returns True if a row was actually deleted."""
    _init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.execute(
            "DELETE FROM benchmarks WHERE id = ?", (result_id,)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_all_results() -> int:
    """Delete all benchmark results (full reset).
    Returns the number of rows deleted."""
    _init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.execute("DELETE FROM benchmarks")
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


_UPDATABLE_COLUMNS = frozenset(
    {"grid_file", "algo", "time_ms", "iterations", "cells_empty", "solved"}
)


def update_result(result_id: int, **fields) -> bool:
    """Update specific fields of a benchmark result.
    Only columns in _UPDATABLE_COLUMNS are accepted; unknown keys are ignored.
    Returns True if a row was actually updated."""
    safe = {k: v for k, v in fields.items() if k in _UPDATABLE_COLUMNS}
    if not safe:
        return False

    set_clause = ", ".join(f"{col} = ?" for col in safe)
    values = list(safe.values()) + [result_id]

    _init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.execute(
            f"UPDATE benchmarks SET {set_clause} WHERE id = ?", values
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# =============================================================================
# Run All Benchmarks (reusable from CLI and GUI)
# =============================================================================

ALGORITHMS = [
    ("brute", "solve_brute_force"),
    ("backtrack", "solve_backtracking"),
    ("backtrack_mrv", "solve_backtracking_mrv"),
    ("propagation", "solve_propagation"),
    ("propagation_mrv", "solve_propagation_mrv"),
]


def run_all_benchmarks(
    grids_dir: str,
    skip_brute: bool = False,
    progress_callback: Callable | None = None,
    cancel_check: Callable | None = None,
) -> list[dict]:
    """Run every algorithm on every grid file and save results to SQLite.

    Parameters:
        grids_dir          -- path to the directory containing .txt grid files
        skip_brute         -- if True, skip the brute force algorithm
        progress_callback  -- optional callable(grid_file, algo_name, done, total)
                              called before each benchmark starts
        cancel_check       -- optional callable() -> bool; return True to abort

    Returns a list of result dicts from run_benchmark()."""
    # Lazy import to avoid circular dependency (script.py imports solver.py)
    from script import SudokuGrid

    if not os.path.isdir(grids_dir):
        return []

    grid_files = sorted(
        f for f in os.listdir(grids_dir) if f.endswith(".txt")
    )

    total = len(grid_files) * len(ALGORITHMS)
    results = []
    done = 0

    for grid_file in grid_files:
        filepath = os.path.join(grids_dir, grid_file)

        for algo_name, method_name in ALGORITHMS:
            if cancel_check and cancel_check():
                return results

            if progress_callback:
                progress_callback(grid_file, algo_name, done, total)

            sg = SudokuGrid(filepath)

            if skip_brute and algo_name == "brute":
                cells_empty = len(get_all_empty(sg.original))
                placeholder = {
                    "algo": "brute",
                    "time_ms": 300_000.0,
                    "iterations": 0,
                    "cells_empty": cells_empty,
                    "solved": False,
                }
                save_result(grid_file, "brute", 300_000.0, 0, cells_empty, 0)
                results.append(placeholder)
                done += 1
                continue

            solve_func = getattr(sg, method_name)
            result = run_benchmark(
                sg.original, algo_name, solve_func, grid_file,
                cancel_check=cancel_check,
            )
            if result is None:
                return results
            results.append(result)
            done += 1

    if progress_callback:
        progress_callback("", "", done, total)

    return results


# =============================================================================
# Backward-compatible aliases
# =============================================================================

brute_force = brute_force_with_callback
backtracking = backtracking_with_callback
