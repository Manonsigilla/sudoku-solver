from solver import brute_force, backtracking


class SudokuGrid:
    grid: list[list[int]]
    original: list[list[int]]

    def __init__(self, filepath: str) -> None:
        """Charge et parse la grille depuis un fichier texte."""
        self.grid = []
        self.original = []
        self.load_from_file(filepath)

    def load_from_file(self, filepath: str) -> None:
        """Parse le fichier : '_' devient 0, les chiffres restent."""
        with open(filepath, "r") as f:
            lines = f.read().splitlines()

        self.grid = []
        for line in lines:
            row = []
            for char in line:
                if char == "_":
                    row.append(0)
                elif char.isdigit():
                    row.append(int(char))
            # Ignorer les lignes vides ou de séparation (ex: "---+---+---")
            if row:
                self.grid.append(row)

        if len(self.grid) != 9 or any(len(row) != 9 for row in self.grid):
            raise ValueError(f"Grille invalide : attendu 9x9")

        # Copie profonde : chaque sous-liste est dupliquée, pas juste la référence
        self.original = [row[:] for row in self.grid]

    def is_valid(self, row: int, col: int, num: int) -> bool:
        """Verifie si placer num a (row, col) respecte les regles du sudoku."""
        # Vérification ligne
        if num in self.grid[row]:
            return False

        # Vérification colonne
        if num in [self.grid[r][col] for r in range(9)]:
            return False

        # Vérification du bloc 3x3 : calcule la case en haut à gauche du bloc
        start_row = (row // 3) * 3
        start_col = (col // 3) * 3
        for r in range(start_row, start_row + 3):
            for c in range(start_col, start_col + 3):
                if self.grid[r][c] == num:
                    return False

        return True

    def is_complete(self) -> bool:
        """Retourne True si la grille n'a plus de case vide (0)."""
        for row in self.grid:
            if 0 in row:
                return False
        return True

    def display(self) -> None:
        """Affiche la grille dans le terminal avec distinction original/ajoute."""
        for r in range(9):
            if r > 0 and r % 3 == 0:
                print("------+-------+------")
            row_str = ""
            for c in range(9):
                if c > 0 and c % 3 == 0:
                    row_str += " | "
                elif c > 0:
                    row_str += " "
                val = self.grid[r][c]
                if val == 0:
                    row_str += "."
                elif self.original[r][c] == 0:
                    # Valeur ajoutée par le solveur : affichage en bleu (code ANSI)
                    row_str += f"\033[94m{val}\033[0m"
                else:
                    row_str += str(val)
            print(row_str)

    def solve_brute_force(self) -> bool:
        """Resout par force brute. Retourne True si solution trouvee."""
        # is_valid est passé en callback : le solveur l'appelle avant de placer chaque valeur
        return brute_force(self.grid, self.is_valid)

    def solve_backtracking(self) -> bool:
        """Resout par backtracking. Retourne True si solution trouvee."""
        # is_valid est passé en callback : le solveur l'appelle avant de placer chaque valeur
        return backtracking(self.grid, self.is_valid)
