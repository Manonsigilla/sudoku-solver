import time
import pygame
import sys
import random
import math
import os
from game_manager import get_or_generate_puzzle, build_candidates, validate_move

WINDOW_SIZE = 540
CELL_SIZE = WINDOW_SIZE // 9

# ============================================================================
# Enhanced Color Palette - Vibrant and Modern
# ============================================================================

COLOR_BG_PRIMARY = (15, 23, 42)
COLOR_BG_SECONDARY = (30, 41, 82)
COLOR_BG_ACCENT = (45, 64, 127)

COLOR_VIBRANT_RED = (255, 71, 87)
COLOR_VIBRANT_GREEN = (46, 213, 115)
COLOR_VIBRANT_BLUE = (30, 144, 255)
COLOR_VIBRANT_YELLOW = (255, 215, 0)
COLOR_VIBRANT_ORANGE = (255, 165, 0)
COLOR_VIBRANT_PURPLE = (186, 85, 211)
COLOR_VIBRANT_CYAN = (0, 206, 209)
COLOR_VIBRANT_PINK = (255, 105, 180)

COLOR_PASTEL_GREEN = (144, 238, 144)
COLOR_PASTEL_RED = (255, 192, 192)
COLOR_PASTEL_YELLOW = (255, 255, 153)

COLOR_BUTTON_PRIMARY = (52, 152, 219)
COLOR_BUTTON_HOVER = (41, 128, 185)
COLOR_BUTTON_ACTIVE = (30, 105, 152)
COLOR_BUTTON_SECONDARY = (155, 89, 182)
COLOR_BUTTON_SECONDARY_HOVER = (142, 68, 173)
COLOR_BUTTON_SUCCESS = (46, 204, 113)
COLOR_BUTTON_SUCCESS_HOVER = (39, 174, 96)

COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_TEXT_LIGHT = (230, 240, 250)
COLOR_CELL_BORDER = (100, 100, 100)

HARD_MODE_COLORS = [
    COLOR_VIBRANT_RED, COLOR_VIBRANT_GREEN, COLOR_VIBRANT_BLUE,
    COLOR_VIBRANT_YELLOW, COLOR_VIBRANT_ORANGE, COLOR_VIBRANT_PURPLE,
    COLOR_VIBRANT_CYAN, COLOR_VIBRANT_PINK, (100, 200, 255),
]


def draw_gradient_background(screen, width, height, color1, color2):
    """Draw a smooth gradient background from color1 to color2."""
    for y in range(height):
        ratio = y / height
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (width, y))


def draw_decorative_circles(screen, width, height):
    """Draw subtle decorative circles in background corners."""
    overlay = pygame.Surface((width, height))
    overlay.set_alpha(10)
    overlay.fill(COLOR_VIBRANT_BLUE)
    pygame.draw.circle(overlay, COLOR_VIBRANT_CYAN, (width - 50, -50), 150)
    screen.blit(overlay, (0, 0))
    
    overlay.fill(COLOR_BG_PRIMARY)
    pygame.draw.circle(overlay, COLOR_VIBRANT_PURPLE, (-100, height + 50), 200)
    screen.blit(overlay, (0, 0))


