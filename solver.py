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

import copy
import time


# =============================================================================
# [ORIGINAL] Original solver.py code (commented, not deleted)
# =============================================================================
# def find_empty(grid):
#     """Find the first empty cell (value 0) in the grid.
#     Returns a tuple (row, col) or None if no empty cell."""
#     for row in range(9):
#         for col in range(9):
#             if grid[row][col] == 0:
#                 return (row, col)
#     return None
#
#
# def get_all_empty(grid):
#     """Return a list of all empty cell positions."""
#     empty_cells = []
#     for row in range(9):
#         for col in range(9):
#             if grid[row][col] == 0:
#                 empty_cells.append((row, col))
#     return empty_cells
#
#
# def is_grid_valid(grid):
#     """Check if a fully completed grid is a valid sudoku solution.
#     Verifies all 9 rows, 9 columns, and 9 blocks for duplicates."""
#
#     # Check each row
#     for row in range(9):
#         seen = []
#         for col in range(9):
#             num = grid[row][col]
#             if num == 0 or num in seen:
#                 return False
#             seen.append(num)
#
#     # Check each column
#     for col in range(9):
#         seen = []
#         for row in range(9):
#             num = grid[row][col]
#             if num in seen:
#                 return False
#             seen.append(num)
#
#     # Check each 3x3 block
#     for block_row in range(3):
#         for block_col in range(3):
#             seen = []
#             for row in range(block_row * 3, block_row * 3 + 3):
#                 for col in range(block_col * 3, block_col * 3 + 3):
#                     num = grid[row][col]
#                     if num in seen:
#                         return False
#                     seen.append(num)
#
#     return True
#
#
# def brute_force(grid, is_valid_func):
#     """Solve by brute force: fill all empty cells, validate only when complete.
#     Places numbers without checking validity at each step.
#     Validation happens only when the entire grid is filled."""
#
#     empty_cells = get_all_empty(grid)
#
#     def try_fill(index):
#         # All cells filled -- now validate the complete grid
#         if index == len(empty_cells):
#             return is_grid_valid(grid)
#
#         row, col = empty_cells[index]
#
#         # Try each number 1 to 9 without checking validity
#         for num in range(1, 10):
#             grid[row][col] = num
#             if try_fill(index + 1):
#                 return True
#
#         # No number worked, reset and go back
#         grid[row][col] = 0
#         return False
#
#     return try_fill(0)
#
#
# def backtracking(grid, is_valid_func):
#     """Solve by backtracking: check validity before placing each number.
#     Prunes invalid branches early, much faster than brute force."""
#
#     # Find the next empty cell
#     empty = find_empty(grid)
#
#     # No empty cell means the grid is solved
#     if empty is None:
#         return True
#
#     row, col = empty
#
#     # Try each number 1 to 9
#     for num in range(1, 10):
#         # Check validity BEFORE placing the number
#         if is_valid_func(row, col, num):
#             grid[row][col] = num
#
#             # Continue solving the rest of the grid
#             if backtracking(grid, is_valid_func):
#                 return True
#
#             # This number did not lead to a solution, undo and try next
#             grid[row][col] = 0
#
#     # No number works for this cell, backtrack
#     return False
# =============================================================================
# [END ORIGINAL]
# =============================================================================


# =============================================================================
# [ADDED] Consolidated algorithms (moved from algorithms.py)
# =============================================================================


# =============================================================================
# Public helpers
# =============================================================================

def find_empty(grid):
    """Find the first empty cell (value 0), scanning top-to-bottom,
    left-to-right. Returns (row, col) or None if no empty cell."""
    for row in range(9):
        for col in range(9):
            if grid[row][col] == 0:
                return (row, col)
    return None


def get_all_empty(grid):
    """Return a list of all empty cell positions (row, col)."""
    empty = []
    for row in range(9):
        for col in range(9):
            if grid[row][col] == 0:
                empty.append((row, col))
    return empty


