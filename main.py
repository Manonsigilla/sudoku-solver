import argparse
import sys
# Import classes and functions from your teammates' files
# (We assume script.py and solver.py are in the same directory)
from script import SudokuGrid
from display import draw_sudoku_window

def main() -> None:
    """Main entry point for the Sudoku solver CLI."""
    # 1. Set up the argument parser for the CLI
    parser = argparse.ArgumentParser(description="Sudoku Solver CLI")
    
    # Required argument: path to the grid file
    parser.add_argument("grid_file", type=str, help="Path to the text file containing the Sudoku grid")
    
    # Optional arguments to choose the algorithm and display mode
    parser.add_argument("--algo", type=str, choices=["brute", "backtrack"], default="backtrack", 
                        help="Choose the solving algorithm (default: backtrack)")
    parser.add_argument("--gui", action="store_true", 
                        help="Display the grid using Pygame after solving")
    
    # Parse the arguments
    args = parser.parse_args()

    # 2. Initialize the grid using Block 1
    print(f"Loading grid from {args.grid_file}...")
    try:
        sudoku = SudokuGrid(args.grid_file)
    except Exception as e:
        print(f"Error loading the grid: {e}")
        sys.exit(1)

    # 3. Solve the grid using Block 2
    print(f"Solving using {args.algo} algorithm...")
    success = False
    
    if args.algo == "brute":
        success = sudoku.solve_brute_force()
    elif args.algo == "backtrack":
        success = sudoku.solve_backtracking()

    # 4. Display the results
    if success:
        print("Sudoku solved successfully!")
        # Terminal display (from Block 1)
        sudoku.display()
        
        # Pygame display (from your Block 3) if requested
        if args.gui:
            draw_sudoku_window(sudoku.grid)
    else:
        print("Failed to solve the Sudoku. The grid might be invalid or unsolvable.")

if __name__ == "__main__":
    main()