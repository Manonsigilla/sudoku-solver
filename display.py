import time
import pygame
import sys
import random
import math
import os
from game_manager import get_or_generate_puzzle, build_candidates, validate_move

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

WINDOW_SIZE = 540
CELL_SIZE = WINDOW_SIZE // 9

COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_PASTEL_GREEN = (144, 238, 144)
COLOR_PASTEL_RED = (255, 192, 192)
COLOR_PASTEL_YELLOW = (255, 255, 153)
COLOR_PASTEL_GRAY = (220, 220, 220)
COLOR_LIGHT_BLUE = (200, 230, 255)
COLOR_BUTTON_BG = (50, 50, 50)
COLOR_BUTTON_HOVER = (100, 100, 100)
COLOR_CELL_BORDER = (100, 100, 100)

# Centralized algorithm color palette (used by display and results_window)
ALGO_PALETTE = {
    "brute":           {"rgb": (231, 76, 60),   "hex": "#e74c3c"},   # Red
    "backtrack":       {"rgb": (52, 152, 219),  "hex": "#3498db"},   # Blue
    "backtrack_mrv":   {"rgb": (46, 204, 113),  "hex": "#2ecc71"},   # Green
    "propagation":     {"rgb": (155, 89, 182),  "hex": "#9b59b6"},   # Purple
    "propagation_mrv": {"rgb": (243, 156, 18),  "hex": "#f39c12"},   # Orange
}

HARD_MODE_COLORS = [
    (144, 238, 144), (255, 192, 192), (255, 255, 153), (220, 220, 220),
    (200, 230, 255), (255, 228, 225), (240, 255, 240), (245, 245, 220),
]

# Font cache with cross-platform fallback (arial may be absent on Linux)
_PREFERRED_FONTS = ["arial", "freesansbold", "dejavusans", "liberationsans"]
_font_cache = {}
_resolved_font_name = None


def _get_font(size, bold=False):
    """Return a cached font with cross-platform fallback."""
    global _resolved_font_name
    key = (size, bold)
    if key not in _font_cache:
        if _resolved_font_name is None:
            available = pygame.font.get_fonts()
            for name in _PREFERRED_FONTS:
                if name in available:
                    _resolved_font_name = name
                    break
            if _resolved_font_name is None:
                _resolved_font_name = ""  # Will use pygame default
        if _resolved_font_name:
            _font_cache[key] = pygame.font.SysFont(_resolved_font_name, size, bold)
        else:
            _font_cache[key] = pygame.font.Font(None, size)
    return _font_cache[key]


class Button:
    def __init__(self, x, y, width, height, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.hovered = False
    
    def draw(self, screen, font):
        color = COLOR_BUTTON_HOVER if self.hovered else COLOR_BUTTON_BG
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, COLOR_WHITE, self.rect, 2)
        text_surf = font.render(self.text, True, COLOR_WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
    
    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)
    
    def update_hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)

