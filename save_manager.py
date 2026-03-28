import json
import os
from datetime import datetime

# File paths
SAVES_DIR = "saves"
SCORES_FILE = os.path.join(SAVES_DIR, "scores.json")
CURRENT_SAVE_FILE = os.path.join(SAVES_DIR, "current_game.json")

# Default data structures
DEFAULT_SCORES_DATA = {
    "games": []
}

DEFAULT_GAME_SAVE = {
    "difficulty": "normal",
    "current_grid": [],
    "original_grid": [],
    "stash": {},
    "cell_status": {},
    "selected_cell": (0, 0),
    "timestamp": "",
}


def init_saves_dir():
    """Create saves directory if it doesn't exist."""
    if not os.path.exists(SAVES_DIR):
        os.makedirs(SAVES_DIR)
        print(f"[OK] Created saves directory: {SAVES_DIR}")


def load_scores():
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


def save_score(difficulty, time_seconds, completed_cells, timestamp=None):
    """Save a completed game score to the JSON file.
    
    Args:
        difficulty (str): 'easy', 'normal', or 'hard'
        time_seconds (float): Time taken to complete the game
        completed_cells (int): Number of cells filled by player (not original)
        timestamp (str): ISO format timestamp (auto-generated if None)
    """
    init_saves_dir()
    
    if timestamp is None:
        timestamp = datetime.now().isoformat()
    
    # Load existing scores
    scores = load_scores()
    
    # Create new score entry
    new_score = {
        "difficulty": difficulty,
        "time_seconds": round(time_seconds, 2),
        "completed_cells": completed_cells,
        "timestamp": timestamp,
    }
    
    # Add to list
    scores.append(new_score)
    
    # Save back to file
    data = {"games": scores}
    try:
        with open(SCORES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[OK] Score saved: {difficulty} in {time_seconds:.1f}s")
    except IOError as e:
        print(f"[ERROR] Could not save score: {e}")


def save_game(game_state, elapsed_time=0):
    """Save current game state for pause/resume functionality.
    
    Args:
        game_state (GameState): The current game state object
        elapsed_time (float): Time elapsed so far (in seconds)
    """
    init_saves_dir()
    
    # Prepare save data
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
    
    try:
        with open(CURRENT_SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        print(f"[OK] Game saved (time: {elapsed_time:.1f}s)")
    except IOError as e:
        print(f"[ERROR] Could not save game: {e}")


def load_game():
    """Load saved game state. Returns None if no save exists.
    
    Returns:
        dict: Save data or None if file doesn't exist
    """
    init_saves_dir()
    
    if not os.path.exists(CURRENT_SAVE_FILE):
        return None
    
    try:
        with open(CURRENT_SAVE_FILE, "r", encoding="utf-8") as f:
            save_data = json.load(f)
        print(f"[OK] Game loaded: {save_data['difficulty']}")
        return save_data
    except (json.JSONDecodeError, IOError) as e:
        print(f"[WARN] Could not load game: {e}")
        return None


def delete_save():
    """Delete the current game save."""
    if os.path.exists(CURRENT_SAVE_FILE):
        try:
            os.remove(CURRENT_SAVE_FILE)
            print(f"[OK] Game save deleted")
        except IOError as e:
            print(f"[ERROR] Could not delete save: {e}")


def has_save():
    """Check if a saved game exists."""
    return os.path.exists(CURRENT_SAVE_FILE)


def get_score_stats(scores):
    """Calculate statistics from scores list.
    
    Args:
        scores (list): List of score dictionaries
    
    Returns:
        dict: Statistics (avg time per difficulty, total games, etc.)
    """
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
        difficulty = score["difficulty"]
        if difficulty in stats:
            stats[difficulty]["count"] += 1
            stats[difficulty]["times"].append(score["time_seconds"])
    
    # Calculate averages
    for difficulty in ["easy", "normal", "hard"]:
        if stats[difficulty]["count"] > 0:
            avg = sum(stats[difficulty]["times"]) / stats[difficulty]["count"]
            stats[difficulty]["avg_time"] = round(avg, 2)
        del stats[difficulty]["times"]
    
    return stats