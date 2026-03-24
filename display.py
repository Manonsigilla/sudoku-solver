import pygame
import sys

# Constants for the display
WINDOW_SIZE = 540  # 540 is easily divisible by 9 (60 pixels per cell)
CELL_SIZE = WINDOW_SIZE // 9
BACKGROUND_COLOR = (255, 255, 255)
LINE_COLOR = (0, 0, 0)
NUMBER_COLOR = (0, 0, 0)

def draw_grid_lines(screen: pygame.Surface) -> None:
    """Draws the 9x9 grid lines on the screen."""
    for i in range(10):
        # Every 3rd line is thicker to separate the 3x3 blocks
        thickness = 3 if i % 3 == 0 else 1
        
        # Draw vertical lines
        pygame.draw.line(screen, LINE_COLOR, (i * CELL_SIZE, 0), (i * CELL_SIZE, WINDOW_SIZE), thickness)
        # Draw horizontal lines
        pygame.draw.line(screen, LINE_COLOR, (0, i * CELL_SIZE), (WINDOW_SIZE, i * CELL_SIZE), thickness)

def draw_numbers(screen: pygame.Surface, grid: list[list[int]]) -> None:
    """Draws the numbers from the 2D array onto the Pygame screen."""
    font = pygame.font.SysFont("arial", 40)
    
    for row in range(9):
        for col in range(9):
            num = grid[row][col]
            if num != 0:  # 0 represents an empty cell
                # Render the text
                text_surface = font.render(str(num), True, NUMBER_COLOR)
                
                # Center the number inside the cell
                text_rect = text_surface.get_rect()
                text_rect.center = (col * CELL_SIZE + CELL_SIZE // 2, row * CELL_SIZE + CELL_SIZE // 2)
                
                screen.blit(text_surface, text_rect)

def draw_sudoku_window(grid: list[list[int]]) -> None:
    """
    Initializes Pygame, draws the solved grid, and waits for the user to close the window.
    """
    pygame.init()
    
    # Set up the display
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
    pygame.display.set_caption("Sudoku Solver")
    
    # Main application loop
    running = True
    while running:
        for event in pygame.event.get():
            # Handle window close event
            if event.type == pygame.QUIT:
                running = False
                
        # Fill background
        screen.fill(BACKGROUND_COLOR)
        
        # Draw the grid and the numbers
        draw_grid_lines(screen)
        draw_numbers(screen, grid)
        
        # Update the display
        pygame.display.flip()
        
    # Quit gracefully when the loop ends
    pygame.quit()