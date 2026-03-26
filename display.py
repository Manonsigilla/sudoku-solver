import pygame
import sys
import time

GRID_SIZE = 540                    # Grid drawing area (unchanged)
WINDOW_SIZE = GRID_SIZE            # Alias for compatibility with draw_grid_lines
CELL_SIZE = GRID_SIZE // 9         # 60 pixels per cell
WINDOW_WIDTH = 720                 # Wider window for the side panel
WINDOW_HEIGHT = 600                # Height for grid + iteration counter
PANEL_X = GRID_SIZE + 15           # X position of the side panel start

# Background and line colors
BACKGROUND_COLOR = (255, 255, 255)  # White
LINE_COLOR = (0, 0, 0)              # Black

# Colors for original/solved distinction and visual indicators
ORIGINAL_COLOR = (0, 0, 0)         # Black: digits present in the initial grid
SOLVED_COLOR = (0, 0, 200)         # Blue: digits placed by the algorithm
CURRENT_COLOR = (255, 255, 100)    # Yellow: cell currently being processed
BACKTRACK_COLOR = (255, 100, 100)  # Red: cell being backtracked
BUTTON_COLOR = (210, 210, 210)     # Light gray: buttons at rest
BUTTON_HOVER_COLOR = (180, 180, 180)  # Gray: buttons on hover
BUTTON_TEXT_COLOR = (30, 30, 30)   # Button text
SOLVE_BUTTON_COLOR = (74, 158, 255)   # Blue: Solve button
SOLVE_BUTTON_TEXT = (255, 255, 255)    # White: Solve button text


# =============================================================================
# Button class
# =============================================================================

class Button:
    """Clickable rectangular button with centered text and hover effect."""

    def __init__(self, x, y, width, height, text, color=None, text_color=None):
        """Create a button at position (x, y) with the given dimensions."""
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color if color else BUTTON_COLOR
        self.text_color = text_color if text_color else BUTTON_TEXT_COLOR
        self.hovered = False

    def draw(self, screen):
        """Draw the button on screen with hover effect."""
        # Background color: darker if mouse is over it
        bg_color = BUTTON_HOVER_COLOR if self.hovered else self.color
        pygame.draw.rect(screen, bg_color, self.rect, border_radius=6)
        # Border
        pygame.draw.rect(screen, (150, 150, 150), self.rect, width=1, border_radius=6)
        # Centered text inside the button
        font = pygame.font.SysFont("arial", 16, bold=True)
        text_surface = font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def update_hover(self, mouse_pos):
        """Update hover state based on mouse position."""
        self.hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, pos):
        """Return True if pos is inside the button."""
        return self.rect.collidepoint(pos)


# =============================================================================
# Grid drawing functions
# =============================================================================

def draw_grid_lines(screen):
    """Draws the 9x9 grid lines on the screen."""
    for i in range(10):
        # Every 3rd line is thicker to separate the 3x3 blocks
        thickness = 3 if i % 3 == 0 else 1

        # Draw vertical lines
        pygame.draw.line(screen, LINE_COLOR, (i * CELL_SIZE, 0), (i * CELL_SIZE, WINDOW_SIZE), thickness)
        # Draw horizontal lines
        pygame.draw.line(screen, LINE_COLOR, (0, i * CELL_SIZE), (WINDOW_SIZE, i * CELL_SIZE), thickness)



