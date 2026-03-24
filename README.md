# Convention de developpement -- Sudoku Solver

Ce document definit les regles de travail en equipe pour le projet Sudoku Solver.
Tout le monde s'engage a le respecter. En cas de doute, on en discute en vocal avant de decider.

---

## 1. Structure du projet

```
sudoku-solver/
  script.py      # Classe SudokuGrid (parsing, validation, affichage terminal) 
  solver.py            # Fonctions de resolution (brute force, backtracking)
  display.py           # Affichage Pygame
  main.py              # Point d'entree CLI
  grids/               # 5 fichiers exemples (.txt)
    grid_1.txt
    grid_2.txt
    grid_3.txt
    grid_4.txt
    grid_5.txt
  README.md            # Analyse comparative + contexte projet
  requirements.txt     # pygame
```

**Pourquoi cette organisation ?**
Chaque fichier correspond a un bloc de travail attribue a un membre de l'equipe.
En separant la logique de resolution (`solver.py`) de la classe principale (`script.py`),
on evite que deux personnes modifient le meme fichier en meme temps -- c'est la source
numero 1 de conflits Git dans un projet en equipe.

La classe `SudokuGrid` importe les fonctions de `solver.py` et les expose comme methodes.
Du point de vue de l'utilisateur final (et du correcteur), tout est accessible via `SudokuGrid`,
conformement a la consigne.

---

## 2. Contrat d'interface

Avant de coder quoi que ce soit, on fige les signatures des fonctions et les attributs partages.
C'est le "contrat" entre les blocs : tant que ces signatures sont respectees, chacun peut coder
librement dans son fichier sans casser le travail des autres.

```python
class SudokuGrid:
    grid: list[list[int]]        # 9x9, 0 = case vide, 1-9 = valeur
    original: list[list[int]]    # copie de la grille initiale (pour distinguer a l'affichage)

    def __init__(self, filepath: str) -> None
        """Charge et parse la grille depuis un fichier texte."""

    def load_from_file(self, filepath: str) -> None
        """Parse le fichier : '_' devient 0, les chiffres restent."""

    def is_valid(self, row: int, col: int, num: int) -> bool
        """Verifie si placer num a (row, col) respecte les regles du sudoku."""

    def is_complete(self) -> bool
        """Retourne True si la grille n'a plus de case vide (0)."""

    def display(self) -> None
        """Affiche la grille dans le terminal avec distinction original/ajoute."""

    def solve_brute_force(self) -> bool
        """Resout par force brute. Retourne True si solution trouvee."""

    def solve_backtracking(self) -> bool
        """Resout par backtracking. Retourne True si solution trouvee."""
```

**Ce que solver.py expose :**
```python
def brute_force(grid: list[list[int]], is_valid_func) -> bool
def backtracking(grid: list[list[int]], is_valid_func) -> bool
```

**Ce que display.py attend :**
Un objet `SudokuGrid` avec les attributs `.grid` et `.original` remplis.

**Regle importante :** si tu as besoin d'ajouter un attribut ou une methode, previens
l'equipe sur Discord AVANT de le faire. Les autres blocs en dependent peut-etre.

---

## 3. Repartition du travail

| Bloc | Responsabilite | Fichier(s) | Dependances |
|------|---------------|------------|-------------|
| **Bloc 1 -- Grid core** | Parsing du fichier, validation des regles, affichage terminal | `sudoku_grid.py` | Aucune (c'est la base) |
| **Bloc 2 -- Algorithmes** | Force brute, backtracking, mesure des temps d'execution | `solver.py` | Utilise `grid` et `is_valid` de Bloc 1 |
| **Bloc 3 -- Affichage + integration** | Fenetre Pygame, fichier main.py, assemblage final | `display.py`, `main.py` | Utilise `SudokuGrid` de Bloc 1 |

**Pourquoi ce decoupage ?**
- Chaque bloc a son (ses) fichier(s) dedie(s) : pas de conflit Git
- Bloc 2 et Bloc 3 dependent de Bloc 1 mais pas l'un de l'autre : ils peuvent avancer en parallele
- Bloc 3 peut commencer avec une grille en dur dans Pygame en attendant que Bloc 1 soit pret

**Astuce pour debloquer Bloc 2 et 3 :**
Bloc 1 cree un squelette minimal de `SudokuGrid` des le J1 (meme avec des methodes vides
qui retournent des valeurs par defaut). Les autres blocs peuvent alors importer et travailler
... (198lignes restantes)