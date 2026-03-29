import time
import pygame
import sys
import random
import math
import os
import json
import ast
import sqlite3
import tempfile
import subprocess
from datetime import datetime

from script import get_or_generate_puzzle, validate_move, SudokuGrid
from solver import (brute_force_with_callback, backtracking_with_callback, backtracking_mrv,
                    constraint_propagation, propagation_mrv,
                    DB_PATH, _init_db, get_latest_results)

WINDOW_SIZE = 540
CELL_SIZE = WINDOW_SIZE // 9
WINDOW_WIDTH = 700
WINDOW_HEIGHT = 700

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
# Algorithm palette for results charts
ALGO_PALETTE = {
    "brute": {"hex": "#FF6B6B", "rgb": COLOR_VIBRANT_RED},
    "backtrack": {"hex": "#4ECDC4", "rgb": COLOR_VIBRANT_CYAN},
    "backtrack_mrv": {"hex": "#45B7D1", "rgb": COLOR_VIBRANT_BLUE},
    "propagation": {"hex": "#96CEB4", "rgb": COLOR_VIBRANT_GREEN},
    "propagation_mrv": {"hex": "#FFEAA7", "rgb": COLOR_VIBRANT_YELLOW},
}

# Derived palette constants for results charts
ALGO_COLORS = {k: v["hex"] for k, v in ALGO_PALETTE.items()}
ALGO_LABELS = {
    "brute": "Brute Force",
    "backtrack": "Backtracking",
    "backtrack_mrv": "Backtrack+MRV",
    "propagation": "AC-3",
    "propagation_mrv": "AC-3+MRV",
}
ALGO_ORDER = ["brute", "backtrack", "backtrack_mrv", "propagation", "propagation_mrv"]

# Base directory for resolving relative paths (saves/, grids/)
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ============================================================================
# SceneManager (absorbed from scene_manager.py)
# ============================================================================

class SceneManager:
    """Manages scene transitions and maintains consistent window size."""

    def __init__(self):
        """Initialize the scene manager with a fixed-size window."""
        self.window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.current_scene = None

    def set_scene(self, scene_name: str):
        """Set the current scene and update window title."""
        self.current_scene = scene_name
        pygame.display.set_caption(f"Sudoku - {scene_name}")

    def get_window(self) -> pygame.Surface:
        """Return the global window surface."""
        return self.window

    def get_size(self) -> tuple[int, int]:
        """Return window dimensions."""
        return WINDOW_WIDTH, WINDOW_HEIGHT


# Initialized in main_menu() after pygame.init()
scene_manager: SceneManager | None = None


# ============================================================================
# Save manager functions (absorbed from save_manager.py)
# ============================================================================

SAVES_DIR = os.path.join(_BASE_DIR, "saves")
SCORES_FILE = os.path.join(SAVES_DIR, "scores.json")
CURRENT_SAVE_FILE = os.path.join(SAVES_DIR, "current_game.json")

DEFAULT_SCORES_DATA: dict = {
    "games": []
}


def init_saves_dir() -> None:
    """Create saves directory if it doesn't exist."""
    if not os.path.exists(SAVES_DIR):
        os.makedirs(SAVES_DIR)
        print(f"[OK] Created saves directory: {SAVES_DIR}")


