from solver import (brute_force_with_callback, backtracking_with_callback,
                    backtracking_mrv, constraint_propagation, propagation_mrv)


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
        with open(filepath, "r") as f:
            lines = f.read().splitlines()

        self.grid = []
        for line in lines:
            row = []
            for char in line:
                if char == "_":
                    row.append(0)
                elif char.isdigit():
                    row.append(int(char))
            if row:
                self.grid.append(row)

        self.original = [row[:] for row in self.grid]

    def is_valid(self, row: int, col: int, num: int) -> bool:
        """Check if placing num at (row, col) respects sudoku rules."""
        if num in self.grid[row]:
            return False

        if num in [self.grid[r][col] for r in range(9)]:
            return False

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
                    row_str += f"\033[94m{val}\033[0m"
                else:
                    row_str += str(val)
            print(row_str)

    def solve_brute_force(self) -> bool:
        """Solve by brute force. Returns True if a solution is found."""
        return brute_force_with_callback(self.grid, self.is_valid)

    def solve_backtracking(self) -> bool:
        """Solve by backtracking. Returns True if a solution is found."""
        return backtracking_with_callback(self.grid, self.is_valid)

    def solve_brute_force_animated(self, callback=None) -> bool:
        """Brute force with callback for animation + 30s timeout."""
        return brute_force_with_callback(self.grid, self.is_valid, callback)

    def solve_backtracking_animated(self, callback=None) -> bool:
        """Backtracking with callback for animation."""
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
