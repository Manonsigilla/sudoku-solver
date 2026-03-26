import argparse
import sys
import os
import pygame
from script import SudokuGrid
from display import draw_sudoku_interactive, show_main_menu, show_difficulty_menu, play_game, main_menu

def main() -> None:
    """Main entry point for the Sudoku solver CLI."""
    
    # Show main menu first
    main_choice = show_main_menu()
    
    if main_choice == "1":
        # Play mode
        while True:
            diff_choice = show_difficulty_menu()
            if diff_choice == "1":
                play_game("easy")
            elif diff_choice == "2":
                play_game("normal")
            elif diff_choice == "3":
                play_game("hard")
            elif diff_choice == "4":
                break
            else:
                print("Invalid choice")
        return
    
    elif main_choice == "2":
        # Automatic solver mode (existing code)
        pass  # Continue with argparse below
    
    elif main_choice == "3":
        print("Goodbye!")
        sys.exit(0)
    
    else:
        print("Invalid choice")
        return
    
    # === AUTOMATIC SOLVER MODE (existing code) ===
    
    parser = argparse.ArgumentParser(description="Sudoku Solver CLI")

    # Required argument: path to the grid file
    parser.add_argument("grid_file", type=str, help="Path to the text file containing the Sudoku grid")

    parser.add_argument("--algo", type=str,
                        choices=["brute", "backtrack", "backtrack_mrv",
                                 "propagation", "propagation_mrv"],
                        default="backtrack",
                        help="Choose the solving algorithm (default: backtrack)")
    parser.add_argument("--gui", action="store_true",
                        help="Display the grid using Pygame after solving")

    parser.add_argument("--benchmark", action="store_true",
                        help="Run all algorithms on the grid, save results to SQLite, show charts")
    parser.add_argument("--results", action="store_true",
                        help="Show historical benchmark results (matplotlib window)")

    # Parse the arguments
    args = parser.parse_args()

    if args.results:
        from results_window import show_results
        show_results()
        return

    # 2. Initialize the grid using Block 1
    print(f"Loading grid from {args.grid_file}...")
    try:
        sudoku = SudokuGrid(args.grid_file)
    except Exception as e:
        print(f"Error loading the grid: {e}")
        sys.exit(1)

    if args.benchmark:
        from benchmark import run_benchmark
        from results_window import show_results
        grid_file_name = os.path.basename(args.grid_file)

        # List of algorithms to benchmark
        algos = [
            ("brute", "Brute Force",
             lambda cb: sudoku.solve_brute_force_animated(cb)),
            ("backtrack", "Backtracking",
             lambda cb: sudoku.solve_backtracking_animated(cb)),
            ("backtrack_mrv", "Backtrack+MRV",
             lambda cb: sudoku.solve_backtracking_mrv(cb)),
            ("propagation", "AC-3",
             lambda cb: sudoku.solve_propagation(cb)),
            ("propagation_mrv", "AC-3+MRV",
             lambda cb: sudoku.solve_propagation_mrv(cb)),
        ]

        print("--- Benchmark on {} ---".format(grid_file_name))
        for algo_name, display_name, solve_func in algos:
            # Restore the grid before each run
            sudoku.grid = [row[:] for row in sudoku.original]
            print("  {} ...".format(display_name), end=" ", flush=True)
            result = run_benchmark(
                sudoku.grid, sudoku.original,
                algo_name, solve_func, grid_file_name
            )
            status = "solved" if result["solved"] else "FAILED"
            print("{:.2f} ms, {} iterations [{}]".format(
                result["time_ms"], result["iterations"], status))

        print("--- Results saved to results.db ---")
        show_results()
        return

    if args.gui:
        draw_sudoku_interactive(sudoku)
        return

    # 3. Terminal-only mode: solve the grid
    print(f"Solving using {args.algo} algorithm...")
    success = False

    if args.algo == "brute":
        success = sudoku.solve_brute_force()
    elif args.algo == "backtrack":
        success = sudoku.solve_backtracking()
    elif args.algo == "backtrack_mrv":
        success = sudoku.solve_backtracking_mrv()
    elif args.algo == "propagation":
        success = sudoku.solve_propagation()
    elif args.algo == "propagation_mrv":
        success = sudoku.solve_propagation_mrv()

    # 4. Display the results
    if success:
        print("Sudoku solved successfully!")
        sudoku.display()
    else:
        print("Failed to solve the Sudoku. The grid might be invalid or unsolvable.")

if __name__ == "__main__":
    main_menu()