class GameState:
    def __init__(self, difficulty: str):
        self.difficulty = difficulty
        self.puzzle_grid, self.solved_grid = get_or_generate_puzzle(difficulty)
        self.current_grid = [row[:] for row in self.puzzle_grid]
        self.original_grid = [row[:] for row in self.puzzle_grid]
        self.candidates = build_candidates(self.current_grid)
        self.stash = {}
        self.cell_status = {}
        self.selected_cell = (0, 0)
        self.hard_mode_cell_colors = {}
        self.generate_hard_mode_colors()
    
    def generate_hard_mode_colors(self):
        self.hard_mode_cell_colors = {(r, c): random.choice(HARD_MODE_COLORS) for r in range(9) for c in range(9)}
    
    def select_cell(self, row: int, col: int):
        if 0 <= row < 9 and 0 <= col < 9:
            self.selected_cell = (row, col)
    
    def add_to_stash(self, num: int):
        row, col = self.selected_cell
        if self.difficulty == "hard":
            return False
        if self.current_grid[row][col] != 0:  # Can't stash if cell already filled
            return False
        
        if self.selected_cell not in self.stash:
            self.stash[self.selected_cell] = set()
        
        if num in self.stash[self.selected_cell]:
            self.stash[self.selected_cell].discard(num)
        else:
            self.stash[self.selected_cell].add(num)
        return True
    
    def validate_move(self, num: int):
        row, col = self.selected_cell
        if self.original_grid[row][col] != 0:
            return False
        if self.current_grid[row][col] != 0:
            return False
        
        status = validate_move(self.current_grid, self.solved_grid, row, col, num)
        
        if status == "correct":
            self.current_grid[row][col] = num
            self.cell_status[(row, col)] = "correct"
            if self.selected_cell in self.stash:
                del self.stash[self.selected_cell]
            if self.difficulty == "hard":
                self.generate_hard_mode_colors()
            return True
        elif status == "multiple" and self.difficulty == "easy":
            self.cell_status[(row, col)] = "multiple"
            return False
        else:
            self.cell_status[(row, col)] = "wrong"
            return False
    
    def is_complete(self):
        return self.current_grid == self.solved_grid

def main_menu():
    pygame.init()
    screen = pygame.display.set_mode((540, 300))
    pygame.display.set_caption("Sudoku Solver - Menu")
    font_large = _get_font(48)
    font_small = _get_font(24)
    
    play_btn = Button(170, 80, 200, 50, "PLAY")
    solver_btn = Button(170, 150, 200, 50, "SOLVER")
    exit_btn = Button(170, 220, 200, 50, "EXIT")
    
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        play_btn.update_hover(mouse_pos)
        solver_btn.update_hover(mouse_pos)
        exit_btn.update_hover(mouse_pos)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if play_btn.is_clicked(event.pos):
                    difficulty_menu()
                elif solver_btn.is_clicked(event.pos):
                    solver_menu_pygame()
                elif exit_btn.is_clicked(event.pos):
                    pygame.quit()
                    sys.exit()
        
        screen.fill(COLOR_WHITE)
        title = font_large.render("SUDOKU", True, COLOR_BLACK)
        screen.blit(title, (120, 20))
        play_btn.draw(screen, font_small)
        solver_btn.draw(screen, font_small)
        exit_btn.draw(screen, font_small)
        pygame.display.flip()

def difficulty_menu():
    screen = pygame.display.get_surface()
    pygame.display.set_mode((540, 300))
    pygame.display.set_caption("Sudoku - Difficulty")
    font_large = _get_font(48)
    font_small = _get_font(24)
    
    easy_btn = Button(170, 80, 200, 50, "EASY")
    normal_btn = Button(170, 150, 200, 50, "NORMAL")
    hard_btn = Button(170, 220, 200, 50, "HARD")
    
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        easy_btn.update_hover(mouse_pos)
        normal_btn.update_hover(mouse_pos)
        hard_btn.update_hover(mouse_pos)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                difficulty = None
                if easy_btn.is_clicked(event.pos):
                    difficulty = "easy"
                elif normal_btn.is_clicked(event.pos):
                    difficulty = "normal"
                elif hard_btn.is_clicked(event.pos):
                    difficulty = "hard"
                
                if difficulty:
                    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
                    result = play_game(difficulty, screen)
                    pygame.display.set_mode((540, 300))
                    # "return" → stay in difficulty menu (loop back)
                    # "menu" or None → go back to main menu
                    if result != "return":
                        return
        
        screen = pygame.display.get_surface()
        screen.fill(COLOR_WHITE)
        title = font_large.render("SELECT DIFFICULTY", True, COLOR_BLACK)
        screen.blit(title, (50, 20))
        easy_btn.draw(screen, font_small)
        normal_btn.draw(screen, font_small)
        hard_btn.draw(screen, font_small)
        pygame.display.flip()

