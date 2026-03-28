# Sudoku Solver & Game

Outil interactif de résolution de grilles de Sudoku 9x9 en Python. Le projet propose un mode **Jeu** pour s'entraîner, et un mode **Solver** pour analyser et comparer 5 algorithmes de résolution.

Projet réalisé dans le cadre de la formation à La Plateforme (Marseille).

## 👥 Rôles et Contributeurs

- **Louis** : `script.py` (Parsing des fichiers, structure globale de la grille, validation des règles Sudoku).
- **Claude** : `solver.py` (Implémentation des 5 algorithmes de résolution, gestion des callbacks d'animation).
- **Manon** : `display.py` & `game_manager.py` (Interface graphique Pygame, logique de jeu, système de benchmark, gestion des difficultés).

---

## 🚀 Installation

1.  Assurez-vous d'avoir Python 3.10+ installé.
2.  Créez un environnement virtuel :
    ```bash
    python -m venv venv
    source venv/bin/activate  # Sur Windows: venv\Scripts\activate
    ```
3.  Installez les dépendances :
    ```bash
    pip install -r requirements.txt
    ```

---

## 🎮 Comment l'utiliser ?

Lancez le programme principal :
```bash
python main.py
```

### Mode JEU (Play)
- Cliquez sur **PLAY** et choisissez une difficulté (**EASY**, **NORMAL**, **HARD**).
- **Contrôles clavier** :
  - **Chiffre seul** : Pose une "option" (pencil mark / stash) en gris.
  - **Ctrl + Chiffre** : Valide le chiffre définitivement.
  - **Entrée** : Valide automatiquement si une seule option est présente dans la case.
  - **Flèches** ou **Souris** : Déplacement et sélection.
  - **Échap** : Retour au menu.

### Mode SOLVER
- Choisissez une grille parmi les fichiers présents dans `grids/`.
- Choisissez l'un des 5 algorithmes :
  1.  **Brute Force** : Exploration totale (très lent, timeout 30s).
  2.  **Backtracking** : Recherche récursive avec élagage.
  3.  **Backtracking MRV** : Backtracking optimisé (choisit la case la plus contrainte).
  4.  **Constraint Propagation** : Résolution logique pure (sans recherche).
  5.  **Propagation MRV** : Algorithme le plus puissant (Norvig).
- Cliquez sur **SOLVE** pour voir l'algorithme résoudre la grille en temps réel.

---

## 📊 Benchmarking & Performance

Le projet inclut un système de mesure automatique.
- Après chaque résolution réussie, le temps est enregistré dans `benchmarks.json`.
- **Zéro doublon** : Seul le **meilleur temps** (le record) est conservé pour chaque couple (Grille | Algorithme).
- Les statistiques (nombre d'étapes et temps) s'affichent sur l'écran final après la résolution.

---

## 📂 Architecture Technique

- **`main.py`** : Point d'entrée lançant le menu Pygame.
- **`display.py`** : Moteur graphique et gestion des événements utilisateurs.
- **`solver.py`** : Cœur algorithmique indépendant de l'affichage.
- **`game_manager.py`** : Logique de génération et validation des puzzles.
- **`script.py`** : Parseur de fichiers `.txt` et utilitaires de grille.
- **`grids/`** : Dossier contenant les fichiers de grilles au format texte (`_` pour vide).
- **`benchmarks.json`** : Fichier local (exclu du Git) stockant vos records personnels.