class Button:
    """Modern button with hover effects, shadow, and gradient appearance."""
    
    def __init__(self, x, y, width, height, text, button_type="primary"):
        """Initialize a modern button."""
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.hovered = False
        self.pressed = False
        self.button_type = button_type
    
    def draw(self, screen, font):
        """Draw button with gradient background, shadow, and hover animation."""
        shadow_rect = self.rect.inflate(4, 4)
        shadow_rect.topleft = (self.rect.x + 2, self.rect.y + 2)
        pygame.draw.rect(screen, (0, 0, 0, 100), shadow_rect, border_radius=8)
        
        if self.button_type == "secondary":
            base_color = COLOR_BUTTON_SECONDARY
            hover_color = COLOR_BUTTON_SECONDARY_HOVER
        elif self.button_type == "success":
            base_color = COLOR_BUTTON_SUCCESS
            hover_color = COLOR_BUTTON_SUCCESS_HOVER
        else:
            base_color = COLOR_BUTTON_PRIMARY
            hover_color = COLOR_BUTTON_HOVER
        
        if self.pressed:
            current_color = COLOR_BUTTON_ACTIVE if self.button_type == "primary" else hover_color
        elif self.hovered:
            current_color = hover_color
        else:
            current_color = base_color
        
        pygame.draw.rect(screen, current_color, self.rect, border_radius=12)
        
        gradient_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, self.rect.height // 2)
        overlay_surface = pygame.Surface((gradient_rect.width, gradient_rect.height))
        overlay_surface.set_alpha(30)
        overlay_surface.fill(COLOR_WHITE)
        screen.blit(overlay_surface, gradient_rect)
        
        border_color = COLOR_VIBRANT_BLUE if self.hovered else (100, 100, 100)
        pygame.draw.rect(screen, border_color, self.rect, 3, border_radius=12)
        
        text_surf = font.render(self.text, True, COLOR_TEXT_LIGHT)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
    
    def is_clicked(self, pos):
        """Check if button was clicked at position."""
        return self.rect.collidepoint(pos)
    
    def update_hover(self, pos):
        """Update hover state based on mouse position."""
        self.hovered = self.rect.collidepoint(pos)


class GameState:
    """Manages game state including grid, moves, and difficulty level."""
    
    def __init__(self, difficulty: str):
        """Initialize game state."""
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
        """Generate random vibrant colors for hard mode cells."""
        self.hard_mode_cell_colors = {(r, c): random.choice(HARD_MODE_COLORS) for r in range(9) for c in range(9)}
    
    def randomize_hard_colors(self):
        """Randomize colors for hard mode."""
        self.generate_hard_mode_colors()
    
    def select_cell(self, row: int, col: int):
        """Select a cell on the grid."""
        if 0 <= row < 9 and 0 <= col < 9:
            self.selected_cell = (row, col)
    
    def add_to_stash(self, num: int):
        """Add a number to the stash (pencil marks) for the selected cell."""
        if not self.selected_cell:
            return False
        row, col = self.selected_cell
        if self.difficulty == "hard":
            return False
        if self.current_grid[row][col] != 0:
            return False
        
        if self.selected_cell not in self.stash:
            self.stash[self.selected_cell] = set()
        
        if num in self.stash[self.selected_cell]:
            self.stash[self.selected_cell].discard(num)
        else:
            self.stash[self.selected_cell].add(num)
        return True
    
    def validate_move(self, num: int):
        """Validate and place a number in the selected cell."""
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
        """Check if the puzzle is completely solved."""
        return self.current_grid == self.solved_grid


def main_menu():
    """Display main menu with Play, Solver, and Exit options."""
    pygame.init()
    screen = pygame.display.set_mode((540, 300))
    pygame.display.set_caption("Sudoku Solver - Menu")
    font_large = pygame.font.SysFont("arial", 48, bold=True)
    font_small = pygame.font.SysFont("arial", 24)
    
    play_btn = Button(170, 80, 200, 50, "PLAY", "primary")
    solver_btn = Button(170, 150, 200, 50, "SOLVER", "secondary")
    exit_btn = Button(170, 220, 200, 50, "EXIT", "success")
    
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
        
        draw_gradient_background(screen, 540, 300, COLOR_BG_PRIMARY, COLOR_BG_ACCENT)
        draw_decorative_circles(screen, 540, 300)
        
        title = font_large.render("SUDOKU", True, COLOR_VIBRANT_BLUE)
        title_rect = title.get_rect(center=(270, 30))
        glow_title = font_large.render("SUDOKU", True, COLOR_VIBRANT_CYAN)
        glow_title.set_alpha(50)
        screen.blit(glow_title, (title_rect.x + 2, title_rect.y + 2))
        screen.blit(title, title_rect)
        
        play_btn.draw(screen, font_small)
        solver_btn.draw(screen, font_small)
        exit_btn.draw(screen, font_small)
        
        pygame.display.flip()


