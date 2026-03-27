import time
import pygame
import sys
import random
import math
import os
from game_manager import get_or_generate_puzzle, build_candidates, validate_move

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

HARD_MODE_COLORS = [
    (144, 238, 144), (255, 192, 192), (255, 255, 153), (220, 220, 220),
    (200, 230, 255), (255, 228, 225), (240, 255, 240), (245, 245, 220),
]

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
    
    def randomize_hard_colors(self):
        self.generate_hard_mode_colors()
    
    def select_cell(self, row: int, col: int):
        if 0 <= row < 9 and 0 <= col < 9:
            self.selected_cell = (row, col)
    
    def add_to_stash(self, num: int):
        if not self.selected_cell:
            return False
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
        if not self.selected_cell:
            return False
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
                self.randomize_hard_colors()
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
    font_large = pygame.font.SysFont("arial", 48)
    font_small = pygame.font.SysFont("arial", 24)
    
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
    font_large = pygame.font.SysFont("arial", 48)
    font_small = pygame.font.SysFont("arial", 24)
    
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
    font = pygame.font.SysFont("arial", 20)
    font_title = pygame.font.SysFont("arial", 28, bold=True)
    font_section = pygame.font.SysFont("arial", 18, bold=True)
    
    import os
    grid_files = sorted([f for f in os.listdir("grids") if f.endswith(".txt")])
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
                    run_solver(f"grids/{selected_grid}", selected_algo)
                
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