def is_grid_valid(grid):
    """Check if a fully completed grid is a valid sudoku solution.
    Verifies all 9 rows, 9 columns, and 9 blocks for duplicates."""
    # Check each row
    for row in range(9):
        seen = []
        for col in range(9):
            num = grid[row][col]
            if num == 0 or num in seen:
                return False
            seen.append(num)
    # Check each column
    for col in range(9):
        seen = []
        for row in range(9):
            num = grid[row][col]
            if num in seen:
                return False
            seen.append(num)
    # Check each 3x3 block
    for block_row in range(3):
        for block_col in range(3):
            seen = []
            for row in range(block_row * 3, block_row * 3 + 3):
                for col in range(block_col * 3, block_col * 3 + 3):
                    num = grid[row][col]
                    if num in seen:
                        return False
                    seen.append(num)
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


def _build_candidates(grid):
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
        units = []
        # Rows: the 9 cells of each row
        for r in range(9):
            units.append([(r, c) for c in range(9)])
        # Columns: the 9 cells of each column
        for c in range(9):
            units.append([(r, c) for r in range(9)])
        # 3x3 blocks
        for br in range(3):
            for bc in range(3):
                block = []
                for r in range(br * 3, br * 3 + 3):
                    for c in range(bc * 3, bc * 3 + 3):
                        block.append((r, c))
                units.append(block)

        for unit in units:
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

def brute_force_with_callback(grid, is_valid_func, callback=None):
    """Brute force with callback for animation and 30-second timeout.
    Reproduces the logic of the original brute_force: fills all cells
    without checking validity, then validates the complete grid at the end.
    The is_valid_func parameter is accepted for interface uniformity
    but is NOT used (same behavior as the original brute_force).

    Returns True if a solution is found, False if timeout or failure."""
    # Collect all empty cells upfront
    empty_cells = get_all_empty(grid)
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

    return try_fill(0)


# =============================================================================
# Algorithm 2: Backtracking with callback
# =============================================================================

def backtracking_with_callback(grid, is_valid_func, callback=None):
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

def backtracking_mrv(grid, is_valid_func, callback=None):
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
            return True

        row, col = best_cell
        cands = candidates[best_cell]

        # If a cell has 0 candidates, contradiction
        if len(cands) == 0:
            return False

        # Try each candidate
        for num in cands:
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

def constraint_propagation(grid, is_valid_func, callback=None):
    """Solve by constraint propagation (AC-3) WITHOUT backtracking.
    Iteratively applies Naked Single and Hidden Single rules until
    stabilization. Does NOT search if propagation alone is insufficient.

    The is_valid_func parameter is accepted for interface uniformity
    but is not used (propagation has its own mechanism).

    LIMITATION: this algorithm does NOT solve all grids. Hard grids
    require a search phase (see propagation_mrv).

    Returns True if the grid is fully solved, False otherwise."""
    # Build initial candidates
    candidates = _build_candidates(grid)

    # Propagate constraints
    no_contradiction = _propagate(candidates, grid, callback)

    if not no_contradiction:
        # Contradiction detected: the grid is invalid
        return False

    # Check if the grid is fully solved
    # (no remaining cells in candidates = all solved)
    return len(candidates) == 0


# =============================================================================
# Algorithm 5: AC-3 Propagation + Backtracking MRV (full Norvig)
# =============================================================================

def propagation_mrv(grid, is_valid_func, callback=None):
    """Solve by constraint propagation + MRV backtracking.
    This is Peter Norvig's approach ("Solving Every Sudoku Puzzle").

    Phase 1: AC-3 propagation (naked + hidden singles)
    Phase 2: If propagation stalls, pick the MRV cell and try
             each candidate with deep copy + recursive propagation.

    Complexity: O(d * n) for propagation + residual search.
    Solves virtually any valid grid in under 1 ms.

    Returns True if a solution is found, False otherwise."""
    # Build initial candidates
    candidates = _build_candidates(grid)

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

            # Backtrack: restore complete state
            for r in range(9):
                for c in range(9):
                    grid[r][c] = grid_copy[r][c]
            candidates.clear()
            candidates.update(copy.deepcopy(candidates_copy))
            if callback:
                callback(row, col, 0, "remove")

        return False

    return solve(candidates, grid)