def load_scores() -> list:
    """Load scores from JSON file. Returns empty list if file doesn't exist."""
    init_saves_dir()

    if not os.path.exists(SCORES_FILE):
        return DEFAULT_SCORES_DATA["games"]

    try:
        with open(SCORES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("games", [])
    except (json.JSONDecodeError, IOError) as e:
        print(f"[WARN] Could not load scores: {e}")
        return []


def save_score(difficulty: str, time_seconds: float, completed_cells: int,
               timestamp: str = None) -> None:
    """Save a completed game score to the JSON file."""
    init_saves_dir()

    if timestamp is None:
        timestamp = datetime.now().isoformat()

    scores = load_scores()
    scores.append({
        "difficulty": difficulty,
        "time_seconds": round(time_seconds, 2),
        "completed_cells": completed_cells,
        "timestamp": timestamp,
    })

    data = {"games": scores}
    tmp_fd, tmp_path = tempfile.mkstemp(dir=SAVES_DIR, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, SCORES_FILE)
        print(f"[OK] Score saved: {difficulty} in {time_seconds:.1f}s")
    except Exception as e:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        print(f"[ERROR] Could not save score: {e}")


def save_game(game_state, elapsed_time: float = 0) -> None:
    """Save current game state for pause/resume functionality."""
    init_saves_dir()

    save_data = {
        "difficulty": game_state.difficulty,
        "current_grid": game_state.current_grid,
        "original_grid": game_state.original_grid,
        "solved_grid": game_state.solved_grid,
        "stash": {str(k): list(v) for k, v in game_state.stash.items()},
        "cell_status": {str(k): v for k, v in game_state.cell_status.items()},
        "selected_cell": game_state.selected_cell,
        "elapsed_time": elapsed_time,
        "timestamp": datetime.now().isoformat(),
    }

    tmp_fd, tmp_path = tempfile.mkstemp(dir=SAVES_DIR, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, CURRENT_SAVE_FILE)
        print(f"[OK] Game saved (time: {elapsed_time:.1f}s)")
    except Exception as e:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        print(f"[ERROR] Could not save game: {e}")


def load_game() -> dict | None:
    """Load saved game state. Returns None if no save exists."""
    init_saves_dir()

    if not os.path.exists(CURRENT_SAVE_FILE):
        return None

    try:
        with open(CURRENT_SAVE_FILE, "r", encoding="utf-8") as f:
            save_data = json.load(f)
        print(f"[OK] Game loaded: {save_data.get('difficulty', 'unknown')}")
        return save_data
    except (json.JSONDecodeError, IOError, KeyError) as e:
        print(f"[WARN] Could not load game: {e}")
        return None


def delete_save() -> None:
    """Delete the current game save."""
    if os.path.exists(CURRENT_SAVE_FILE):
        try:
            os.remove(CURRENT_SAVE_FILE)
            print("[OK] Game save deleted")
        except IOError as e:
            print(f"[ERROR] Could not delete save: {e}")


def has_save() -> bool:
    """Check if a saved game exists."""
    return os.path.exists(CURRENT_SAVE_FILE)


def get_score_stats(scores: list) -> dict:
    """Calculate statistics from scores list."""
    if not scores:
        return {
            "total_games": 0,
            "easy": {"count": 0, "avg_time": 0},
            "normal": {"count": 0, "avg_time": 0},
            "hard": {"count": 0, "avg_time": 0},
        }

    stats = {
        "total_games": len(scores),
        "easy": {"count": 0, "avg_time": 0, "times": []},
        "normal": {"count": 0, "avg_time": 0, "times": []},
        "hard": {"count": 0, "avg_time": 0, "times": []},
    }

    for score in scores:
        difficulty = score.get("difficulty")
        if difficulty in stats and difficulty != "total_games":
            stats[difficulty]["count"] += 1
            stats[difficulty]["times"].append(score.get("time_seconds", 0))

    for difficulty in ["easy", "normal", "hard"]:
        if stats[difficulty]["count"] > 0:
            avg = sum(stats[difficulty]["times"]) / stats[difficulty]["count"]
            stats[difficulty]["avg_time"] = round(avg, 2)
        del stats[difficulty]["times"]

    return stats


# ============================================================================
# Drawing utilities
# ============================================================================

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
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.circle(overlay, (*COLOR_VIBRANT_CYAN, 25), (width - 50, 0), 150)
    screen.blit(overlay, (0, 0))

    overlay2 = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.circle(overlay2, (*COLOR_VIBRANT_PURPLE, 25), (50, height), 200)
    screen.blit(overlay2, (0, 0))


# ============================================================================
# Button
# ============================================================================

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
        shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 100))
        screen.blit(shadow_surf, shadow_rect.topleft)
        
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
        overlay_surface = pygame.Surface((gradient_rect.width, gradient_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(overlay_surface, (255, 255, 255, 30), overlay_surface.get_rect(), border_radius=12)
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


# ============================================================================
# GameState
# ============================================================================

class GameState:
    """Manages game state including grid, moves, and difficulty level."""
    
    def __init__(self, difficulty: str):
        """Initialize game state."""
        self.difficulty = difficulty
        self.puzzle_grid, self.solved_grid = get_or_generate_puzzle(difficulty)
        self.current_grid = [row[:] for row in self.puzzle_grid]
        self.original_grid = [row[:] for row in self.puzzle_grid]
        self.stash = {}
        self.cell_status = {}
        self.selected_cell = (0, 0)
        self.hard_mode_cell_colors = {}
        self.generate_hard_mode_colors()

    @staticmethod
    def restore_from_save(save_data):
        """Restore a GameState from saved data.

        Args:
            save_data (dict): Save data from load_game()

        Returns:
            GameState: Restored game state
        """
        # Create instance without triggering puzzle generation
        game_state = object.__new__(GameState)
        game_state.difficulty = save_data["difficulty"]
        game_state.stash = {}
        game_state.cell_status = {}
        game_state.selected_cell = (0, 0)
        game_state.hard_mode_cell_colors = {}
        game_state.generate_hard_mode_colors()
        
        # Restore grids exactly as they were saved
        game_state.current_grid = [row[:] for row in save_data["current_grid"]]
        game_state.original_grid = [row[:] for row in save_data["original_grid"]]
        game_state.puzzle_grid = [row[:] for row in save_data["original_grid"]]
        
        # Restore solved grid from save (FALLBACK: generate if missing in old saves)
        if "solved_grid" in save_data:
            game_state.solved_grid = [row[:] for row in save_data["solved_grid"]]
        else:
            _, game_state.solved_grid = get_or_generate_puzzle(save_data["difficulty"])
        
        # Restore stash (convert string keys back to tuples)
        game_state.stash = {}
        for key_str, values in save_data.get("stash", {}).items():
            row, col = ast.literal_eval(key_str)
            game_state.stash[(row, col)] = set(values)
        
        # Restore cell status
        game_state.cell_status = {}
        for key_str, status in save_data.get("cell_status", {}).items():
            row, col = ast.literal_eval(key_str)
            game_state.cell_status[(row, col)] = status
        
        game_state.selected_cell = tuple(save_data.get("selected_cell", (0, 0)))
        
        print("[OK] Game restored from save")
        return game_state
    
    def generate_hard_mode_colors(self):
        """Generate random vibrant colors for hard mode cells."""
        self.hard_mode_cell_colors = {(r, c): random.choice(HARD_MODE_COLORS) for r in range(9) for c in range(9)}
    
    def randomize_hard_colors(self):
        """Randomize colors for hard mode."""
        self.generate_hard_mode_colors()
    
    def select_cell(self, row: int, col: int):
        """Select a cell on the grid."""
        if 0 <= row < 9 and 0 <= col < 9:
            # Clear wrong/multiple status from previous cell if it's still empty
            prev = self.selected_cell
            if prev and prev in self.cell_status and self.cell_status[prev] in ("wrong", "multiple"):
                if self.current_grid[prev[0]][prev[1]] == 0:
                    del self.cell_status[prev]
            self.selected_cell = (row, col)
    
    def add_to_stash(self, num: int):
        """Add a number to the stash (pencil marks) for the selected cell."""
        if self.selected_cell is None:
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
        if self.selected_cell is None:
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
        elif status == "multiple":
            self.cell_status[(row, col)] = "multiple"
            return False
        else:
            self.cell_status[(row, col)] = "wrong"
            return False
    
    def is_complete(self):
        """Check if the puzzle is completely solved."""
        return self.current_grid == self.solved_grid


# ============================================================================
# Menu scenes
# ============================================================================

def main_menu():
    """Display main menu with Play, Solver, and Exit options."""
    global scene_manager
    pygame.init()
    scene_manager = SceneManager()
    scene_manager.set_scene("Menu")
    screen = scene_manager.get_window()
    
    font_large = pygame.font.SysFont("arial", 48, bold=True)
    font_small = pygame.font.SysFont("arial", 24)
    clock = pygame.time.Clock()

    play_btn = Button((WINDOW_WIDTH - 200) // 2, 200, 200, 50, "PLAY", "primary")
    solver_btn = Button((WINDOW_WIDTH - 200) // 2, 270, 200, 50, "SOLVER", "secondary")
    exit_btn = Button((WINDOW_WIDTH - 200) // 2, 340, 200, 50, "EXIT", "success")

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
        
        draw_gradient_background(screen, WINDOW_WIDTH, WINDOW_HEIGHT, COLOR_BG_PRIMARY, COLOR_BG_ACCENT)
        draw_decorative_circles(screen, WINDOW_WIDTH, WINDOW_HEIGHT)
        
        title = font_large.render("SUDOKU", True, COLOR_VIBRANT_BLUE)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 100))
        glow_title = font_large.render("SUDOKU", True, COLOR_VIBRANT_CYAN)
        glow_title.set_alpha(50)
        screen.blit(glow_title, (title_rect.x + 2, title_rect.y + 2))
        screen.blit(title, title_rect)
        
        play_btn.draw(screen, font_small)
        solver_btn.draw(screen, font_small)

        exit_btn.draw(screen, font_small)
        
        pygame.display.flip()
        clock.tick(30)


def difficulty_menu():
    """Display difficulty selection menu."""
    scene_manager.set_scene("Difficulty")
    screen = scene_manager.get_window()
    
    font_large = pygame.font.SysFont("arial", 48, bold=True)
    font_small = pygame.font.SysFont("arial", 24)
    clock = pygame.time.Clock()

    # Fixed-position buttons (no window resize)
    resume_btn = None
    if has_save():
        # ✅ Move down (from 50 to 110)
        resume_btn = Button((WINDOW_WIDTH - 200) // 2, 110, 200, 45, "RESUME GAME", "success")
        y_start = 180
    else:
        y_start = 140
    
    easy_btn = Button((WINDOW_WIDTH - 200) // 2, y_start, 200, 50, "EASY", "success")
    normal_btn = Button((WINDOW_WIDTH - 200) // 2, y_start + 70, 200, 50, "NORMAL", "primary")
    hard_btn = Button((WINDOW_WIDTH - 200) // 2, y_start + 140, 200, 50, "HARD", "secondary")
    scores_btn = Button((WINDOW_WIDTH - 200) // 2, y_start + 210, 200, 50, "SCORES", "primary")
    
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        easy_btn.update_hover(mouse_pos)
        normal_btn.update_hover(mouse_pos)
        hard_btn.update_hover(mouse_pos)
        scores_btn.update_hover(mouse_pos)
        if resume_btn:
            resume_btn.update_hover(mouse_pos)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Resume game
                if resume_btn and resume_btn.is_clicked(event.pos):
                    save_data = load_game()
                    if save_data:
                        result = play_game(save_data["difficulty"], screen, resume_save=save_data)
                        if result != "return":
                            return
                    continue
                
                difficulty = None
                if easy_btn.is_clicked(event.pos):
                    difficulty = "easy"
                elif normal_btn.is_clicked(event.pos):
                    difficulty = "normal"
                elif hard_btn.is_clicked(event.pos):
                    difficulty = "hard"
                elif scores_btn.is_clicked(event.pos):
                    scores_menu()
                    continue
                
                if difficulty:
                    result = play_game(difficulty, screen)
                    if result != "return":
                        return
        
        draw_gradient_background(screen, WINDOW_WIDTH, WINDOW_HEIGHT, COLOR_BG_PRIMARY, COLOR_BG_ACCENT)
        draw_decorative_circles(screen, WINDOW_WIDTH, WINDOW_HEIGHT)
        
        title = font_large.render("SELECT DIFFICULTY", True, COLOR_VIBRANT_YELLOW)
        # ✅ Move title slightly down (from 30 to 50)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 50))
        screen.blit(title, title_rect)
        
        if resume_btn:
            resume_btn.draw(screen, font_small)
        
        easy_btn.draw(screen, font_small)
        normal_btn.draw(screen, font_small)
        hard_btn.draw(screen, font_small)
        scores_btn.draw(screen, font_small)

        pygame.display.flip()
        clock.tick(30)


def solver_menu_pygame():
    """Display solver menu with grid and algorithm selection."""
    pygame.display.set_caption("Sudoku - Solver")
    font = pygame.font.SysFont("arial", 16)
    font_title = pygame.font.SysFont("arial", 32, bold=True)
    font_section = pygame.font.SysFont("arial", 20, bold=True)
    clock = pygame.time.Clock()

    grids_dir = os.path.join(_BASE_DIR, "grids")
    grid_files = sorted([f for f in os.listdir(grids_dir) if f.endswith(".txt")])[:5]
    if not grid_files:
        return
    
    window_w = WINDOW_WIDTH
    window_h = WINDOW_HEIGHT
    scene_manager.set_scene("Solver")
    screen = scene_manager.get_window()
    
    # GRID BUTTONS
    grid_list_y = 80
    grid_btn_h = 40
    grid_btn_w = 620
    grid_btn_x = 40
    grid_list_h = len(grid_files) * (grid_btn_h + 8) - 8

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
    algo_btn_w = 280
    algo_btn_h = 42
    algo_btn_step = 48
    algo_buttons = []
    for i, name in enumerate(algo_names):
        x = (window_w - algo_btn_w) // 2
        y = algo_list_y + i * algo_btn_step
        algo_buttons.append(Button(x, y, algo_btn_w, algo_btn_h, name, "secondary"))

    # CONTROL BUTTONS
    buttons_y = algo_list_y + len(algo_names) * algo_btn_step + 15
    solve_btn = Button(150, buttons_y, 140, 50, "SOLVE", "success")
    results_btn = Button(410, buttons_y, 140, 50, "RESULTS", "primary")
    
    selected_grid = None
    selected_algo = None
    
    while True:
        mouse_pos = pygame.mouse.get_pos()
        
        for btn in algo_buttons + [solve_btn, results_btn]:
            btn.update_hover(mouse_pos)
        
        for btn in grid_buttons:
            # ✅ Hover detection now uses fixed y (no scroll_offset bug)
            btn.hovered = btn.rect.collidepoint(mouse_pos)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # ✅ Mouse wheel handling removed (no longer needed)
                for btn in grid_buttons:
                    if btn.is_clicked(event.pos):
                        selected_grid = btn.text
                
                for btn in algo_buttons:
                    if btn.is_clicked(event.pos):
                        selected_algo = btn.text
                
                if solve_btn.is_clicked(event.pos) and selected_grid and selected_algo:
                    run_solver(os.path.join(grids_dir, selected_grid), selected_algo)
                    # Restore solver menu window after resolution
                    scene_manager.set_scene("Solver")
                    screen = scene_manager.get_window()
                
                if results_btn.is_clicked(event.pos):
                    show_results_menu()
        
        draw_gradient_background(screen, window_w, window_h, COLOR_BG_PRIMARY, COLOR_BG_ACCENT)
        draw_decorative_circles(screen, window_w, window_h)
        
        title = font_title.render("SOLVER", True, COLOR_VIBRANT_BLUE)
        title_rect = title.get_rect(center=(window_w // 2, 20))
        screen.blit(title, title_rect)
        
        section1 = font_section.render("Select a grid:", True, COLOR_VIBRANT_YELLOW)
        screen.blit(section1, (grid_btn_x, grid_list_y - 35))
        
        panel_rect = pygame.Rect(grid_btn_x - 5, grid_list_y - 5, grid_btn_w + 10, grid_list_h + 10)
        pygame.draw.rect(screen, COLOR_BG_SECONDARY, panel_rect, border_radius=8)
        pygame.draw.rect(screen, COLOR_VIBRANT_BLUE, panel_rect, 2, border_radius=8)
        
        # ✅ Draw all buttons directly (all fit in 280px)
        for btn in grid_buttons:
            btn.draw(screen, font)
            if btn.text == selected_grid:
                pygame.draw.rect(screen, COLOR_VIBRANT_CYAN, btn.rect, 4, border_radius=12)
        
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
        clock.tick(30)


# ============================================================================
# Solver execution
# ============================================================================

class _SolverAborted(Exception):
    """Raised when user presses ESC or closes window during solving."""
    pass


def run_solver(filepath, algo):
    """Run the selected solver algorithm on the selected grid."""
    algo_map = {
        "Brute Force": brute_force_with_callback,
        "Backtracking": backtracking_with_callback,
        "Backtracking MRV": backtracking_mrv,
        "Constraint Propagation": constraint_propagation,
        "Propagation MRV": propagation_mrv,
    }
    
    sudoku = SudokuGrid(filepath)
    scene_manager.set_scene(f"Solving - {algo}")
    screen = scene_manager.get_window()
    clock = pygame.time.Clock()
    font_large = pygame.font.SysFont("arial", 36)
    font_status = pygame.font.SysFont("arial", 18)
    
    step_count = [0]
    UPDATE_EVERY = 10
    start_time_perf = pygame.time.get_ticks()

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
        draw_gradient_background(screen, WINDOW_WIDTH, WINDOW_HEIGHT, COLOR_BG_PRIMARY, COLOR_BG_ACCENT)

        # Draw status panel at the top
        panel_rect = pygame.Rect(0, 0, WINDOW_WIDTH, 100)
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
        screen.blit(time_text, (WINDOW_WIDTH // 2 + 20, 45))

        # Draw the grid below the panel
        draw_solver_grid_offset(screen, sudoku, font_large, 100)

        pygame.display.flip()
        pygame.time.delay(50)

    algo_func = algo_map.get(algo, propagation_mrv)
    
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
        draw_gradient_background(screen, WINDOW_WIDTH, WINDOW_HEIGHT, COLOR_BG_PRIMARY, COLOR_BG_ACCENT)

        # Draw result panel at the top
        panel_rect = pygame.Rect(0, 0, WINDOW_WIDTH, 100)
        pygame.draw.rect(screen, COLOR_BG_SECONDARY, panel_rect)
        pygame.draw.rect(screen, COLOR_VIBRANT_BLUE, panel_rect, 2)

        # Result text
        title_color = COLOR_VIBRANT_GREEN if success else COLOR_VIBRANT_RED
        title = font_large.render(result_text, True, title_color)
        screen.blit(title, (20, 10))

        # Stats
        stats_line = font_status.render(
            f"Steps: {step_count[0]}   |   Time: {solve_duration:.3f}s", True, COLOR_TEXT_LIGHT
        )
        screen.blit(stats_line, (20, 50))

        footer = font_status.render(
            "Press ESC to go back", True, COLOR_VIBRANT_YELLOW
        )
        screen.blit(footer, (WINDOW_WIDTH - 200, 50))
        
        # Draw the grid below the panel
        draw_solver_grid_offset(screen, sudoku, font_large, 100)
        
        pygame.display.flip()
        clock.tick(60)


# ============================================================================
# Results visualization (matplotlib)
# ============================================================================

_results_viewer_proc = None


def _plot_bars(ax, results, field, ylabel, title):
    """Grouped bars: one numeric field per algorithm, grouped by grid."""
    import numpy as np

    grids = sorted(set(r["grid_file"] for r in results))
    algos = [a for a in ALGO_ORDER if any(r["algo"] == a for r in results)]

    if not grids or not algos:
        ax.text(0.5, 0.5, "No data", ha="center", va="center",
                transform=ax.transAxes, fontsize=12)
        return

    x = np.arange(len(grids))
    width = 0.8 / len(algos)

    for i, algo in enumerate(algos):
        values = []
        for grid in grids:
            matching = [r for r in results
                        if r["grid_file"] == grid and r["algo"] == algo]
            val = matching[0][field] if matching else 0
            values.append(val if val > 0 else np.nan)
        offset = (i - len(algos) / 2 + 0.5) * width
        ax.bar(x + offset, values, width, label=ALGO_LABELS.get(algo, algo),
               color=ALGO_COLORS.get(algo, "#999"))

    ax.set_xlabel("Grid")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels([g.replace(".txt", "") for g in grids], rotation=45, ha="right")
    ax.legend(fontsize=8)
    ax.set_yscale("log")


def _plot_time_vs_difficulty(ax, results):
    """Curves: execution time vs number of empty cells (difficulty)."""
    import numpy as np

    algos = [a for a in ALGO_ORDER if any(r["algo"] == a for r in results)]

    if not algos:
        ax.text(0.5, 0.5, "No data", ha="center", va="center",
                transform=ax.transAxes, fontsize=12)
        return

    for algo in algos:
        algo_results = [r for r in results if r["algo"] == algo]
        if not algo_results:
            continue
        algo_results.sort(key=lambda r: r["cells_empty"])
        x_vals = [r["cells_empty"] for r in algo_results]
        y_vals = [r["time_ms"] if r["time_ms"] > 0 else np.nan for r in algo_results]
        ax.plot(x_vals, y_vals, marker="o", linewidth=2, markersize=5,
                label=ALGO_LABELS.get(algo, algo),
                color=ALGO_COLORS.get(algo, "#999"))

    ax.set_xlabel("Empty cells (difficulty)")
    ax.set_ylabel("Time (ms)")
    ax.set_title("Time vs grid difficulty")
    ax.legend(fontsize=8)
    ax.set_yscale("log")


def _plot_formulas(ax):
    """Display algorithmic complexity formulas in LaTeX."""
    ax.axis("off")
    ax.set_title("Algorithmic complexity", fontsize=14, fontweight="bold")

    formulas = [
        ("Brute Force",
         r"$O(9^m)$, $m$ = empty cells",
         r"Validation only on complete grid"),
        ("Backtracking",
         r"$O(9^m)$ worst case",
         r"Pruning: $\mathrm{is\_valid}$ before placement"),
        ("Backtracking + MRV",
         r"$O(9^m)$ worst case, better in practice",
         r"Heuristic: $\min(|\mathrm{candidates}|)$"),
        ("AC-3 Propagation",
         r"$O(d \cdot n)$, $d$ = domain, $n$ = cells",
         r"Naked: $|D(c)|=1$ / Hidden: unique in unit"),
        ("AC-3 + MRV",
         r"$O(d \cdot n)$ + residual search",
         r"Propagation + MRV backtracking if stalled"),
    ]

    formula_algo_keys = {
        "Brute Force": "brute",
        "Backtracking": "backtrack",
        "Backtracking + MRV": "backtrack_mrv",
        "AC-3 Propagation": "propagation",
        "AC-3 + MRV": "propagation_mrv",
    }

    y = 0.92
    for name, complexity, detail in formulas:
        algo_key = formula_algo_keys.get(name)
        color = ALGO_COLORS.get(algo_key, "#333")
        ax.text(0.02, y, name, fontsize=11, fontweight="bold",
                transform=ax.transAxes, verticalalignment="top",
                color=color)
        ax.text(0.02, y - 0.05, complexity, fontsize=10,
                transform=ax.transAxes, verticalalignment="top")
        ax.text(0.02, y - 0.10, detail, fontsize=9, color="#666",
                transform=ax.transAxes, verticalalignment="top")
        y -= 0.20


def show_results():
    """Open a results window with 4 matplotlib subplots.

    Loads data from SQLite and saves chart to a temp file,
    opened with the system viewer to avoid Pygame conflicts.
    """
    import matplotlib.pyplot as plt
    global _results_viewer_proc

    if _results_viewer_proc is not None:
        _results_viewer_proc.poll()

    results = get_latest_results()

    if not results:
        print("[WARN] No benchmark results in database. "
              "Run first: python3 main.py grids/grid_1.txt --benchmark")
        return

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Sudoku Solver -- Comparative Results", fontsize=16, fontweight="bold")

    _plot_bars(axes[0, 0], results, "time_ms", "Time (ms)", "Execution time per algorithm")
    _plot_bars(axes[0, 1], results, "iterations", "Iterations", "Number of iterations per algorithm")
    _plot_time_vs_difficulty(axes[1, 0], results)
    _plot_formulas(axes[1, 1])

    plt.tight_layout()

    tmp_path = os.path.join(tempfile.gettempdir(), f"sudoku_results_{int(time.time())}.png")
    fig.savefig(tmp_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] Results chart saved to {tmp_path}")

    try:
        if sys.platform == "win32":
            os.startfile(tmp_path)
        elif sys.platform == "darwin":
            _results_viewer_proc = subprocess.Popen(["open", tmp_path])
        else:
            _results_viewer_proc = subprocess.Popen(["xdg-open", tmp_path])
    except (FileNotFoundError, OSError, AttributeError):
        print("[WARN] Could not open image viewer. Open manually: " + tmp_path)


def show_results_menu():
    """Show results from SQLite benchmarks in matplotlib window."""
    try:
        print("[DEBUG] Calling show_results()...")
        show_results()
        print("[DEBUG] show_results() completed")
    except ImportError as e:
        print(f"[ERROR] Import failed: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")


# ============================================================================
# Grid drawing
# ============================================================================

def draw_solver_grid_offset(screen, sudoku, font, y_offset):
    """Draw the solver's grid with offset from top, centered horizontally."""
    x_offset = (WINDOW_WIDTH - WINDOW_SIZE) // 2
    for i in range(10):
        thickness = 3 if i % 3 == 0 else 1
        pygame.draw.line(screen, COLOR_BLACK, (x_offset + i * CELL_SIZE, y_offset), (x_offset + i * CELL_SIZE, y_offset + WINDOW_SIZE), thickness)
        pygame.draw.line(screen, COLOR_BLACK, (x_offset, y_offset + i * CELL_SIZE), (x_offset + WINDOW_SIZE, y_offset + i * CELL_SIZE), thickness)

    for row in range(9):
        for col in range(9):
            x, y = x_offset + col * CELL_SIZE, y_offset + row * CELL_SIZE
            pygame.draw.rect(screen, COLOR_CELL_BORDER, (x, y, CELL_SIZE, CELL_SIZE), 1)
            if sudoku.grid[row][col] != 0:
                color = COLOR_BLACK if sudoku.original[row][col] != 0 else COLOR_VIBRANT_BLUE
                text = font.render(str(sudoku.grid[row][col]), True, color)
                text_rect = text.get_rect(center=(x + CELL_SIZE // 2, y + CELL_SIZE // 2))
                screen.blit(text, text_rect)

# ============================================================================
# Play mode
# ============================================================================

def play_game(difficulty: str, screen, resume_save=None):
    """Main game loop for playing sudoku.

    Args:
        difficulty (str): Game difficulty
        screen: Pygame surface
        resume_save (dict): Optional saved game data to resume from
    """
    pygame.display.set_caption(f"Sudoku - {difficulty.upper()}")
    clock = pygame.time.Clock()
    
    font_large = pygame.font.SysFont("arial", 36)
    font_small = pygame.font.SysFont("arial", 14)
    
    # Check if resuming from save or starting new game
    if resume_save:
        game_state = GameState.restore_from_save(resume_save)
        # IMPORTANT: Recover elapsed time before pause
        elapsed_time_before_pause = resume_save.get("elapsed_time", 0)
        print(f"[OK] Game resumed (previous time: {elapsed_time_before_pause:.1f}s)")
    else:
        game_state = GameState(difficulty)
        elapsed_time_before_pause = 0
        print(f"[OK] New game started")
    
    # Scoring timer (continue from saved time)
    start_time = time.time() - elapsed_time_before_pause
    
    is_paused = False
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Pause game et calculer le temps actuel
                    is_paused = True
                    current_elapsed = time.time() - start_time
                    pause_result = show_pause_menu(screen, font_small)
                    
                    if pause_result == "resume":
                        is_paused = False
                        # Readjust time after pause
                        start_time = time.time() - current_elapsed
                        continue
                    elif pause_result == "save_and_exit":
                        # Save with elapsed time
                        save_game(game_state, current_elapsed)
                        return
                    elif pause_result == "menu":
                        return
                
                # ... rest of key handling (digits, arrows, etc.)
                # Handle digits (top row or numpad)
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
                    # ✅ Standardization: Ctrl + Digit = VALIDATE, Digit alone = STASH
                    if event.mod & pygame.KMOD_CTRL:
                        game_state.validate_move(num)
                    else:
                        game_state.add_to_stash(num)
                elif event.key == pygame.K_RETURN:
                    # ✅ Auto-validate ONLY if exactly 1 stashed number
                    if game_state.selected_cell in game_state.stash and len(game_state.stash[game_state.selected_cell]) == 1:
                        num = next(iter(game_state.stash[game_state.selected_cell]))
                        game_state.validate_move(num)
                elif event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                    row, col = game_state.selected_cell
                    if event.key == pygame.K_UP: row = (row - 1) % 9
                    elif event.key == pygame.K_DOWN: row = (row + 1) % 9
                    elif event.key == pygame.K_LEFT: col = (col - 1) % 9
                    elif event.key == pygame.K_RIGHT: col = (col + 1) % 9
                    game_state.select_cell(row, col)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                # ✅ Fix: Account for centered grid x_offset (80)
                grid_x_offset = (WINDOW_WIDTH - WINDOW_SIZE) // 2
                if 120 <= y < 120 + WINDOW_SIZE and grid_x_offset <= x < grid_x_offset + WINDOW_SIZE:
                    col, row = (x - grid_x_offset) // CELL_SIZE, (y - 120) // CELL_SIZE
                    game_state.select_cell(row, col)
        
        if game_state.is_complete():
            # Game completed!
            elapsed_time = time.time() - start_time
            completed_cells = sum(1 for r in range(9) for c in range(9) 
                                if game_state.current_grid[r][c] != 0 and 
                                game_state.original_grid[r][c] == 0)
            
            # Save score
            save_score(difficulty, elapsed_time, completed_cells)
            
            # Clean up save file
            delete_save()
            
            result = show_victory_screen()
            if result == "restart":
                game_state = GameState(difficulty)
                start_time = time.time()  # Reset timer
                continue
            else:
                return result
        
        # Draw everything
        draw_gradient_background(screen, WINDOW_WIDTH, WINDOW_HEIGHT, COLOR_BG_PRIMARY, COLOR_BG_ACCENT)
        # ✅ Instructions panel now spans full width
        draw_game_instructions_panel(screen, font_small, difficulty)
        
        # ✅ Center the grid: x_offset = (700 - 540) // 2 = 80
        grid_x_offset = (WINDOW_WIDTH - WINDOW_SIZE) // 2
        draw_game_grid_centered(screen, game_state, font_large, font_small, 120, grid_x_offset)
        
        # ✅ Move timer to top-right of the controls panel (well within 700px)
        elapsed = time.time() - start_time
        time_text = pygame.font.SysFont("arial", 16, bold=True).render(
            f"Time: {int(elapsed // 60):02d}:{int(elapsed % 60):02d}", 
            True, COLOR_VIBRANT_CYAN
        )
        screen.blit(time_text, (WINDOW_WIDTH - 120, 20))
        
        pygame.display.flip()
        clock.tick(60)


def draw_game_grid_centered(screen, game_state, font_large, font_small, y_offset, x_offset):
    """Draw the game grid with offset from top and center it horizontally."""
    for i in range(10):
        thickness = 3 if i % 3 == 0 else 1
        # Drawing grid lines
        pygame.draw.line(screen, COLOR_BLACK, (x_offset + i * CELL_SIZE, y_offset), 
                         (x_offset + i * CELL_SIZE, y_offset + WINDOW_SIZE), thickness)
        pygame.draw.line(screen, COLOR_BLACK, (x_offset, y_offset + i * CELL_SIZE), 
                         (x_offset + WINDOW_SIZE, y_offset + i * CELL_SIZE), thickness)
    
    for row in range(9):
        for col in range(9):
            x, y = x_offset + col * CELL_SIZE, y_offset + row * CELL_SIZE
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
            
            # Draw stash (pencil marks)
            if cell_coord in game_state.stash and game_state.current_grid[row][col] == 0:
                stashed = sorted(game_state.stash[cell_coord])
                for idx, num in enumerate(stashed):
                    sx = x + 4 + (idx % 3) * 20
                    sy = y + 2 + (idx // 3) * 18
                    # ✅ Color darker for better contrast on white background
                    text = font_small.render(str(num), True, (130, 130, 130))
                    screen.blit(text, (sx, sy))
            
            if game_state.selected_cell == cell_coord:
                pygame.draw.rect(screen, COLOR_VIBRANT_CYAN, (x, y, CELL_SIZE, CELL_SIZE), 3)
                
def draw_game_instructions_panel(screen, font_small, difficulty):
    """Draw instructions panel at the top of the game screen spanning FULL width."""
    panel_height = 120
    panel_rect = pygame.Rect(0, 0, WINDOW_WIDTH, panel_height)
    
    # Panel background
    pygame.draw.rect(screen, COLOR_BG_SECONDARY, panel_rect)
    pygame.draw.rect(screen, COLOR_VIBRANT_BLUE, panel_rect, 2)
    
    # Title
    title = font_small.render("CONTROLS", True, COLOR_VIBRANT_YELLOW)
    screen.blit(title, (15, 8))

    # Instructions in 2 columns
    font_instructions = font_small
    
    # Column 1
    instructions_col1 = [
        "1-9: Pencil marks",
        "Ctrl+1-9: Place number",
        "↑↓←→: Move around",
    ]
    
    # Column 2
    instructions_col2 = [
        "Enter: Auto-place",
        "ESC: Exit game",
        f"Difficulty: {difficulty.upper()}",
    ]
    
    y_start = 35
    for i, text in enumerate(instructions_col1):
        surf = font_instructions.render(text, True, COLOR_TEXT_LIGHT)
        screen.blit(surf, (15, y_start + i * 25))
    
    for i, text in enumerate(instructions_col2):
        surf = font_instructions.render(text, True, COLOR_TEXT_LIGHT)
        screen.blit(surf, (WINDOW_WIDTH // 2 + 15, y_start + i * 25))
        
# ============================================================================
# Pause menu
# ============================================================================

def show_pause_menu(screen, font):
    """Display pause menu with options to resume, save, or exit.
    
    Returns:
        str: 'resume', 'save_and_exit', or 'menu'
    """
    font_title = pygame.font.SysFont("arial", 48, bold=True)
    font_button = pygame.font.SysFont("arial", 24)
    clock = pygame.time.Clock()

    # Compute panel layout once (D7: no per-frame mutation)
    panel_w, panel_h = 300, 350
    panel_x = (WINDOW_WIDTH - panel_w) // 2
    panel_y = (WINDOW_HEIGHT - panel_h) // 2
    btn_cx = WINDOW_WIDTH // 2
    btn_w = 200

    resume_btn = Button(btn_cx - btn_w // 2, panel_y + 110, btn_w, 50, "RESUME", "primary")
    save_btn = Button(btn_cx - btn_w // 2, panel_y + 180, btn_w, 50, "SAVE & EXIT", "secondary")
    menu_btn = Button(btn_cx - btn_w // 2, panel_y + 250, btn_w, 50, "MAIN MENU", "success")

    # D2: capture background before the overlay loop
    screenshot = screen.copy()

    paused = True
    while paused:
        mouse_pos = pygame.mouse.get_pos()
        resume_btn.update_hover(mouse_pos)
        save_btn.update_hover(mouse_pos)
        menu_btn.update_hover(mouse_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if resume_btn.is_clicked(event.pos):
                    return "resume"
                elif save_btn.is_clicked(event.pos):
                    return "save_and_exit"
                elif menu_btn.is_clicked(event.pos):
                    return "menu"
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "resume"

        # D2: restore clean background then apply overlay
        screen.blit(screenshot, (0, 0))
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((10, 10, 25))
        screen.blit(overlay, (0, 0))

        # Draw pause menu panel
        pygame.draw.rect(screen, COLOR_BG_SECONDARY, (panel_x, panel_y, panel_w, panel_h), border_radius=15)
        pygame.draw.rect(screen, COLOR_VIBRANT_BLUE, (panel_x, panel_y, panel_w, panel_h), 3, border_radius=15)

        title = font_title.render("PAUSED", True, COLOR_VIBRANT_YELLOW)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, panel_y + 50))
        screen.blit(title, title_rect)

        resume_btn.draw(screen, font_button)
        save_btn.draw(screen, font_button)
        menu_btn.draw(screen, font_button)

        hint = font.render("ESC to resume", True, (150, 150, 150))
        screen.blit(hint, (WINDOW_WIDTH // 2 - hint.get_width() // 2, panel_y + 320))

        pygame.display.flip()
        clock.tick(30)

# ============================================================================
# Scores and victory screens
# ============================================================================

def scores_menu():
    """Display scores/history screen with stats."""
    scene_manager.set_scene("Scores")
    screen = scene_manager.get_window()
    
    font_title = pygame.font.SysFont("arial", 36, bold=True)
    font_score = pygame.font.SysFont("arial", 16)
    font_stat = pygame.font.SysFont("arial", 18, bold=True)
    clock = pygame.time.Clock()

    back_btn = Button((WINDOW_WIDTH - 100) // 2, WINDOW_HEIGHT - 80, 100, 40, "BACK", "primary")
    
    scores = load_scores()
    stats = get_score_stats(scores)
    
    while True:
        mouse_pos = pygame.mouse.get_pos()
        back_btn.update_hover(mouse_pos)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_btn.is_clicked(event.pos):
                    return
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
        
        draw_gradient_background(screen, WINDOW_WIDTH, WINDOW_HEIGHT, COLOR_BG_PRIMARY, COLOR_BG_ACCENT)
        
        title = font_title.render("GAME HISTORY", True, COLOR_VIBRANT_BLUE)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 40))
        screen.blit(title, title_rect)

        y = 80
        stat_title = font_stat.render(f"Total Games: {stats['total_games']}", True, COLOR_VIBRANT_YELLOW)
        screen.blit(stat_title, (50, y))
        y += 40
        
        for difficulty in ["easy", "normal", "hard"]:
            # Convert seconds to min:sec
            avg_time = stats[difficulty]['avg_time']
            avg_minutes = int(avg_time // 60)
            avg_seconds = int(avg_time % 60)
            time_str = f"{avg_minutes}:{avg_seconds:02d}" if avg_time > 0 else "N/A"
            
            text = font_score.render(
                f"{difficulty.upper()}: {stats[difficulty]['count']} games | Avg: {time_str}",
                True, COLOR_TEXT_LIGHT
            )
            screen.blit(text, (50, y))
            y += 30
        
        y += 20
        last_games_title = font_stat.render("Recent games:", True, COLOR_VIBRANT_CYAN)
        screen.blit(last_games_title, (50, y))
        y += 35
        
        for score in scores[-10:]:
            date = score["timestamp"][:10]
            # Convert time_seconds to min:sec
            time_val = score["time_seconds"]
            minutes = int(time_val // 60)
            seconds = int(time_val % 60)
            time_str = f"{minutes}:{seconds:02d}"
            
            text = font_score.render(
                f"{date} | {score['difficulty'].upper():8} | {time_str:>6} | Cells: {score['completed_cells']}",
                True, COLOR_TEXT_LIGHT
            )
            screen.blit(text, (50, y))
            y += 25
        
        back_btn.draw(screen, font_score)

        pygame.display.flip()
        clock.tick(30)

def show_victory_screen():
    """Display victory screen with confetti animation and navigation buttons."""
    screen = pygame.display.get_surface()
    font_small = pygame.font.SysFont("arial", 24)
    base_font = pygame.font.SysFont("arial", 48, bold=True)
    base_text = base_font.render("PUZZLE SOLVED!", True, COLOR_VIBRANT_GREEN)
    hint_font = pygame.font.SysFont("arial", 12)
    clock = pygame.time.Clock()
    
    btn_w = 140
    spacing = 20
    total_w = btn_w * 3 + spacing * 2
    start_x = (WINDOW_WIDTH - total_w) // 2
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
            random.randint(0, WINDOW_WIDTH),
            random.randint(-WINDOW_HEIGHT, 0),
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
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "menu"

        draw_gradient_background(screen, WINDOW_WIDTH, WINDOW_HEIGHT, COLOR_BG_PRIMARY, COLOR_BG_ACCENT)

        new_confetti = []
        for x, y, speed, size, color, drift in confetti:
            y += speed
            x += drift
            if y > WINDOW_HEIGHT:
                y = random.randint(-30, -5)
                x = random.randint(0, WINDOW_WIDTH)
            new_confetti.append((x, y, speed, size, color, drift))
            rect_w = size
            rect_h = size // 2 if size > 4 else size
            pygame.draw.rect(screen, color, (int(x), int(y), rect_w, rect_h))
        confetti = new_confetti

        pulse = math.sin(frame_count * 0.05) * 0.15 + 1.0
        scaled_w = int(base_text.get_width() * pulse)
        scaled_h = int(base_text.get_height() * pulse)
        scaled_text = pygame.transform.smoothscale(base_text, (scaled_w, scaled_h))
        text_rect = scaled_text.get_rect(center=(WINDOW_WIDTH // 2, 120))
        screen.blit(scaled_text, text_rect)

        alpha = min(255, frame_count * 4)
        sub_surf = font_small.render("Congratulations!", True, COLOR_VIBRANT_YELLOW)
        sub_surf.set_alpha(alpha)
        sub_rect = sub_surf.get_rect(center=(WINDOW_WIDTH // 2, 180))
        screen.blit(sub_surf, sub_rect)

        menu_btn.draw(screen, font_small)
        return_btn.draw(screen, font_small)
        restart_btn.draw(screen, font_small)

        hints = [("Main Menu", menu_btn), ("Difficulty", return_btn), ("Same Level", restart_btn)]
        for hint_text, btn in hints:
            hint_surf = hint_font.render(hint_text, True, (140, 140, 140))
            hint_rect = hint_surf.get_rect(center=(btn.rect.centerx, btn.rect.bottom + 14))
            screen.blit(hint_surf, hint_rect)

        pygame.display.flip()
        clock.tick(60)