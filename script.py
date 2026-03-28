import sys
import os

from solver import (brute_force_with_callback, backtracking_with_callback,
                    backtracking_mrv, constraint_propagation, propagation_mrv)

# ANSI colors: supported natively on Linux/macOS and Windows Terminal,
# but not on legacy cmd.exe (WT_SESSION env var indicates Windows Terminal)
_ANSI_SUPPORTED = sys.platform != "win32" or "WT_SESSION" in os.environ
_BLUE = "\033[94m" if _ANSI_SUPPORTED else ""
_RESET = "\033[0m" if _ANSI_SUPPORTED else ""


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
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()

        self.grid = []
        for line in lines:
            row = []
            for char in line:
                if char == "_":
                    row.append(0)
                elif char.isdigit():
                    row.append(int(char))
            # Skip empty or separator lines (e.g. "---+---+---")
            if row:
                self.grid.append(row)

        if len(self.grid) != 9 or any(len(row) != 9 for row in self.grid):
            raise ValueError("Invalid grid: expected 9x9")

        # Deep copy: each sub-list is duplicated, not just the reference
        self.original = [row[:] for row in self.grid]

    def is_valid(self, row: int, col: int, num: int) -> bool:
        """Check if placing num at (row, col) respects sudoku rules."""
        if num in self.grid[row]:
            return False

        # Check column
        if any(self.grid[r][col] == num for r in range(9)):
            return False

        # Check 3x3 block
        start_row = (row // 3) * 3
        start_col = (col // 3) * 3
        for r in range(start_row, start_row + 3):
            for c in range(start_col, start_col + 3):
                if self.grid[r][c] == num:
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

    def solve_brute_force(self, callback=None) -> bool:
        """Brute force with optional callback for animation + 30s timeout."""
        return brute_force_with_callback(self.grid, self.is_valid, callback)

    def solve_backtracking(self, callback=None) -> bool:
        """Backtracking with optional callback for animation."""
        return backtracking_with_callback(self.grid, self.is_valid, callback)

    def solve_backtracking_mrv(self, callback=None) -> bool:
        """Improved backtracking with MRV heuristic (Minimum Remaining Values).
        Picks the cell with the fewest candidates at each step."""
        return backtracking_mrv(self.grid, self.is_valid, callback)

    def solve_propagation(self, callback=None) -> bool:
        """AC-3 constraint propagation (naked + hidden singles).
        No search: may fail on hard grids."""
        return constraint_propagation(self.grid, self.is_valid, callback)

    def solve_propagation_mrv(self, callback=None) -> bool:
        """AC-3 propagation + MRV backtracking (Norvig approach).
        Solves virtually any valid grid in under 1 ms."""
        return propagation_mrv(self.grid, self.is_valid, callback)


def count_empty_cells(grid):
    """Count empty cells (value 0) in a 9x9 grid."""
    return sum(1 for row in grid for cell in row if cell == 0)
