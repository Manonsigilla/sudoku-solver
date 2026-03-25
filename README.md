# Sudoku Solver

Outil de résolution de grilles de Sudoku 9x9 en Python. Le programme lit une grille depuis un fichier texte, la résout avec l'un des cinq algorithmes disponibles, et affiche le résultat dans le terminal ou dans une fenêtre Pygame interactive.

Projet réalisé dans le cadre de la formation à La Plateforme (Marseille).

## Structure du projet

```
sudoku-solver-repo/
  script.py          # Classe SudokuGrid (parsing, validation, affichage)
  solver.py          # 5 algorithmes de résolution
  display.py         # Interface Pygame interactive
  main.py            # Point d'entrée CLI
  benchmark.py       # Mesure des performances (SQLite)
  results_window.py  # Graphes matplotlib des résultats
  grids/             # 5 grilles d'exemple (grid_1.txt à grid_5.txt)
  requirements.txt   # Dépendances (pygame, matplotlib, numpy)
```

## Utilisation

```bash
# Résolution dans le terminal (backtracking par défaut)
python3 main.py grids/grid_1.txt

# Choix de l'algorithme
python3 main.py grids/grid_1.txt --algo propagation_mrv

# Interface Pygame interactive
python3 main.py grids/grid_1.txt --gui

# Benchmark de tous les algorithmes sur une grille
python3 main.py grids/grid_1.txt --benchmark

# Consulter les résultats historiques
python3 main.py --results
```

Algorithmes disponibles via `--algo` : `brute`, `backtrack`, `backtrack_mrv`, `propagation`, `propagation_mrv`.

## Algorithmes implémentés

### 1. Force brute

Remplit toutes les cases vides avec les chiffres 1 à 9 sans vérification intermédiaire. La grille n'est validée qu'une fois entièrement remplie. Timeout fixé à 30 secondes.

Complexité : **O(9^m)** où *m* est le nombre de cases vides. Pour une grille avec 50 cases vides, l'espace de recherche théorique dépasse 10^47 combinaisons. En pratique, l'algorithme atteint le timeout sur la plupart des grilles non triviales.

### 2. Backtracking

Parcours en profondeur (DFS) avec élagage. Avant de placer un chiffre, l'algorithme vérifie qu'il ne viole aucune contrainte (ligne, colonne, bloc 3x3). Si un placement mène à une impasse, il revient en arrière et essaie le chiffre suivant.

Complexité : **O(9^m)** dans le pire cas, mais l'élagage réduit l'espace réel de plusieurs ordres de grandeur. Résout les grilles faciles à moyennes en quelques millisecondes.

### 3. Backtracking + MRV

Même principe que le backtracking classique, avec une heuristique de sélection de variable : à chaque étape, l'algorithme choisit la case ayant le moins de candidats valides (Minimum Remaining Values). Cette stratégie réduit le facteur de branchement et accélère la convergence.

Complexité : **O(9^m)** dans le pire cas. En pratique, le MRV divise le temps de résolution par un facteur 10 à 50 sur les grilles difficiles (grid_4 : 17.5 ms en backtracking classique vs 0.5 ms avec MRV).

### 4. Propagation de contraintes (AC-3)

Modélisation du Sudoku comme un problème de satisfaction de contraintes (CSP). L'algorithme applique deux règles de déduction en boucle :

- **Naked Single** : une case n'a qu'un seul candidat possible, on le place.
- **Hidden Single** : dans une unité (ligne, colonne ou bloc), un chiffre ne peut aller qu'à un seul endroit, on le place là.

Pas de recherche. L'algorithme s'arrête quand plus aucune déduction n'est possible. Suffisant pour les grilles faciles et moyennes, mais échoue sur les grilles qui nécessitent des hypothèses (grid_2, grid_5).

Complexité : **O(d * n)** où *d* est la taille du domaine (9) et *n* le nombre de cases.

### 5. Propagation + MRV (approche Norvig)

Combine la propagation AC-3 avec un backtracking MRV pour les cas où la déduction seule ne suffit pas. C'est l'implémentation de l'approche décrite par Peter Norvig dans *Solving Every Sudoku Puzzle*.

Phase 1 : propager les contraintes. Phase 2 : si la grille n'est pas résolue, choisir la case MRV, essayer chaque candidat avec une copie de l'état, et relancer la propagation récursivement.

Complexité : **O(d * n)** pour la propagation, plus la recherche résiduelle. Résout toutes les grilles testées en moins de 2 ms.

## Analyse comparative

### Complexité théorique

