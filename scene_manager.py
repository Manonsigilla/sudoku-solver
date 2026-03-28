"""
Scene manager for consistent window sizing and transitions.
All scenes use the same window size to prevent rendering issues.
"""

import pygame

# Global window size (fixed for all scenes)
WINDOW_WIDTH = 700
WINDOW_HEIGHT = 700

class SceneManager:
    """Manages scene transitions and maintains consistent window size."""
    
    def __init__(self):
        """Initialize the scene manager."""
        self.window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.current_scene = None
    
    def set_scene(self, scene_name):
        """Set the current scene (mainly for tracking/debugging)."""
        self.current_scene = scene_name
        pygame.display.set_caption(f"Sudoku - {scene_name}")
    
    def get_window(self):
        """Return the global window surface."""
        return self.window
    
    def get_size(self):
        """Return window dimensions."""
        return WINDOW_WIDTH, WINDOW_HEIGHT
    
    def clear(self):
        """Clear the window (prevents ghosting/overlapping)."""
        self.window.fill((0, 0, 0))
        pygame.display.flip()

# Global instance
scene_manager = SceneManager()