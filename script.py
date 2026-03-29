import json
import os
import random
import sys

from solver import (brute_force_with_callback, backtracking_with_callback,
                    backtracking_mrv, constraint_propagation, propagation_mrv,
                    build_candidates)

# ANSI colors: supported natively on Linux/macOS and Windows Terminal,
# but not on legacy cmd.exe (WT_SESSION env var indicates Windows Terminal)
_ANSI_SUPPORTED = sys.platform != "win32" or "WT_SESSION" in os.environ
_BLUE = "\033[94m" if _ANSI_SUPPORTED else ""
_RESET = "\033[0m" if _ANSI_SUPPORTED else ""

# ============================================================================
# Game constants
# ============================================================================
EASY_MIN, EASY_MAX = 36, 50          # Easy: 36-50 filled cells
NORMAL_MIN, NORMAL_MAX = 27, 35      # Normal: 27-35 filled cells
HARD_MIN, HARD_MAX = 17, 26          # Hard: 17-26 filled cells

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOLUTIONS_FILE = os.path.join(_BASE_DIR, "solutions.json")
GRIDS_DIR = os.path.join(_BASE_DIR, "grids")


# ============================================================================
# SudokuGrid class
# ============================================================================

class SudokuGrid:
    grid: list[list[int]]
    original: list[list[int]]

    def __init__(self, filepath: str) -> None:
        """Load and parse the grid from a text file."""
        self.grid = []
        self.original = []
        self.load_from_file(filepath)

    def load_from_file(self, filepath: str) -> None:
        """Parse the file: '_' becomes 0, digits stay as-is."""
        # BUG 3 fix: intercept FileNotFoundError
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
        except FileNotFoundError:
            raise ValueError(f"Grid file not found: {filepath}")

        self.grid = []
        for i, line in enumerate(lines):
            row = []
            for char in line:
                if char == "_":
                    row.append(0)
                elif char.isdigit():
                    row.append(int(char))
            # Skip empty or separator lines (e.g. "---+---+---")
            if row:
                # BUG 4 fix: report partial lines with line number and count
                if len(row) != 9:
                    raise ValueError(
                        f"Invalid row at line {i + 1}: "
                        f"expected 9 elements, got {len(row)}"
                    )
                self.grid.append(row)

        if len(self.grid) != 9:
            raise ValueError(
                f"Invalid grid: expected 9 rows, got {len(self.grid)}"
            )

        # Deep copy: each sub-list is duplicated, not just the reference
        self.original = [row[:] for row in self.grid]

    def is_valid(self, row: int, col: int, num: int) -> bool:
        """Check if placing num at (row, col) respects sudoku rules."""
        # BUG 1 fix: exclude the cell itself in all three checks
        # Check row
        for c in range(9):
            if c != col and self.grid[row][c] == num:
                return False

        # Check column
        for r in range(9):
            if r != row and self.grid[r][col] == num:
                return False

        # Check 3x3 block
        start_row = (row // 3) * 3
        start_col = (col // 3) * 3
        for r in range(start_row, start_row + 3):
            for c in range(start_col, start_col + 3):
                if (r, c) != (row, col) and self.grid[r][c] == num:
                    return False

        return True

    def is_complete(self) -> bool:
        """Return True if the grid has no empty cells (0)."""
        for row in self.grid:
            if 0 in row:
                return False
        return True

    def display(self) -> None:
        """Display the grid in the terminal with original/added distinction."""
        for r in range(9):
            if r > 0 and r % 3 == 0:
                print("------+-------+------")
            row_str = ""
            for c in range(9):
                if c > 0 and c % 3 == 0:
                    row_str += " | "
                elif c > 0:
                    row_str += " "
                val = self.grid[r][c]
                if val == 0:
                    row_str += "."
                elif self.original[r][c] == 0:
                    # Value added by the solver: display in blue
                    row_str += f"{_BLUE}{val}{_RESET}"
                else:
                    row_str += str(val)
            print(row_str)

    # BUG 2 fix: each solve_* restores self.grid from self.original
    def solve_brute_force(self, callback=None) -> bool:
        """Brute force with optional callback for animation + 30s timeout."""
        self.grid = [row[:] for row in self.original]
        return brute_force_with_callback(self.grid, self.is_valid, callback)

    def solve_backtracking(self, callback=None) -> bool:
        """Backtracking with optional callback for animation."""
        self.grid = [row[:] for row in self.original]
        return backtracking_with_callback(self.grid, self.is_valid, callback)

    def solve_backtracking_mrv(self, callback=None) -> bool:
        """Improved backtracking with MRV heuristic (Minimum Remaining Values).
        Picks the cell with the fewest candidates at each step."""
        self.grid = [row[:] for row in self.original]
        return backtracking_mrv(self.grid, self.is_valid, callback)

    def solve_propagation(self, callback=None) -> bool:
        """AC-3 constraint propagation (naked + hidden singles).
        No search: may fail on hard grids."""
        self.grid = [row[:] for row in self.original]
        return constraint_propagation(self.grid, self.is_valid, callback)

    def solve_propagation_mrv(self, callback=None) -> bool:
        """AC-3 propagation + MRV backtracking (Norvig approach).
        Solves virtually any valid grid in under 1 ms."""
        self.grid = [row[:] for row in self.original]
        return propagation_mrv(self.grid, self.is_valid, callback)


# ============================================================================
# Grid utilities
# ============================================================================

def count_empty_cells(grid: list[list[int]]) -> int:
    """Count empty cells (value 0) in a 9x9 grid."""
    return sum(1 for row in grid for cell in row if cell == 0)


def count_filled_cells(grid: list[list[int]]) -> int:
    """Count non-zero cells in a grid."""
    return 81 - count_empty_cells(grid)


def get_grid_difficulty(grid: list[list[int]]) -> str:
    """Classify grid difficulty based on filled cells."""
    filled = count_filled_cells(grid)
    if EASY_MIN <= filled <= EASY_MAX:
        return "easy"
    elif NORMAL_MIN <= filled <= NORMAL_MAX:
        return "normal"
    elif HARD_MIN <= filled <= HARD_MAX:
        return "hard"
    # BUG G4 fix: return "unknown" instead of None
    return "unknown"


# ============================================================================
# Solutions database (JSON)
# ============================================================================

def load_solutions_db() -> dict:
    """Load solutions from JSON file. Create if doesn't exist."""
    if os.path.exists(SOLUTIONS_FILE):
        try:
            with open(SOLUTIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_solutions_db(db: dict) -> None:
    """Save solutions to JSON file (atomic write-then-rename)."""
    tmp_path = SOLUTIONS_FILE + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2)
    os.replace(tmp_path, SOLUTIONS_FILE)


def grid_to_string(grid: list[list[int]]) -> str:
    """Convert grid to string key for JSON storage."""
    return json.dumps(grid)


def string_to_grid(grid_str: str) -> list[list[int]]:
    """Convert string key back to grid."""
    return json.loads(grid_str)


# ============================================================================
# Puzzle generation
# ============================================================================

def generate_solved_grid() -> list[list[int]]:
    """Generate a complete valid sudoku grid (backtracking from empty grid)."""
    grid = [[0] * 9 for _ in range(9)]

    def is_valid(row: int, col: int, num: int) -> bool:
        if num in grid[row]:
            return False
        if any(grid[r][col] == num for r in range(9)):
            return False
        start_row, start_col = (row // 3) * 3, (col // 3) * 3
        for r in range(start_row, start_row + 3):
            for c in range(start_col, start_col + 3):
                if grid[r][c] == num:
                    return False
        return True

    def fill():
        for row in range(9):
            for col in range(9):
                if grid[row][col] == 0:
                    nums = list(range(1, 10))
                    random.shuffle(nums)
                    for num in nums:
                        if is_valid(row, col, num):
                            grid[row][col] = num
                            if fill():
                                return True
                            grid[row][col] = 0
                    return False
        return True

    fill()
    return grid


def _is_valid_placement(grid: list[list[int]], row: int, col: int,
                        num: int) -> bool:
    """Check if placing num at (row, col) is valid on a standalone grid."""
    if num in grid[row]:
        return False
    if any(grid[r][col] == num for r in range(9)):
        return False
    br, bc = (row // 3) * 3, (col // 3) * 3
    for r in range(br, br + 3):
        for c in range(bc, bc + 3):
            if grid[r][c] == num:
                return False
    return True


def _count_solutions(grid: list[list[int]], limit: int = 2) -> int:
    """Count solutions of grid, stopping early at limit.
    Returns count (0, 1, or up to limit)."""
    count = [0]

    def _solve(g):
        empty = None
        for r in range(9):
            for c in range(9):
                if g[r][c] == 0:
                    empty = (r, c)
                    break
            if empty:
                break
        if empty is None:
            count[0] += 1
            return count[0] >= limit
        r, c = empty
        for num in range(1, 10):
            if _is_valid_placement(g, r, c, num):
                g[r][c] = num
                if _solve(g):
                    g[r][c] = 0
                    return True
                g[r][c] = 0
        return False

    _solve([row[:] for row in grid])
    return count[0]


def remove_cells(grid: list[list[int]],
                 target_difficulty: str) -> list[list[int]]:
    """Remove cells from a solved grid to create a puzzle of target difficulty.
    Ensures the resulting puzzle has exactly one solution."""
    puzzle = [row[:] for row in grid]

    if target_difficulty == "easy":
        target = random.randint(EASY_MIN, EASY_MAX)
    elif target_difficulty == "normal":
        target = random.randint(NORMAL_MIN, NORMAL_MAX)
    elif target_difficulty == "hard":
        target = random.randint(HARD_MIN, HARD_MAX)
    else:
        target = 30

    cells_to_remove = 81 - target
    positions = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(positions)

    removed = 0
    for row, col in positions:
        if removed >= cells_to_remove:
            break
        saved = puzzle[row][col]
        puzzle[row][col] = 0
        if _count_solutions(puzzle, limit=2) != 1:
            puzzle[row][col] = saved
        else:
            removed += 1

    # BUG G2 fix: warn if target not reached
    if removed < cells_to_remove:
        print(f"[WARN] Could only remove {removed}/{cells_to_remove} cells "
              f"while maintaining unique solution")

    return puzzle


def generate_new_puzzle(
    difficulty: str,
) -> tuple[list[list[int]], list[list[int]]]:
    """Generate a new puzzle and return (puzzle, solved_grid)."""
    print(f"Generating new {difficulty} puzzle...")
    solved = generate_solved_grid()
    puzzle = remove_cells(solved, difficulty)
    return puzzle, solved


def get_or_generate_puzzle(
    difficulty: str,
) -> tuple[list[list[int]], list[list[int]]]:
    """Get a puzzle of specified difficulty from existing grids in grids/ folder.
    If not enough grids, generate a new one.
    Returns (puzzle_grid, solved_grid)."""
    db = load_solutions_db()

    available_grids = []
    if os.path.exists(GRIDS_DIR):
        for filename in os.listdir(GRIDS_DIR):
            if filename.endswith(".txt"):
                filepath = os.path.join(GRIDS_DIR, filename)
                try:
                    sudoku = SudokuGrid(filepath)
                    diff = get_grid_difficulty(sudoku.grid)
                    if diff == difficulty:
                        available_grids.append(filepath)
                except Exception as e:
                    print(f"[WARN] Skipping grid file {filename}: {e}")

    if available_grids:
        selected_path = random.choice(available_grids)
        print(f"Loading puzzle from {selected_path}...")
        try:
            sudoku = SudokuGrid(selected_path)
            puzzle_grid = [row[:] for row in sudoku.grid]
            grid_key = grid_to_string(puzzle_grid)

            if grid_key in db:
                solved_grid = string_to_grid(db[grid_key])
                return puzzle_grid, solved_grid
            else:
                print("Solving puzzle for validation...")
                solved_grid = [row[:] for row in sudoku.grid]
                # BUG G1 fix: use _is_valid_placement on solved_grid
                # instead of sudoku.is_valid (which checks sudoku.grid)
                success = propagation_mrv(
                    solved_grid,
                    lambda r, c, n: _is_valid_placement(solved_grid, r, c, n),
                )
                if success:
                    db[grid_key] = grid_to_string(solved_grid)
                    save_solutions_db(db)
                    return puzzle_grid, solved_grid
                else:
                    print("[WARN] Could not solve loaded grid. "
                          "Generating new one...")
        except Exception as e:
            print(f"Error loading grid: {e}")

    puzzle_grid, solved_grid = generate_new_puzzle(difficulty)
    grid_key = grid_to_string(puzzle_grid)
    db[grid_key] = grid_to_string(solved_grid)
    save_solutions_db(db)
    return puzzle_grid, solved_grid


# ============================================================================
# Move validation
# ============================================================================

def validate_move(grid: list[list[int]], solved_grid: list[list[int]],
                  row: int, col: int, num: int) -> str:
    """Validate a player's move.
    Returns: "correct" (green), "wrong" (red), "multiple" (yellow).

    Design note (BUG G3): candidates are computed on the current grid state,
    which may already contain player moves. This reflects the board as the
    player sees it, so "multiple" accounts for prior placements."""
    if solved_grid[row][col] == num:
        return "correct"
    candidates = build_candidates(grid)
    if (row, col) in candidates and num in candidates[(row, col)]:
        return "multiple"
    return "wrong"
