import pygame
import sys
import random
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
        self.selected_cell = None
        self.hard_mode_cell_colors = {}
        self.generate_hard_mode_colors()
    
    def generate_hard_mode_colors(self):
        self.hard_mode_cell_colors = {(r, c): random.choice(HARD_MODE_COLORS) for r in range(9) for c in range(9)}
    
    def randomize_hard_colors(self):
        self.generate_hard_mode_colors()
    
    def select_cell(self, row: int, col: int):
        if self.original_grid[row][col] == 0:
            self.selected_cell = (row, col)
    
    def add_to_stash(self, num: int):
        if not self.selected_cell or self.difficulty == "hard":
            return False
        row, col = self.selected_cell
        if self.original_grid[row][col] != 0:
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
        status = validate_move(self.current_grid, self.solved_grid, row, col, num)
        if status == "correct":
            self.current_grid[row][col] = num
            self.cell_status[(row, col)] = "correct"
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
                    solver_menu()
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
                if easy_btn.is_clicked(event.pos):
                    play_game("easy")
                    return
                elif normal_btn.is_clicked(event.pos):
                    play_game("normal")
                    return
                elif hard_btn.is_clicked(event.pos):
                    play_game("hard")
                    return
        
        screen.fill(COLOR_WHITE)
        title = font_large.render("SELECT DIFFICULTY", True, COLOR_BLACK)
        screen.blit(title, (50, 20))
        easy_btn.draw(screen, font_small)
        normal_btn.draw(screen, font_small)
        hard_btn.draw(screen, font_small)
        pygame.display.flip()

def solver_menu():
    screen = pygame.display.get_surface()
    font = pygame.font.SysFont("arial", 20)
    
    text = "SOLVER MODE\nSelect a grid file\n(Feature: Use terminal with --help)"
    lines = text.split("\n")
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
        
        screen.fill(COLOR_WHITE)
        y = 100
        for line in lines:
            text_surf = font.render(line, True, COLOR_BLACK)
            screen.blit(text_surf, (150, y))
            y += 30
        
        back_text = font.render("Press ESC to go back", True, COLOR_LIGHT_BLUE)
        screen.blit(back_text, (140, 250))
        pygame.display.flip()

def play_game(difficulty: str):
    game_state = GameState(difficulty)
    screen = pygame.display.get_surface()
    pygame.display.set_caption(f"Sudoku - {difficulty.upper()}")
    clock = pygame.time.Clock()
    font_large = pygame.font.SysFont("arial", 36)
    font_small = pygame.font.SysFont("arial", 10)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return
                elif pygame.K_1 <= event.key <= pygame.K_9:
                    num = event.key - pygame.K_0
                    if event.mod & pygame.KMOD_SHIFT:
                        game_state.validate_move(num)
                    else:
                        game_state.add_to_stash(num)
                elif event.key == pygame.K_RETURN:
                    if game_state.selected_cell and game_state.selected_cell in game_state.stash:
                        num = max(game_state.stash[game_state.selected_cell])
                        game_state.validate_move(num)
                elif event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                    if game_state.selected_cell:
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
            show_victory_screen()
            return
        
        screen.fill(COLOR_WHITE)
        draw_grid(screen, game_state, font_large, font_small)
        pygame.display.flip()
        clock.tick(60)

def draw_grid(screen, game_state, font_large, font_small):
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
            
            if game_state.current_grid[row][col] != 0:
                num = game_state.current_grid[row][col]
                color = COLOR_BLACK if game_state.original_grid[row][col] != 0 else (0, 100, 200)
                text = font_large.render(str(num), True, color)
                text_rect = text.get_rect(center=(x + CELL_SIZE // 2, y + CELL_SIZE // 2))
                screen.blit(text, text_rect)
            
            if cell_coord in game_state.stash:
                for idx, num in enumerate(sorted(game_state.stash[cell_coord])):
                    sx = x + 5 + (idx % 3) * 15
                    sy = y + 5 + (idx // 3) * 12
                    text = font_small.render(str(num), True, COLOR_PASTEL_GRAY)
                    screen.blit(text, (sx, sy))
            
            if game_state.selected_cell == cell_coord:
                pygame.draw.rect(screen, (100, 149, 237), (x, y, CELL_SIZE, CELL_SIZE), 3)

def show_victory_screen():
    screen = pygame.display.get_surface()
    font = pygame.font.SysFont("arial", 48)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                return
        
        screen.fill(COLOR_WHITE)
        text = font.render("PUZZLE SOLVED!", True, (0, 200, 0))
        text_rect = text.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2))
        screen.blit(text, text_rect)
        small_font = pygame.font.SysFont("arial", 20)
        press_text = small_font.render("Click or press any key to continue", True, COLOR_BLACK)
        screen.blit(press_text, (100, WINDOW_SIZE - 50))
        pygame.display.flip()

if __name__ == "__main__":
    main_menu()