| Algorithme | Complexité | Particularité |
|---|---|---|
| Force brute | O(9^m) | Aucun élagage, timeout 30 s |
| Backtracking | O(9^m) pire cas | Élagage par vérification avant placement |
| Backtracking + MRV | O(9^m) pire cas | Heuristique de choix de variable |
| Propagation AC-3 | O(d * n) | Déduction pure, pas de recherche |
| Propagation + MRV | O(d * n) + résiduel | Déduction + recherche si nécessaire |

### Temps d'exécution mesurés

Mesures sur un CPU AMD Ryzen (un seul thread, Python 3.12).

| Grille | Cases vides | Backtracking | Back.+MRV | AC-3 | AC-3+MRV |
|---|---|---|---|---|---|
| grid_1 | 45 | 0.54 ms | 0.33 ms | 0.65 ms | 0.62 ms |
| grid_2 | 52 | 2.87 ms | 0.47 ms | échec | 1.68 ms |
| grid_3 | 43 | 0.26 ms | 0.21 ms | 0.51 ms | 0.49 ms |
| grid_4 | 57 | 17.50 ms | 0.50 ms | 1.07 ms | 1.03 ms |
| grid_5 | 58 | 8.28 ms | 0.29 ms | échec | 1.77 ms |

La force brute n'apparaît pas dans le tableau : elle atteint systématiquement le timeout de 30 secondes sur les grilles à plus de ~25 cases vides.

### Observations

La difficulté d'une grille ne dépend pas uniquement du nombre de cases vides. grid_4 (57 vides) prend 17.5 ms en backtracking classique, tandis que grid_5 (58 vides) n'en prend que 8.3 ms. La structure des contraintes initiales compte autant que la quantité de cases à remplir.

Le backtracking classique souffre d'un défaut : il choisit la première case vide en balayant de gauche à droite, sans considérer les contraintes. Le MRV corrige ce problème. Sur grid_4, le gain est d'un facteur 35.

La propagation AC-3 seule ne résout pas toutes les grilles. grid_2 et grid_5 nécessitent des hypothèses que la déduction pure ne peut pas fournir. L'ajout du backtracking MRV en fallback (approche Norvig) rend l'algorithme complet.

### Conclusion

Le backtracking + MRV offre le meilleur compromis entre performance et simplicité. Il résout toutes les grilles testées en moins d'une milliseconde et ne nécessite pas de structures de données auxiliaires complexes.

L'approche Norvig (propagation + MRV) est la plus robuste : elle combine déduction logique et recherche. Sur les grilles faciles, la propagation seule suffit et la recherche n'est jamais déclenchée. Sur les grilles difficiles, le backtracking MRV prend le relais avec un arbre de recherche déjà réduit par la propagation.

La force brute n'a qu'une valeur pédagogique. Elle met en évidence l'explosion combinatoire et justifie les techniques d'élagage.

## Outils et technologies

- **Python 3.12** : langage principal
- **Pygame 2.6.1** : interface graphique interactive (grille, boutons Solve/Reset, animation)
- **matplotlib + numpy** : graphes comparatifs des performances
- **SQLite** : persistance des résultats de benchmark
- **argparse** : interface en ligne de commande

## Veille technologique

Le Sudoku généralisé (grilles n^2 x n^2) est un problème NP-complet. McGuire et al. (2012) ont prouvé qu'une grille 9x9 nécessite au minimum 17 indices pour admettre une solution unique.

Les solveurs les plus performants aujourd'hui utilisent des approches radicalement différentes de celles implémentées ici :

- **Dancing Links (DLX)** de Knuth : réduction du Sudoku en problème de couverture exacte, résolu via l'Algorithme X avec des listes doublement chaînées circulaires. Temps de résolution typique sous la microseconde.
- **Solveurs SAT** : traduction en formule booléenne (729 variables, ~9 000 clauses) et résolution par CDCL (Conflict-Driven Clause Learning). Exploite 30 ans d'optimisation des solveurs SAT.
- **tdoku** : le solveur le plus rapide connu, utilise la propagation de contraintes vectorisée (instructions SIMD) pour traiter plusieurs candidats en parallèle.

Ces approches dépassent le cadre du projet mais illustrent la richesse algorithmique du problème.

### Références

- Peter Norvig, *Solving Every Sudoku Puzzle* (norvig.com/sudoku.html)
- Donald Knuth, *Dancing Links* (2000), arXiv:cs/0011047
- McGuire, Tugemann, Civario, *There is no 16-Clue Sudoku* (2012)
- Lynce & Ouaknine, *Sudoku as a SAT Problem* (2006)
