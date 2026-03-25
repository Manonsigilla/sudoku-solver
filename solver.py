def find_empty(grid):
    """Find the first empty cell (value 0) in the grid.
    Returns a tuple (row, col) or None if no empty cell."""
    for row in range(9):
        for col in range(9):
            if grid[row][col] == 0:
                return (row, col)
    return None


def get_all_empty(grid):
    """Return a list of all empty cell positions."""
    empty_cells = []
    for row in range(9):
        for col in range(9):
            if grid[row][col] == 0:
                empty_cells.append((row, col))
    return empty_cells


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


def brute_force(grid, is_valid_func):
    """Solve by brute force: fill all empty cells, validate only when complete.
    Places numbers without checking validity at each step.
    Validation happens only when the entire grid is filled."""

    empty_cells = get_all_empty(grid)

    def try_fill(index):
        # All cells filled -- now validate the complete grid
        if index == len(empty_cells):
            return is_grid_valid(grid)

        row, col = empty_cells[index]

        # Try each number 1 to 9 without checking validity
        for num in range(1, 10):
            grid[row][col] = num
            if try_fill(index + 1):
                return True

        # No number worked, reset and go back
        grid[row][col] = 0
        return False

    return try_fill(0)


def backtracking(grid, is_valid_func):
    """Solve by backtracking: check validity before placing each number.
    Prunes invalid branches early, much faster than brute force."""

    # Find the next empty cell
    empty = find_empty(grid)

    # No empty cell means the grid is solved
    if empty is None:
        return True

    row, col = empty

    # Try each number 1 to 9
    for num in range(1, 10):
        # Check validity BEFORE placing the number
        if is_valid_func(row, col, num):
            grid[row][col] = num

            # Continue solving the rest of the grid
            if backtracking(grid, is_valid_func):
                return True

            # This number did not lead to a solution, undo and try next
            grid[row][col] = 0

    # No number works for this cell, backtrack
    return False
