import json
import random
import os
from script import SudokuGrid, count_empty_cells
from solver import propagation_mrv, build_candidates

# Game constants
EASY_MIN, EASY_MAX = 36, 50          # Easy: 36-50 filled cells
NORMAL_MIN, NORMAL_MAX = 27, 35      # Normal: 27-35 filled cells
HARD_MIN, HARD_MAX = 17, 26          # Hard: 17-26 filled cells

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOLUTIONS_FILE = os.path.join(_BASE_DIR, "solutions.json")
GRIDS_DIR = os.path.join(_BASE_DIR, "grids")


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
    else:
        return None  # Outside all ranges


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


def generate_solved_grid() -> list[list[int]]:
    """Generate a complete valid sudoku grid (backtracking from empty grid)."""
    grid = [[0] * 9 for _ in range(9)]
    
    def is_valid(row: int, col: int, num: int) -> bool:
        # Check row
        if num in grid[row]:
            return False
        # Check column
        if any(grid[r][col] == num for r in range(9)):
            return False
        # Check 3x3 block
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
                    # Shuffle digits 1-9 for randomness
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


def _is_valid_placement(grid, row, col, num):
    """Check if placing num at (row, col) is valid (no conflict)."""
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


def _count_solutions(grid, limit=2):
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


def remove_cells(grid: list[list[int]], target_difficulty: str) -> list[list[int]]:
    """Remove cells from a solved grid to create a puzzle of target difficulty.
    Ensures the resulting puzzle has exactly one solution."""
    puzzle = [row[:] for row in grid]

    # Determine target number of filled cells
    if target_difficulty == "easy":
        target = random.randint(EASY_MIN, EASY_MAX)
    elif target_difficulty == "normal":
        target = random.randint(NORMAL_MIN, NORMAL_MAX)
    elif target_difficulty == "hard":
        target = random.randint(HARD_MIN, HARD_MAX)
    else:
        target = 30

    # Currently all 81 cells are filled, remove until target
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
            puzzle[row][col] = saved  # Restore: removal breaks uniqueness
        else:
            removed += 1

    return puzzle


def generate_new_puzzle(difficulty: str) -> tuple[list[list[int]], list[list[int]]]:
    """Generate a new puzzle and return (puzzle, solved_grid)."""
    print(f"Generating new {difficulty} puzzle...")
    solved = generate_solved_grid()
    puzzle = remove_cells(solved, difficulty)
    return puzzle, solved


def get_or_generate_puzzle(difficulty: str) -> tuple[list[list[int]], list[list[int]]]:
    """
    Get a puzzle of specified difficulty from existing grids in grids/ folder.
    If not enough grids, generate a new one.
    Returns (puzzle_grid, solved_grid).
    """
    db = load_solutions_db()
    
    # Scan existing grids in grids/ directory
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
    
    # If we found a grid of the right difficulty, use it
    if available_grids:
        selected_path = random.choice(available_grids)
        print(f"Loading puzzle from {selected_path}...")
        try:
            sudoku = SudokuGrid(selected_path)
            puzzle_grid = [row[:] for row in sudoku.grid]
            grid_key = grid_to_string(puzzle_grid)
            
            # Check if we already solved this puzzle
            if grid_key in db:
                solved_grid = string_to_grid(db[grid_key])
                return puzzle_grid, solved_grid
            else:
                # Need to solve it
                print("Solving puzzle for validation...")
                solved_grid = [row[:] for row in sudoku.grid]
                # Use the solver to find the complete solution
                success = propagation_mrv(solved_grid, sudoku.is_valid)
                if success:
                    db[grid_key] = grid_to_string(solved_grid)
                    save_solutions_db(db)
                    return puzzle_grid, solved_grid
                else:
                    print("Warning: Could not solve loaded grid. Generating new one...")
        except Exception as e:
            print(f"Error loading grid: {e}")
    
    # Generate new puzzle
    puzzle_grid, solved_grid = generate_new_puzzle(difficulty)
    grid_key = grid_to_string(puzzle_grid)
    db[grid_key] = grid_to_string(solved_grid)
    save_solutions_db(db)
    return puzzle_grid, solved_grid


def validate_move(grid: list[list[int]], solved_grid: list[list[int]], 
                  row: int, col: int, num: int) -> str:
    """
    Validate a player's move.
    Returns: "correct" (green), "wrong" (red), "multiple" (yellow, only EASY mode)
    """
    if solved_grid[row][col] == num:
        # Correct number
        return "correct"
    else:
        # Check if this number could be valid (is it in the candidates)
        candidates = build_candidates(grid)
        if (row, col) in candidates and num in candidates[(row, col)]:
            # Player placed a valid candidate but not the solution
            return "multiple"
        else:
            # Invalid number
            return "wrong"