def difficulty_menu():
    """Display difficulty selection menu."""
    screen = pygame.display.get_surface()
    pygame.display.set_mode((540, 300))
    pygame.display.set_caption("Sudoku - Difficulty")
    font_large = pygame.font.SysFont("arial", 48, bold=True)
    font_small = pygame.font.SysFont("arial", 24)
    
    easy_btn = Button(170, 80, 200, 50, "EASY", "success")
    normal_btn = Button(170, 150, 200, 50, "NORMAL", "primary")
    hard_btn = Button(170, 220, 200, 50, "HARD", "secondary")
    
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
                    if result != "return":
                        return
        
        screen = pygame.display.get_surface()
        draw_gradient_background(screen, 540, 300, COLOR_BG_PRIMARY, COLOR_BG_ACCENT)
        draw_decorative_circles(screen, 540, 300)
        
        title = font_large.render("SELECT DIFFICULTY", True, COLOR_VIBRANT_YELLOW)
        title_rect = title.get_rect(center=(270, 30))
        screen.blit(title, title_rect)
        
        easy_btn.draw(screen, font_small)
        normal_btn.draw(screen, font_small)
        hard_btn.draw(screen, font_small)
        
        pygame.display.flip()


def solver_menu_pygame():
    """Display solver menu with grid and algorithm selection."""
    pygame.display.set_caption("Sudoku - Solver")
    font = pygame.font.SysFont("arial", 16)
    font_title = pygame.font.SysFont("arial", 32, bold=True)
    font_section = pygame.font.SysFont("arial", 20, bold=True)
    
    import os
    grid_files = sorted([f for f in os.listdir("grids") if f.endswith(".txt")])
    if not grid_files:
        return
    
    window_w = 700
    window_h = 750
    screen = pygame.display.set_mode((window_w, window_h))
    
    # GRID BUTTONS
    grid_list_y = 80
    grid_list_h = 200
    grid_btn_h = 40
    grid_btn_w = 620
    grid_btn_x = 40
    scroll_offset = 0
    
    grid_buttons = []
    for i, f in enumerate(grid_files):
        y = grid_list_y + i * (grid_btn_h + 8)
        btn = Button(grid_btn_x, y, grid_btn_w, grid_btn_h, f, "primary")
        grid_buttons.append(btn)
    
    # ALGORITHM BUTTONS
    algo_list_y = grid_list_y + grid_list_h + 50
    algo_names = [
        "Brute Force",
        "Backtracking",
        "Backtracking MRV",
        "Constraint Propagation",
        "Propagation MRV",
    ]
    algo_btn_w = 140
    algo_btn_h = 45
    algo_buttons = []
    for i, name in enumerate(algo_names):
        col = i % 2
        row = i // 2
        x = 40 if col == 0 else 380
        y = algo_list_y + row * 55
        algo_buttons.append(Button(x, y, algo_btn_w, algo_btn_h, name, "secondary"))
    
    # CONTROL BUTTONS
    buttons_y = algo_list_y + 3 * 55 + 20
    solve_btn = Button(150, buttons_y, 140, 50, "SOLVE", "success")
    results_btn = Button(410, buttons_y, 140, 50, "RESULTS", "primary")
    
    selected_grid = None
    selected_algo = None
    
    while True:
        mouse_pos = pygame.mouse.get_pos()
        
        for btn in algo_buttons + [solve_btn, results_btn]:
            btn.update_hover(mouse_pos)
        
        for btn in grid_buttons:
            btn_screen_y = btn.rect.y - scroll_offset
            visible = grid_list_y <= btn_screen_y < grid_list_y + grid_list_h
            if visible:
                temp_rect = pygame.Rect(btn.rect.x, btn_screen_y, btn.rect.width, btn.rect.height)
                btn.hovered = temp_rect.collidepoint(mouse_pos)
            else:
                btn.hovered = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    scroll_offset = max(0, scroll_offset - 40)
                elif event.button == 5:
                    max_scroll = max(0, len(grid_buttons) * (grid_btn_h + 8) - grid_list_h)
                    scroll_offset = min(max_scroll, scroll_offset + 40)
                
                for btn in grid_buttons:
                    btn_screen_y = btn.rect.y - scroll_offset
                    visible = grid_list_y <= btn_screen_y < grid_list_y + grid_list_h
                    if visible:
                        temp_rect = pygame.Rect(btn.rect.x, btn_screen_y, btn.rect.width, btn.rect.height)
                        if temp_rect.collidepoint(event.pos):
                            selected_grid = btn.text
                
                for btn in algo_buttons:
                    if btn.is_clicked(event.pos):
                        selected_algo = btn.text
                
                if solve_btn.is_clicked(event.pos) and selected_grid and selected_algo:
                    run_solver(f"grids/{selected_grid}", selected_algo)
                    # ✅ Réadapter la fenêtre après résolution
                    screen = pygame.display.set_mode((window_w, window_h))
                    pygame.display.set_caption("Sudoku - Solver")
                
                if results_btn.is_clicked(event.pos):
                    show_results_menu()
        
        draw_gradient_background(screen, window_w, window_h, COLOR_BG_PRIMARY, COLOR_BG_ACCENT)
        draw_decorative_circles(screen, window_w, window_h)
        
        title = font_title.render("SOLVER", True, COLOR_VIBRANT_BLUE)
        title_rect = title.get_rect(center=(window_w // 2, 30))
        screen.blit(title, title_rect)
        
        section1 = font_section.render("Select a grid:", True, COLOR_VIBRANT_YELLOW)
        screen.blit(section1, (grid_btn_x, grid_list_y - 35))
        
        panel_rect = pygame.Rect(grid_btn_x - 5, grid_list_y - 5, grid_btn_w + 10, grid_list_h + 10)
        pygame.draw.rect(screen, COLOR_BG_SECONDARY, panel_rect, border_radius=8)
        pygame.draw.rect(screen, COLOR_VIBRANT_BLUE, panel_rect, 2, border_radius=8)
        
        clip_rect = pygame.Rect(grid_btn_x, grid_list_y, grid_btn_w, grid_list_h)
        screen.set_clip(clip_rect)
        
        for i, btn in enumerate(grid_buttons):
            btn.rect.y = grid_list_y + i * (grid_btn_h + 8) - scroll_offset
            if grid_list_y <= btn.rect.y < grid_list_y + grid_list_h:
                btn.draw(screen, font)
                if btn.text == selected_grid:
                    pygame.draw.rect(screen, COLOR_VIBRANT_CYAN, btn.rect, 4, border_radius=12)
        
        screen.set_clip(None)
        
        if len(grid_buttons) * (grid_btn_h + 8) > grid_list_h:
            total_scroll_height = len(grid_buttons) * (grid_btn_h + 8)
            scrollbar_h = (grid_list_h / total_scroll_height) * grid_list_h
            scrollbar_y = (scroll_offset / total_scroll_height) * grid_list_h
            scrollbar_rect = pygame.Rect(
                grid_btn_x + grid_btn_w + 5,
                grid_list_y + scrollbar_y,
                8,
                scrollbar_h
            )
            pygame.draw.rect(screen, COLOR_VIBRANT_BLUE, scrollbar_rect, border_radius=4)
        
        section2 = font_section.render("Select an algorithm:", True, COLOR_VIBRANT_YELLOW)
        screen.blit(section2, (40, algo_list_y - 35))
        
        for btn in algo_buttons:
            btn.draw(screen, font)
            if btn.text == selected_algo:
                pygame.draw.rect(screen, COLOR_VIBRANT_CYAN, btn.rect, 4, border_radius=12)
        
        if selected_grid and selected_algo:
            solve_btn.draw(screen, font)
        else:
            pygame.draw.rect(screen, (80, 80, 80), solve_btn.rect, border_radius=12)
            dim_text = font.render("SOLVE", True, (150, 150, 150))
            dim_rect = dim_text.get_rect(center=solve_btn.rect.center)
            screen.blit(dim_text, dim_rect)
        
        results_btn.draw(screen, font)
        
        pygame.display.flip()


class _SolverAborted(Exception):
    """Raised when user presses ESC or closes window during solving."""
    pass


def run_solver(filepath, algo):
    """Run the selected solver algorithm on the selected grid."""
    from script import SudokuGrid
    from solver import (brute_force_with_callback, backtracking_with_callback,
                        backtracking_mrv, constraint_propagation, propagation_mrv)
    
    algo_map = {
        "Brute Force": brute_force_with_callback,
        "Backtracking": backtracking_with_callback,
        "Backtracking MRV": backtracking_mrv,
        "Constraint Propagation": constraint_propagation,
        "Propagation MRV": propagation_mrv,
    }
    
    sudoku = SudokuGrid(filepath)
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE + 100))
    pygame.display.set_caption(f"Solving - {algo}...")
    clock = pygame.time.Clock()
    font_large = pygame.font.SysFont("arial", 36)
    font_status = pygame.font.SysFont("arial", 18)
    
    step_count = [0]
    UPDATE_EVERY = 10
    
    def solver_callback(row, col, num, action):
        """Called by the solver on each place/remove step."""
        step_count[0] += 1
        
        if step_count[0] % UPDATE_EVERY != 0:
            return
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                raise _SolverAborted()
        
        # Draw background and grid
        draw_gradient_background(screen, WINDOW_SIZE, WINDOW_SIZE + 100, COLOR_BG_PRIMARY, COLOR_BG_ACCENT)
        
        # Draw status panel at the top
        panel_rect = pygame.Rect(0, 0, WINDOW_SIZE, 100)
        pygame.draw.rect(screen, COLOR_BG_SECONDARY, panel_rect)
        pygame.draw.rect(screen, COLOR_VIBRANT_BLUE, panel_rect, 2)
        
        # Status text in the panel
        status_text = font_status.render(
            f"Solving with {algo}...", True, COLOR_VIBRANT_YELLOW
        )
        screen.blit(status_text, (20, 15))
        
        step_text = font_status.render(
            f"Steps: {step_count[0]}", True, COLOR_VIBRANT_CYAN
        )
        screen.blit(step_text, (20, 45))
        
        time_text = font_status.render(
            f"Time: {(pygame.time.get_ticks() - start_time_perf) / 1000:.2f}s", True, COLOR_VIBRANT_GREEN
        )
        screen.blit(time_text, (WINDOW_SIZE // 2 + 20, 45))
        
        # Draw the grid below the panel
        draw_solver_grid_offset(screen, sudoku, font_large, 100)
        
        pygame.display.flip()
        time.sleep(0.05)
    
    algo_func = algo_map.get(algo, propagation_mrv)
    start_time_perf = pygame.time.get_ticks()
    
    try:
        success = algo_func(sudoku.grid, sudoku.is_valid, solver_callback)
    except _SolverAborted:
        return
    
    end_time_perf = pygame.time.get_ticks()
    solve_duration = (end_time_perf - start_time_perf) / 1000.0
    
    grid_name = os.path.basename(filepath)
    
    try:
        algo_key = {
            "Brute Force": "brute",
            "Backtracking": "backtrack",
            "Backtracking MRV": "backtrack_mrv",
            "Constraint Propagation": "propagation",
            "Propagation MRV": "propagation_mrv",
        }.get(algo, "unknown")
        
        cells_empty = sum(1 for r in sudoku.original for c in r if c == 0)
        
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
    
    result_text = "SOLVED!" if success else "NO SOLUTION FOUND"
    pygame.display.set_caption(f"Solver - {algo} - {result_text}")
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
        
        # Draw background
        draw_gradient_background(screen, WINDOW_SIZE, WINDOW_SIZE + 100, COLOR_BG_PRIMARY, COLOR_BG_ACCENT)
        
        # Draw result panel at the top
        panel_rect = pygame.Rect(0, 0, WINDOW_SIZE, 100)
        pygame.draw.rect(screen, COLOR_BG_SECONDARY, panel_rect)
        pygame.draw.rect(screen, COLOR_VIBRANT_BLUE, panel_rect, 2)
        
        # Result text
        title_color = COLOR_VIBRANT_GREEN if success else COLOR_VIBRANT_RED
        title = pygame.font.SysFont("arial", 28, bold=True).render(
            f"{result_text}", True, title_color
        )
        screen.blit(title, (20, 10))
        
        # Stats
        stats_line = font_status.render(
            f"Steps: {step_count[0]}   |   Time: {solve_duration:.3f}s", True, COLOR_TEXT_LIGHT
        )
        screen.blit(stats_line, (20, 50))
        
        footer = font_status.render(
            "Press ESC to go back", True, COLOR_VIBRANT_YELLOW
        )
        screen.blit(footer, (WINDOW_SIZE - 200, 50))
        
        # Draw the grid below the panel
        draw_solver_grid_offset(screen, sudoku, font_large, 100)
        
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
    """Draw the solver's grid with current state."""
    for i in range(10):
        thickness = 3 if i % 3 == 0 else 1
        pygame.draw.line(screen, COLOR_BLACK, (i * CELL_SIZE, 0), (i * CELL_SIZE, WINDOW_SIZE), thickness)
        pygame.draw.line(screen, COLOR_BLACK, (0, i * CELL_SIZE), (WINDOW_SIZE, i * CELL_SIZE), thickness)
    
    for row in range(9):
        for col in range(9):
            x, y = col * CELL_SIZE, row * CELL_SIZE
            pygame.draw.rect(screen, COLOR_CELL_BORDER, (x, y, CELL_SIZE, CELL_SIZE), 1)
            if sudoku.grid[row][col] != 0:
                color = COLOR_BLACK if sudoku.original[row][col] != 0 else COLOR_VIBRANT_BLUE
                text = font.render(str(sudoku.grid[row][col]), True, color)
                text_rect = text.get_rect(center=(x + CELL_SIZE // 2, y + CELL_SIZE // 2))
                screen.blit(text, text_rect)

def draw_solver_grid_offset(screen, sudoku, font, y_offset):
    """Draw the solver's grid with offset from top."""
    for i in range(10):
        thickness = 3 if i % 3 == 0 else 1
        pygame.draw.line(screen, COLOR_BLACK, (i * CELL_SIZE, y_offset), (i * CELL_SIZE, y_offset + WINDOW_SIZE), thickness)
        pygame.draw.line(screen, COLOR_BLACK, (0, y_offset + i * CELL_SIZE), (WINDOW_SIZE, y_offset + i * CELL_SIZE), thickness)
    
    for row in range(9):
        for col in range(9):
            x, y = col * CELL_SIZE, y_offset + row * CELL_SIZE
            pygame.draw.rect(screen, COLOR_CELL_BORDER, (x, y, CELL_SIZE, CELL_SIZE), 1)
            if sudoku.grid[row][col] != 0:
                color = COLOR_BLACK if sudoku.original[row][col] != 0 else COLOR_VIBRANT_BLUE
                text = font.render(str(sudoku.grid[row][col]), True, color)
                text_rect = text.get_rect(center=(x + CELL_SIZE // 2, y + CELL_SIZE // 2))
                screen.blit(text, text_rect)

def play_game(difficulty: str, screen):
    """Main game loop for playing sudoku."""
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
                    if event.mod & pygame.KMOD_CTRL:
                        game_state.validate_move(num)
                    else:
                        game_state.add_to_stash(num)
                elif event.key == pygame.K_RETURN:
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
                game_state = GameState(difficulty)
                continue
            else:
                return result
        
        screen.fill(COLOR_WHITE)
        draw_game_grid(screen, game_state, font_large, font_small)
        pygame.display.flip()
        clock.tick(60)


def draw_game_grid(screen, game_state, font_large, font_small):
    """Draw the game grid with current state and cells."""
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
                color = COLOR_BLACK if game_state.original_grid[row][col] != 0 else COLOR_VIBRANT_BLUE
                text = font_large.render(str(num), True, color)
                text_rect = text.get_rect(center=(x + CELL_SIZE // 2, y + CELL_SIZE // 2))
                screen.blit(text, text_rect)
            
            if cell_coord in game_state.stash and game_state.current_grid[row][col] == 0:
                stashed = sorted(game_state.stash[cell_coord])
                for idx, num in enumerate(stashed):
                    sx = x + 4 + (idx % 3) * 18
                    sy = y + 2 + (idx // 3) * 16
                    text = font_small.render(str(num), True, (150, 150, 150))
                    screen.blit(text, (sx, sy))
            
            if game_state.selected_cell == cell_coord:
                pygame.draw.rect(screen, COLOR_VIBRANT_CYAN, (x, y, CELL_SIZE, CELL_SIZE), 3)


def show_victory_screen():
    """Display victory screen with confetti animation and navigation buttons."""
    screen = pygame.display.get_surface()
    font_large = pygame.font.SysFont("arial", 48, bold=True)
    font_small = pygame.font.SysFont("arial", 24)
    clock = pygame.time.Clock()
    
    btn_w = 140
    spacing = 20
    total_w = btn_w * 3 + spacing * 2
    start_x = (WINDOW_SIZE - total_w) // 2
    btn_y = 280
    menu_btn = Button(start_x, btn_y, btn_w, 50, "MENU", "primary")
    return_btn = Button(start_x + btn_w + spacing, btn_y, btn_w, 50, "RETURN", "secondary")
    restart_btn = Button(start_x + 2 * (btn_w + spacing), btn_y, btn_w, 50, "RESTART", "success")
    
    confetti_colors = [
        COLOR_VIBRANT_RED, COLOR_VIBRANT_GREEN, COLOR_VIBRANT_BLUE,
        COLOR_VIBRANT_YELLOW, COLOR_VIBRANT_ORANGE, COLOR_VIBRANT_PURPLE,
        COLOR_VIBRANT_CYAN, COLOR_VIBRANT_PINK,
    ]
    confetti = []
    for _ in range(80):
        confetti.append((
            random.randint(0, WINDOW_SIZE),
            random.randint(-WINDOW_SIZE, 0),
            random.uniform(1.0, 3.5),
            random.randint(3, 7),
            random.choice(confetti_colors),
            random.uniform(-0.8, 0.8),
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
        
        draw_gradient_background(screen, WINDOW_SIZE, WINDOW_SIZE, COLOR_BG_PRIMARY, COLOR_BG_ACCENT)
        
        new_confetti = []
        for x, y, speed, size, color, drift in confetti:
            y += speed
            x += drift
            if y > WINDOW_SIZE:
                y = random.randint(-30, -5)
                x = random.randint(0, WINDOW_SIZE)
            new_confetti.append((x, y, speed, size, color, drift))
            rect_w = size
            rect_h = size // 2 if size > 4 else size
            pygame.draw.rect(screen, color, (int(x), int(y), rect_w, rect_h))
        confetti = new_confetti
        
        pulse = math.sin(frame_count * 0.05) * 0.15 + 1.0
        pulse_size = int(48 * pulse)
        pulse_font = pygame.font.SysFont("arial", pulse_size, bold=True)
        text = pulse_font.render("PUZZLE SOLVED!", True, COLOR_VIBRANT_GREEN)
        text_rect = text.get_rect(center=(WINDOW_SIZE // 2, 120))
        screen.blit(text, text_rect)
        
        alpha = min(255, frame_count * 4)
        sub_surf = font_small.render("Congratulations!", True, COLOR_VIBRANT_YELLOW)
        sub_surf.set_alpha(alpha)
        sub_rect = sub_surf.get_rect(center=(WINDOW_SIZE // 2, 180))
        screen.blit(sub_surf, sub_rect)
        
        menu_btn.draw(screen, font_small)
        return_btn.draw(screen, font_small)
        restart_btn.draw(screen, font_small)
        
        hint_font = pygame.font.SysFont("arial", 12)
        hints = [("Main Menu", menu_btn), ("Difficulty", return_btn), ("Same Level", restart_btn)]
        for hint_text, btn in hints:
            hint_surf = hint_font.render(hint_text, True, (140, 140, 140))
            hint_rect = hint_surf.get_rect(center=(btn.rect.centerx, btn.rect.bottom + 14))
            screen.blit(hint_surf, hint_rect)
        
        pygame.display.flip()
        clock.tick(60)