def run_solver(filepath, algo):
    from script import SudokuGrid
    from solver import (brute_force_with_callback, backtracking_with_callback,
                        backtracking_mrv, constraint_propagation, propagation_mrv)
    
    # Map display names to solver functions
    algo_map = {
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
    font_large = pygame.font.SysFont("arial", 36)
    font_status = pygame.font.SysFont("arial", 20)
    
    # Step counter for throttled rendering
    step_count = [0]
    UPDATE_EVERY = 10  # Redraw every N solver steps
    
    def solver_callback(row, col, num, action):
        """Called by the solver on each place/remove step.
        Processes events to keep the window responsive and
        redraws the grid periodically for a live animation."""
        step_count[0] += 1
        
        if step_count[0] % UPDATE_EVERY != 0:
            return
        
        # Process Pygame events to prevent "not responding"
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                raise _SolverAborted()
        
        # Redraw the grid to show progress
        screen.fill(COLOR_WHITE)
        draw_solver_grid(screen, sudoku, font_large)
        status = font_status.render(
            f"Solving... step {step_count[0]}  (ESC to cancel)", True, (100, 100, 100)
        )
        screen.blit(status, (10, WINDOW_SIZE - 30))
        pygame.display.flip()
        time.sleep(0.1) # Slow down for visibility; remove or adjust as needed
    
    algo_func = algo_map.get(algo, propagation_mrv)
    
    start_time_perf = pygame.time.get_ticks()
    
    try:
        success = algo_func(sudoku.grid, sudoku.is_valid, solver_callback)
    except _SolverAborted:
        return
    
    end_time_perf = pygame.time.get_ticks()
    solve_duration = (end_time_perf - start_time_perf) / 1000.0
    
    # Save benchmark
    from benchmark import run_benchmark
    
    grid_name = os.path.basename(filepath)
    # run_benchmark(grid, original, algo_name, solve_func, grid_file)
    
    try:
        # Map display names to algo_name for database
        algo_key = {
            "Brute Force": "brute",
            "Backtracking": "backtrack",
            "Backtracking MRV": "backtrack_mrv",
            "Constraint Propagation": "propagation",
            "Propagation MRV": "propagation_mrv",
        }.get(algo, "unknown")
        
        # Count empty cells
        cells_empty = sum(1 for r in sudoku.original for c in r if c == 0)
        
        # Save directly to benchmark
        import sqlite3
        from benchmark import DB_PATH, _init_db
        _init_db()
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "INSERT INTO benchmarks (grid_file, algo, time_ms, iterations, cells_empty, solved) VALUES (?, ?, ?, ?, ?, ?)",
            (grid_name, algo_key, solve_duration * 1000, step_count[0], cells_empty, int(success))
        )
        conn.commit()
        conn.close()
        print(f"[BENCHMARK] Saved: {grid_name} | {algo} | {solve_duration*1000:.1f}ms | {step_count[0]} iterations")
    except Exception as e:
        print(f"[ERROR] Benchmark save failed: {e}")
    
    # Show final result
    result_text = "SOLVED!" if success else "NO SOLUTION FOUND"
    pygame.display.set_caption(f"Solver - {algo} - {result_text}")
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
        
        screen.fill(COLOR_WHITE)
        draw_solver_grid(screen, sudoku, font_large)
        
        # Display main result
        title_color = (0, 180, 0) if success else (200, 0, 0)
        title = pygame.font.SysFont("arial", 24, bold=True).render(
            f"{result_text}", True, title_color
        )
        screen.blit(title, (WINDOW_SIZE // 2 - title.get_width() // 2, 10))
        
        # Display stats
        stats_line = font_status.render(
            f"Steps: {step_count[0]}   Time: {solve_duration:.3f}s", True, (50, 50, 50)
        )
        screen.blit(stats_line, (WINDOW_SIZE // 2 - stats_line.get_width() // 2, 45))
        
        # Display Best Time
        best_line = font_status.render(
            f"Time: {solve_duration:.3f}s", True, (130, 30, 30)
        )
        screen.blit(best_line, (WINDOW_SIZE // 2 - best_line.get_width() // 2, 70))
        
        footer = font_status.render("Press ESC to go back", True, (150, 150, 150))
        screen.blit(footer, (WINDOW_SIZE // 2 - footer.get_width() // 2, WINDOW_SIZE - 30))
        
        pygame.display.flip()
        clock.tick(60)
        
def show_results_menu():
        """Show results from SQLite benchmarks in matplotlib window."""
        try:
            from results_window import show_results
            show_results()
        except ImportError:
            pass

def draw_solver_grid(screen, sudoku, font):
    for i in range(10):
        thickness = 3 if i % 3 == 0 else 1
        pygame.draw.line(screen, COLOR_BLACK, (i * CELL_SIZE, 0), (i * CELL_SIZE, WINDOW_SIZE), thickness)
        pygame.draw.line(screen, COLOR_BLACK, (0, i * CELL_SIZE), (WINDOW_SIZE, i * CELL_SIZE), thickness)
    
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
    font_large = pygame.font.SysFont("arial", 36)
    font_small = pygame.font.SysFont("arial", 14)
    
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
    for i in range(10):
        thickness = 3 if i % 3 == 0 else 1
        pygame.draw.line(screen, COLOR_BLACK, (i * CELL_SIZE, 0), (i * CELL_SIZE, WINDOW_SIZE), thickness)
        pygame.draw.line(screen, COLOR_BLACK, (0, i * CELL_SIZE), (WINDOW_SIZE, i * CELL_SIZE), thickness)
    
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
    font_large = pygame.font.SysFont("arial", 48)
    font_small = pygame.font.SysFont("arial", 24)
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
        pulse_font = pygame.font.SysFont("arial", pulse_size, bold=True)
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
        hint_font = pygame.font.SysFont("arial", 12)
        hints = [("Main Menu", menu_btn), ("Difficulty", return_btn), ("Same Level", restart_btn)]
        for hint_text, btn in hints:
            hint_surf = hint_font.render(hint_text, True, (140, 140, 140))
            hint_rect = hint_surf.get_rect(center=(btn.rect.centerx, btn.rect.bottom + 14))
            screen.blit(hint_surf, hint_rect)
        
        pygame.display.flip()
        clock.tick(60)