def solver_menu_pygame():
    pygame.display.set_caption("Sudoku - Solver")
    font = _get_font(20)
    font_title = _get_font(28, bold=True)
    font_section = _get_font(18, bold=True)
    
    grids_dir = os.path.join(_BASE_DIR, "grids")
    grid_files = sorted([f for f in os.listdir(grids_dir) if f.endswith(".txt")])
    if not grid_files:
        return
    
    # Layout: grid buttons in a compact list
    grid_y_start = 60
    grid_btn_h = 40
    grid_spacing = 8
    grid_buttons = []
    for i, f in enumerate(grid_files):
        y = grid_y_start + i * (grid_btn_h + grid_spacing)
        grid_buttons.append(Button(50, y, 440, grid_btn_h, f))
    
    # Algorithm section starts after grid buttons
    algo_y_start = grid_y_start + len(grid_files) * (grid_btn_h + grid_spacing) + 40
    
    # All 5 algorithms from solver.py, in 2 columns
    algo_names = [
        "Brute Force",
        "Backtracking",
        "Backtracking MRV",
        "Constraint Propagation",
        "Propagation MRV",
    ]
    col_w = 215
    algo_btn_h = 40
    algo_buttons = []
    for i, name in enumerate(algo_names):
        col = i % 2
        row = i // 2
        x = 50 + col * (col_w + 10)
        y = algo_y_start + row * (algo_btn_h + grid_spacing)
        algo_buttons.append(Button(x, y, col_w, algo_btn_h, name))
    
    # SOLVE button at the bottom
    solve_y = algo_y_start + ((len(algo_names) + 1) // 2) * (algo_btn_h + grid_spacing) + 20
    solve_btn = Button(170, solve_y, 200, 50, "SOLVE")
    results_btn = Button(170, solve_y + 60, 200, 50, "VIEW RESULTS")
    
    # Compute window height to fit everything
    window_h = solve_y + 120
    screen = pygame.display.set_mode((540, window_h))
    
    selected_grid = None
    selected_algo = None
    
    while True:
        mouse_pos = pygame.mouse.get_pos()
        for btn in grid_buttons + algo_buttons + [solve_btn, results_btn]:
            btn.update_hover(mouse_pos)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for btn in grid_buttons:
                    if btn.is_clicked(event.pos):
                        selected_grid = btn.text
                for btn in algo_buttons:
                    if btn.is_clicked(event.pos):
                        selected_algo = btn.text
                
                # SOLVE button only works when both are selected
                if solve_btn.is_clicked(event.pos) and selected_grid and selected_algo:
                    run_solver(os.path.join(_BASE_DIR, "grids", selected_grid), selected_algo)
                
                # Results button
                if results_btn.is_clicked(event.pos):
                    show_results_menu()
        
        screen.fill(COLOR_WHITE)
        
        # Title
        title = font_title.render("SOLVER", True, COLOR_BLACK)
        screen.blit(title, (230, 15))
        
        # Grid section label
        section1 = font_section.render("Select a grid:", True, (80, 80, 80))
        screen.blit(section1, (50, grid_y_start - 22))
        
        # Draw grid buttons with selected highlight
        for btn in grid_buttons:
            btn.draw(screen, font)
            if btn.text == selected_grid:
                pygame.draw.rect(screen, (30, 144, 255), btn.rect, 3)
        
        # Algorithm section label
        section2 = font_section.render("Select an algorithm:", True, (80, 80, 80))
        screen.blit(section2, (50, algo_y_start - 22))
        
        # Draw algorithm buttons with selected highlight
        for btn in algo_buttons:
            btn.draw(screen, font)
            if btn.text == selected_algo:
                pygame.draw.rect(screen, (30, 144, 255), btn.rect, 3)
        
        # Draw SOLVE button (dimmed if selection incomplete)
        if selected_grid and selected_algo:
            solve_btn.draw(screen, font)
        else:
            # Draw dimmed version
            pygame.draw.rect(screen, (130, 130, 130), solve_btn.rect)
            pygame.draw.rect(screen, (180, 180, 180), solve_btn.rect, 2)
            dim_text = font.render("SOLVE", True, (180, 180, 180))
            dim_rect = dim_text.get_rect(center=solve_btn.rect.center)
            screen.blit(dim_text, dim_rect)
        
        # Draw results button   
        results_btn.draw(screen, font)
        
        pygame.display.flip()
class _SolverAborted(Exception):
    """Raised when user presses ESC or closes window during solving."""
    pass

_ALGO_MAP_DISPLAY_TO_KEY = {
    "Brute Force": "brute",
    "Backtracking": "backtrack",
    "Backtracking MRV": "backtrack_mrv",
    "Constraint Propagation": "propagation",
    "Propagation MRV": "propagation_mrv",
}


def _execute_solver(sudoku, algo_func, screen, clock):
    """Run the solver with animated callback. Returns (success, steps, cpu_time)
    or raises _SolverAborted if the user cancels."""
    font_large = _get_font(36)
    font_status = _get_font(20)
    step_count = [0]
    UPDATE_EVERY = 10

    def solver_callback(row, col, num, action):
        step_count[0] += 1
        if step_count[0] % UPDATE_EVERY != 0:
            return
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                raise _SolverAborted()
        screen.fill(COLOR_WHITE)
        draw_solver_grid(screen, sudoku, font_large)
        status = font_status.render(
            f"Solving... step {step_count[0]}  (ESC to cancel)", True, (100, 100, 100)
        )
        screen.blit(status, (10, WINDOW_SIZE - 30))
        pygame.display.flip()
        pygame.time.delay(100)

    start_cpu = time.process_time()
    success = algo_func(sudoku.grid, sudoku.is_valid, solver_callback)
    cpu_time = time.process_time() - start_cpu
    return success, step_count[0], cpu_time


def _save_solver_benchmark(grid_name, algo_key, solve_duration, step_count, sudoku):
    """Save benchmark result to the database."""
    try:
        from benchmark import save_result
        from script import count_empty_cells
        cells_empty = count_empty_cells(sudoku.original)
        save_result(grid_name, algo_key, solve_duration * 1000,
                    step_count, cells_empty, 1)
        print(f"[BENCHMARK] Saved: {grid_name} | {algo_key} | {solve_duration*1000:.1f}ms | {step_count} iterations")
    except Exception as e:
        print(f"[ERROR] Benchmark save failed: {e}")


def _show_solver_result(screen, sudoku, success, step_count, solve_duration,
                        grid_name, algo_key):
    """Display the solver result screen until user presses ESC."""
    clock = pygame.time.Clock()
    font_large = _get_font(36)
    font_status = _get_font(20)
    title_font = _get_font(24, bold=True)
    result_text = "SOLVED!" if success else "NO SOLUTION FOUND"

    # Query best time from database
    try:
        from benchmark import get_results_by_grid
        grid_results = get_results_by_grid(grid_name)
        algo_times = [r["time_ms"] for r in grid_results if r["algo"] == algo_key]
        best_time_ms = min(algo_times) if algo_times else solve_duration * 1000
    except Exception:
        best_time_ms = solve_duration * 1000

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return

        screen.fill(COLOR_WHITE)
        draw_solver_grid(screen, sudoku, font_large)

        title_color = (0, 180, 0) if success else (200, 0, 0)
        title = title_font.render(result_text, True, title_color)
        screen.blit(title, (WINDOW_SIZE // 2 - title.get_width() // 2, 10))

        stats_line = font_status.render(
            f"Steps: {step_count}   Time: {solve_duration:.3f}s", True, (50, 50, 50)
        )
        screen.blit(stats_line, (WINDOW_SIZE // 2 - stats_line.get_width() // 2, 45))

        best_line = font_status.render(
            f"Best: {best_time_ms:.1f}ms", True, (130, 30, 30)
        )
        screen.blit(best_line, (WINDOW_SIZE // 2 - best_line.get_width() // 2, 70))

        footer = font_status.render("Press ESC to go back", True, (150, 150, 150))
        screen.blit(footer, (WINDOW_SIZE // 2 - footer.get_width() // 2, WINDOW_SIZE - 30))

        pygame.display.flip()
        clock.tick(60)


def run_solver(filepath, algo):
    """Orchestrate solving: execute algorithm, save benchmark, show result."""
    from script import SudokuGrid
    from solver import (brute_force_with_callback, backtracking_with_callback,
                        backtracking_mrv, constraint_propagation, propagation_mrv)

    algo_funcs = {
        "Brute Force": brute_force_with_callback,
        "Backtracking": backtracking_with_callback,
        "Backtracking MRV": backtracking_mrv,
        "Constraint Propagation": constraint_propagation,
        "Propagation MRV": propagation_mrv,
    }

    sudoku = SudokuGrid(filepath)
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
    pygame.display.set_caption(f"Solving - {algo}...")
    clock = pygame.time.Clock()

    algo_func = algo_funcs.get(algo, propagation_mrv)
    algo_key = _ALGO_MAP_DISPLAY_TO_KEY.get(algo, "unknown")

    try:
        success, steps, cpu_time = _execute_solver(sudoku, algo_func, screen, clock)
    except _SolverAborted:
        return

    grid_name = os.path.basename(filepath)
    if success:
        _save_solver_benchmark(grid_name, algo_key, cpu_time, steps, sudoku)

    pygame.display.set_caption(f"Solver - {algo} - {'SOLVED!' if success else 'NO SOLUTION'}")
    _show_solver_result(screen, sudoku, success, steps, cpu_time, grid_name, algo_key)
        
def show_results_menu():
    """Show results from SQLite benchmarks in matplotlib window."""
    try:
        from results_window import show_results
        show_results()
    except ImportError as e:
        print(f"[ERROR] Cannot display results: {e}")
        print("[HINT] Install matplotlib and numpy: pip install matplotlib numpy")

def _draw_grid_lines(screen):
    """Draw the 10 horizontal and vertical lines forming the 9x9 sudoku grid.
    Bold lines every 3 cells to delimit 3x3 blocks."""
    for i in range(10):
        thickness = 3 if i % 3 == 0 else 1
        pygame.draw.line(screen, COLOR_BLACK, (i * CELL_SIZE, 0), (i * CELL_SIZE, WINDOW_SIZE), thickness)
        pygame.draw.line(screen, COLOR_BLACK, (0, i * CELL_SIZE), (WINDOW_SIZE, i * CELL_SIZE), thickness)


def draw_solver_grid(screen, sudoku, font):
    _draw_grid_lines(screen)
    
    for row in range(9):
        for col in range(9):
            x, y = col * CELL_SIZE, row * CELL_SIZE
            pygame.draw.rect(screen, COLOR_CELL_BORDER, (x, y, CELL_SIZE, CELL_SIZE), 1)
            if sudoku.grid[row][col] != 0:
                color = COLOR_BLACK if sudoku.original[row][col] != 0 else (0, 100, 200)
                text = font.render(str(sudoku.grid[row][col]), True, color)
                text_rect = text.get_rect(center=(x + CELL_SIZE // 2, y + CELL_SIZE // 2))
                screen.blit(text, text_rect)

def play_game(difficulty: str, screen):
    game_state = GameState(difficulty)
    pygame.display.set_caption(f"Sudoku - {difficulty.upper()}")
    clock = pygame.time.Clock()
    font_large = _get_font(36)
    font_small = _get_font(14)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return
                # Map both top-row and numpad keys to digit values
                digit_keys = {
                    pygame.K_1: 1, pygame.K_2: 2, pygame.K_3: 3,
                    pygame.K_4: 4, pygame.K_5: 5, pygame.K_6: 6,
                    pygame.K_7: 7, pygame.K_8: 8, pygame.K_9: 9,
                    pygame.K_KP_1: 1, pygame.K_KP_2: 2, pygame.K_KP_3: 3,
                    pygame.K_KP_4: 4, pygame.K_KP_5: 5, pygame.K_KP_6: 6,
                    pygame.K_KP_7: 7, pygame.K_KP_8: 8, pygame.K_KP_9: 9,
                }
                if event.key in digit_keys:
                    num = digit_keys[event.key]
                    # Ctrl+digit = validate (definitive), digit alone = stash (pencil mark)
                    if event.mod & pygame.KMOD_CTRL:
                        game_state.validate_move(num)
                    else:
                        game_state.add_to_stash(num)
                elif event.key == pygame.K_RETURN:
                    # Only auto-validate when exactly one number is stashed
                    if game_state.selected_cell in game_state.stash and len(game_state.stash[game_state.selected_cell]) == 1:
                        num = next(iter(game_state.stash[game_state.selected_cell]))
                        game_state.validate_move(num)
                elif event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                    row, col = game_state.selected_cell
                    if event.key == pygame.K_UP:
                        row = (row - 1) % 9
                    elif event.key == pygame.K_DOWN:
                        row = (row + 1) % 9
                    elif event.key == pygame.K_LEFT:
                        col = (col - 1) % 9
                    elif event.key == pygame.K_RIGHT:
                        col = (col + 1) % 9
                    game_state.select_cell(row, col)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if 0 <= x < WINDOW_SIZE and 0 <= y < WINDOW_SIZE:
                    col, row = x // CELL_SIZE, y // CELL_SIZE
                    game_state.select_cell(row, col)
        
        if game_state.is_complete():
            result = show_victory_screen()
            if result == "restart":
                # Create a fresh game with the same difficulty
                game_state = GameState(difficulty)
                continue
            else:
                # "menu" or "return" — propagate to difficulty_menu
                return result
        
        screen.fill(COLOR_WHITE)
        draw_game_grid(screen, game_state, font_large, font_small)
        pygame.display.flip()
        clock.tick(60)

def draw_game_grid(screen, game_state, font_large, font_small):
    _draw_grid_lines(screen)
    
    for row in range(9):
        for col in range(9):
            x, y = col * CELL_SIZE, row * CELL_SIZE
            cell_coord = (row, col)
            
            if game_state.original_grid[row][col] != 0:
                bg_color = COLOR_WHITE
            elif game_state.difficulty == "hard" and cell_coord in game_state.cell_status:
                bg_color = game_state.hard_mode_cell_colors[cell_coord]
            elif cell_coord in game_state.cell_status:
                status = game_state.cell_status[cell_coord]
                bg_color = COLOR_PASTEL_GREEN if status == "correct" else (COLOR_PASTEL_RED if status == "wrong" else COLOR_PASTEL_YELLOW)
            else:
                bg_color = COLOR_WHITE
            
            pygame.draw.rect(screen, bg_color, (x, y, CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(screen, COLOR_CELL_BORDER, (x, y, CELL_SIZE, CELL_SIZE), 1)
            
            if game_state.current_grid[row][col] != 0:
                num = game_state.current_grid[row][col]
                color = COLOR_BLACK if game_state.original_grid[row][col] != 0 else (0, 100, 200)
                text = font_large.render(str(num), True, color)
                text_rect = text.get_rect(center=(x + CELL_SIZE // 2, y + CELL_SIZE // 2))
                screen.blit(text, text_rect)
            
            # Only draw stash marks on empty cells
            if cell_coord in game_state.stash and game_state.current_grid[row][col] == 0:
                stashed = sorted(game_state.stash[cell_coord])
                for idx, num in enumerate(stashed):
                    sx = x + 4 + (idx % 3) * 18
                    sy = y + 2 + (idx // 3) * 16
                    text = font_small.render(str(num), True, (150, 150, 150))
                    screen.blit(text, (sx, sy))
            
            if game_state.selected_cell == cell_coord:
                pygame.draw.rect(screen, (100, 149, 237), (x, y, CELL_SIZE, CELL_SIZE), 3)

def show_victory_screen():
    screen = pygame.display.get_surface()
    font_large = _get_font(48)
    font_small = _get_font(24)
    clock = pygame.time.Clock()
    
    # Three navigation buttons
    btn_w = 140
    spacing = 20
    total_w = btn_w * 3 + spacing * 2
    start_x = (WINDOW_SIZE - total_w) // 2
    btn_y = 280
    menu_btn = Button(start_x, btn_y, btn_w, 50, "MENU")
    return_btn = Button(start_x + btn_w + spacing, btn_y, btn_w, 50, "RETURN")
    restart_btn = Button(start_x + 2 * (btn_w + spacing), btn_y, btn_w, 50, "RESTART")
    
    # Confetti particle system: (x, y, speed, size, color, horizontal_drift)
    confetti_colors = [
        (255, 71, 87), (46, 213, 115), (30, 144, 255), (255, 215, 0),
        (255, 165, 0), (186, 85, 211), (0, 206, 209), (255, 105, 180),
    ]
    confetti = []
    for _ in range(80):
        confetti.append((
            random.randint(0, WINDOW_SIZE),     # x
            random.randint(-WINDOW_SIZE, 0),    # y (start above screen)
            random.uniform(1.0, 3.5),           # fall speed
            random.randint(3, 7),               # size
            random.choice(confetti_colors),      # color
            random.uniform(-0.8, 0.8),          # horizontal drift
        ))
    
    frame_count = 0
    
    while True:
        frame_count += 1
        mouse_pos = pygame.mouse.get_pos()
        menu_btn.update_hover(mouse_pos)
        return_btn.update_hover(mouse_pos)
        restart_btn.update_hover(mouse_pos)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if menu_btn.is_clicked(event.pos):
                    return "menu"
                elif return_btn.is_clicked(event.pos):
                    return "return"
                elif restart_btn.is_clicked(event.pos):
                    return "restart"
        
        screen.fill(COLOR_WHITE)
        
        # Update and draw confetti with drift and respawn
        new_confetti = []
        for x, y, speed, size, color, drift in confetti:
            y += speed
            x += drift
            # Respawn particles that fall off screen
            if y > WINDOW_SIZE:
                y = random.randint(-30, -5)
                x = random.randint(0, WINDOW_SIZE)
            new_confetti.append((x, y, speed, size, color, drift))
            # Draw confetti as small rectangles for visual variety
            rect_w = size
            rect_h = size // 2 if size > 4 else size
            pygame.draw.rect(screen, color, (int(x), int(y), rect_w, rect_h))
        confetti = new_confetti
        
        # Pulsing victory text with scale effect via font size
        pulse = math.sin(frame_count * 0.05) * 0.15 + 1.0  # scale between 0.85 and 1.15
        pulse_size = int(48 * pulse)
        pulse_font = _get_font(pulse_size, bold=True)
        # Color cycles through green shades
        green_val = int(180 + 75 * math.sin(frame_count * 0.03))
        text = pulse_font.render("PUZZLE SOLVED!", True, (0, min(green_val, 255), 0))
        text_rect = text.get_rect(center=(WINDOW_SIZE // 2, 120))
        screen.blit(text, text_rect)
        
        # Subtitle with fade-in
        alpha = min(255, frame_count * 4)
        sub_surf = font_small.render("Congratulations!", True, (100, 100, 100))
        sub_surf.set_alpha(alpha)
        sub_rect = sub_surf.get_rect(center=(WINDOW_SIZE // 2, 180))
        screen.blit(sub_surf, sub_rect)
        
        # Draw buttons
        menu_btn.draw(screen, font_small)
        return_btn.draw(screen, font_small)
        restart_btn.draw(screen, font_small)
        
        # Button labels below
        hint_font = _get_font(12)
        hints = [("Main Menu", menu_btn), ("Difficulty", return_btn), ("Same Level", restart_btn)]
        for hint_text, btn in hints:
            hint_surf = hint_font.render(hint_text, True, (140, 140, 140))
            hint_rect = hint_surf.get_rect(center=(btn.rect.centerx, btn.rect.bottom + 14))
            screen.blit(hint_surf, hint_rect)
        
        pygame.display.flip()
        clock.tick(60)