def draw_numbers_colored(screen, sudoku, current_cell=None, backtrack_cell=None):
    """Draw the grid numbers with visual distinction:
    - Original digits: black (ORIGINAL_COLOR)
    - Digits solved by the algorithm: blue (SOLVED_COLOR)
    - Cell currently being processed: yellow background (CURRENT_COLOR)
    - Cell being backtracked: red background (BACKTRACK_COLOR)

    Parameters:
        screen         -- Pygame surface
        sudoku         -- SudokuGrid object (to access .grid and .original)
        current_cell   -- tuple (row, col) of the current cell, or None
        backtrack_cell -- tuple (row, col) of the backtrack cell, or None
    """
    font = pygame.font.SysFont("arial", 40)

    for row in range(9):
        for col in range(9):
            # Draw colored background for visual indicators
            if current_cell == (row, col):
                # Yellow background for the current cell
                cell_rect = pygame.Rect(
                    col * CELL_SIZE + 1, row * CELL_SIZE + 1,
                    CELL_SIZE - 2, CELL_SIZE - 2)
                pygame.draw.rect(screen, CURRENT_COLOR, cell_rect)
            elif backtrack_cell == (row, col):
                # Red background for the backtrack cell
                cell_rect = pygame.Rect(
                    col * CELL_SIZE + 1, row * CELL_SIZE + 1,
                    CELL_SIZE - 2, CELL_SIZE - 2)
                pygame.draw.rect(screen, BACKTRACK_COLOR, cell_rect)

            num = sudoku.grid[row][col]
            if num == 0:
                continue  # Empty cell, nothing to draw

            # Choose text color based on digit origin
            if sudoku.original[row][col] != 0:
                color = ORIGINAL_COLOR   # Initial grid digit: black
            else:
                color = SOLVED_COLOR     # Algorithm-added digit: blue

            # Render and center the text in the cell
            text_surface = font.render(str(num), True, color)
            text_rect = text_surface.get_rect()
            text_rect.center = (
                col * CELL_SIZE + CELL_SIZE // 2,
                row * CELL_SIZE + CELL_SIZE // 2)
            screen.blit(text_surface, text_rect)


def draw_iteration_counter(screen, iterations, elapsed_ms=0.0):
    """Display the iteration counter and elapsed time below the grid."""
    font = pygame.font.SysFont("arial", 18)
    # Iteration counter
    text = "Iterations: {:,}".format(iterations).replace(",", " ")
    text_surface = font.render(text, True, (60, 60, 60))
    screen.blit(text_surface, (10, GRID_SIZE + 10))
    # Elapsed time
    if elapsed_ms > 0:
        time_text = "Time: {:.1f} ms".format(elapsed_ms)
        time_surface = font.render(time_text, True, (60, 60, 60))
        screen.blit(time_surface, (250, GRID_SIZE + 10))


def draw_algo_info(screen, algo_name):
    """Display the selected algorithm name in the side panel."""
    font_small = pygame.font.SysFont("arial", 12)
    label = font_small.render("Algorithm:", True, (100, 100, 100))
    screen.blit(label, (PANEL_X, 130))
    font = pygame.font.SysFont("arial", 15, bold=True)
    name_surface = font.render(algo_name, True, (100, 50, 150))
    screen.blit(name_surface, (PANEL_X, 148))


# =============================================================================
# Available algorithms and interactive window
# =============================================================================

ALGO_LIST = [
    ("brute", "Brute Force"),
    ("backtrack", "Backtracking"),
    ("backtrack_mrv", "Backtrack+MRV"),
    ("propagation", "AC-3"),
    ("propagation_mrv", "AC-3+MRV"),
]


def draw_sudoku_interactive(sudoku):
    """Interactive Pygame window with Solve, Reset, algorithm selector,
    real-time solving animation, and visual indicators.

    Parameters:
        sudoku -- SudokuGrid object (not a raw grid list)

    Buttons:
        Solve   -- start solving with step-by-step animation
        Reset   -- restore the grid to its initial state
        Algo    -- cycle between the 5 available algorithms
        Results -- open the matplotlib results window
    """
    pygame.init()

    # Create the wider window
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Sudoku Solver")

    # --- Internal state ---
    algo_index = 1                # Default algorithm: Backtracking
    iterations = 0                # Current iteration counter
    elapsed_ms = 0                # Elapsed time
    solving = False               # True during solving (blocks clicks)
    cancelled = False             # True when user presses Escape to cancel
    current_cell = None           # Cell currently being processed (yellow highlight)
    backtrack_cell = None         # Cell being backtracked (red highlight)
    # Save the original grid for reset
    # Uses sudoku.original (the initial grid loaded from file),
    # not sudoku.grid which may already be solved if main.py solved it before
    original_grid_backup = [row[:] for row in sudoku.original]

    # --- Buttons ---
    btn_solve = Button(PANEL_X, 20, 145, 42, "Solve",
                       color=SOLVE_BUTTON_COLOR, text_color=SOLVE_BUTTON_TEXT)
    btn_reset = Button(PANEL_X, 72, 145, 42, "Reset")
    btn_algo = Button(PANEL_X, 175, 145, 42, "< Change >")
    btn_results = Button(PANEL_X, 240, 145, 42, "Results")

    # --- Internal redraw function ---
    def redraw():
        """Redraw the entire window (grid, buttons, counter)."""
        screen.fill(BACKGROUND_COLOR)
        draw_grid_lines(screen)
        draw_numbers_colored(screen, sudoku, current_cell, backtrack_cell)
        # Side panel
        btn_solve.draw(screen)
        btn_reset.draw(screen)
        draw_algo_info(screen, ALGO_LIST[algo_index][1])
        btn_algo.draw(screen)
        btn_results.draw(screen)
        # Iteration counter at the bottom
        draw_iteration_counter(screen, iterations, elapsed_ms)

    # --- Animation callback ---
    def animation_callback(row, col, num, action):
        """Callback called by the algorithm at each step.
        Updates the display and pauses for animation.
        Raises KeyboardInterrupt if the user presses Escape to cancel."""
        nonlocal iterations, current_cell, backtrack_cell, cancelled

        iterations += 1

        # Update visual indicators
        if action == "place":
            current_cell = (row, col)
            backtrack_cell = None
        elif action == "remove":
            backtrack_cell = (row, col)
            current_cell = None

        # Redraw the screen
        redraw()
        pygame.display.flip()

        # Process pygame events during animation
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                cancelled = True
                raise KeyboardInterrupt("Solving cancelled by user")

        # Pause to make the animation visible (~50 fps)
        time.sleep(0.02)

    # --- Main loop ---
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and not solving:
                pos = event.pos

                # Click on Solve: start solving
                if btn_solve.is_clicked(pos):
                    solving = True
                    cancelled = False
                    iterations = 0
                    elapsed_ms = 0
                    current_cell = None
                    backtrack_cell = None

                    # Choose the solve method based on the selected algorithm
                    algo_key = ALGO_LIST[algo_index][0]
                    start_time = time.perf_counter()
                    success = False

                    try:
                        if algo_key == "brute":
                            success = sudoku.solve_brute_force_animated(animation_callback)
                        elif algo_key == "backtrack":
                            success = sudoku.solve_backtracking_animated(animation_callback)
                        elif algo_key == "backtrack_mrv":
                            success = sudoku.solve_backtracking_mrv(animation_callback)
                        elif algo_key == "propagation":
                            success = sudoku.solve_propagation(animation_callback)
                        elif algo_key == "propagation_mrv":
                            success = sudoku.solve_propagation_mrv(animation_callback)
                    except KeyboardInterrupt:
                        # User pressed Escape: restore the grid and cancel
                        sudoku.grid = [row[:] for row in original_grid_backup]
                        cancelled = True

                    elapsed_ms = (time.perf_counter() - start_time) * 1000
                    solving = False
                    current_cell = None
                    backtrack_cell = None

                    # Print the result to the terminal
                    if cancelled:
                        print("[{}] {} : cancelled after {:.1f} ms, {} iterations".format(
                            algo_key, ALGO_LIST[algo_index][1],
                            elapsed_ms, iterations))
                    else:
                        status = "solved" if success else "failed"
                        print("[{}] {} : {:.1f} ms, {} iterations [{}]".format(
                            algo_key, ALGO_LIST[algo_index][1],
                            elapsed_ms, iterations, status))

                # Click on Reset: restore the original grid
                elif btn_reset.is_clicked(pos):
                    sudoku.grid = [row[:] for row in original_grid_backup]
                    iterations = 0
                    elapsed_ms = 0
                    current_cell = None
                    backtrack_cell = None

                # Click on Algo: switch to the next algorithm
                elif btn_algo.is_clicked(pos):
                    algo_index = (algo_index + 1) % len(ALGO_LIST)

                # Click on Results: open the matplotlib results window
                elif btn_results.is_clicked(pos):
                    try:
                        from results_window import show_results
                        show_results()
                    except ImportError:
                        print("[WARN] matplotlib not installed. "
                              "Run: pip install matplotlib")

        # Update button hover effects
        if not solving:
            btn_solve.update_hover(mouse_pos)
            btn_reset.update_hover(mouse_pos)
            btn_algo.update_hover(mouse_pos)
            btn_results.update_hover(mouse_pos)

        # Redraw and refresh the display
        redraw()
        pygame.display.flip()

        # Limit framerate to avoid overloading the CPU
        pygame.time.Clock().tick(30)

    # Clean shutdown
    pygame.quit()
