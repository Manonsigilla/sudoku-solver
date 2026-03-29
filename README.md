# Sudoku Solver & Game

Outil interactif de résolution de grilles de Sudoku 9x9 en Python. Deux modes : **Jeu** pour s'entraîner, **Solver** pour analyser et comparer 5 algorithmes de résolution.

Projet réalisé dans le cadre de la formation à La Plateforme (Marseille).

## Rôles et Contributeurs

- **Louis** : `script.py` (Parsing des fichiers, génération de puzzles avec garantie d'unicité, validation des coups, cache solutions).
- **Claude** : `solver.py` (Implémentation des 5 algorithmes de résolution, benchmarking SQLite, callbacks d'animation).
- **Manon** : `display.py` (Interface graphique Pygame complète : menus, jeu interactif, solver animé, sauvegarde/reprise, scores, résultats matplotlib).

---

## Installation

1. Assurez-vous d'avoir Python 3.10+ installé.
2. Créez un environnement virtuel :

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Sur Windows: venv\Scripts\activate
   ```

3. Installez les dépendances :

   ```bash
   pip install -r requirements.txt
   ```

---

## Veille technologique

- **Peter Norvig** - "Solving Every Sudoku Puzzle" (article seminal AC-3+MRV)
- **AC-3 Algorithm** - Constraint propagation standards
- **Benchmarking standards** - Mesure de complexité vs temps réel

## Utilisation

Lancez le programme principal :

```bash
python3 main.py
```

### Mode JEU (Play)

![Flux mode jeu](docs/flux-jeu.svg)

- Cliquez sur **PLAY** et choisissez une difficulté (**EASY**, **NORMAL**, **HARD**).
- **Contrôles clavier** :
  - **Chiffre seul** : Pose une "option" (pencil mark / stash) en gris.
  - **Ctrl + Chiffre** : Valide le chiffre définitivement.
  - **Entrée** : Valide automatiquement si une seule option est présente dans la case.
  - **Flèches** ou **Souris** : Déplacement et sélection.
  - **Échap** : Menu pause (reprendre, sauvegarder et quitter, retour menu principal).
- **Sauvegarde et reprise** : La partie en cours peut être sauvegardée depuis le menu pause. Au retour, le bouton **RESUME GAME** permet de reprendre là où vous en étiez.
- **Mode Hard** : En difficulté HARD, chaque case affiche une couleur vibrante aléatoire et les pencil marks sont désactivés.
- **Scores** : Chaque partie terminée enregistre le temps et la difficulté. Le bouton **SCORES** dans le menu de difficulté affiche l'historique et les statistiques par niveau.

### Mode SOLVER

![Flux mode solver](docs/flux-solver.svg)

- Choisissez une grille parmi les fichiers présents dans `grids/`.
- Choisissez l'un des 5 algorithmes :
  1. **Brute Force** : Exploration totale (très lent, timeout 30s).
  2. **Backtracking** : Recherche récursive avec élagage.
  3. **Backtracking MRV** : Backtracking optimisé (choisit la case la plus contrainte).
  4. **Constraint Propagation** : Résolution logique pure (sans recherche).
  5. **Propagation MRV** : Algorithme le plus puissant (Norvig).
- Cliquez sur **SOLVE** pour voir l'algorithme résoudre la grille en temps réel.

---

## Benchmarking

- Chaque résolution enregistre le temps, le nombre d'itérations, le nombre de cases vides et le statut dans `results.db` (base SQLite).
- Tous les runs sont conservés (pas seulement le meilleur temps).
- Le bouton **RESULTS** dans le menu Solver ouvre un écran avec **5 onglets** :
  1. **Time** : barres groupées du temps d'exécution par algorithme et par grille (échelle log).
  2. **Iterations** : barres groupées du nombre d'itérations.
  3. **Difficulty** : courbes du temps en fonction du nombre de cases vides.
  4. **Formulas** : formules de complexité algorithmique en LaTeX.
  5. **Manage** : tableau de tous les résultats avec suppression individuelle (scroll vertical).
- **Toggle par algorithme** : 5 boutons en bas permettent de masquer/afficher chaque algorithme sur les graphiques.
- **Export** : boutons CSV (tous les résultats) et PDF (graphiques).
- **RUN ALL** : lance tous les algorithmes sur toutes les grilles depuis l'interface, avec barre de progression et annulation.
- **RESET** : supprime tous les résultats après confirmation.
- L'outil CLI `regenerate_benchmarks.py` permet de relancer tous les algorithmes sur toutes les grilles :

  ```bash
  python3 regenerate_benchmarks.py              # tous les algorithmes
  python3 regenerate_benchmarks.py --skip-brute  # sans brute force (30s de timeout par grille)
  ```

---

## Architecture Technique

![Architecture en couches](docs/archi-couches.svg)

- **`main.py`** : Point d'entrée (lance le menu Pygame).
- **`script.py`** (~440 lignes) : Logique métier -- classe `SudokuGrid`, génération de puzzles avec garantie d'unicité, validation des coups, cache `solutions.json`.
- **`solver.py`** (~885 lignes) : Algorithmes de résolution (5 algorithmes), benchmarking SQLite (`results.db`), CRUD (suppression, mise à jour), `run_all_benchmarks()`.
- **`display.py`** (~2400 lignes) : Interface Pygame complète -- `SceneManager` (transitions), `GameState`, `Button`, sauvegarde/reprise JSON, menus, jeu interactif, solver animé, graphiques matplotlib (5 onglets), système audio (6 SFX + 2 musiques).
- **`regenerate_benchmarks.py`** : Outil CLI pour relancer les benchmarks sur toutes les grilles.
- **`grids/`** : Fichiers de grilles au format texte (`_` pour vide).
- **`sounds/`** : 6 effets sonores (`click`, `select`, `place`, `error`, `victory`, `ding`) et 2 musiques de fond (`ambient_calm.ogg`, `mondotek_alive.ogg`).
- **`saves/`** : Sauvegardes JSON des parties (`scores.json`, `current_game.json`).
- **`solutions.json`** : Cache puzzle vers solution (évite de résoudre deux fois la même grille).
- **`results.db`** : Base SQLite des benchmarks (exclue du Git).

---

## Audio

L'application inclut un système audio complet avec mute/volume :

- **Effets sonores** : `click` (bouton), `select` (case), `place` (chiffre correct), `error` (mauvaise réponse), `victory` (puzzle terminé), `ding` (fin solver).
- **Musiques de fond** : `ambient_calm.ogg` (mode jeu, 30% volume), `mondotek_alive.ogg` (écran résultats).
- **Contrôles** : bouton mute (M/S) + slider de volume, affichés en bas à droite de chaque écran.

Les fichiers audio sont dans `sounds/`. L'application fonctionne sans problème si le dossier est absent (fallback silencieux).

---
