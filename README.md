# consulting-scheduler

> Résolution optimale du **Sujet 06** — affectation hebdomadaire d'une équipe de consultants — par **programmation dynamique**, avec CLI colorée et interface graphique Streamlit.

```
╭─── Gain optimal ───╮
│   100 €            │
╰────────────────────╯
            Planning optimal
┏━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Semaine ┃ Action     ┃ Gain (€) ┃
┡━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━┩
│       1 │ repos      │        0 │
│       2 │ difficile  │       50 │
│       3 │ repos      │        0 │
│       4 │ difficile  │       50 │
└─────────┴────────────┴──────────┘
```

## Le problème

> Une société de conseil doit organiser les affectations à venir d'une de ses équipes. Les travaux hebdomadaires disponibles sont soit faciles, soit difficiles. Si on effectue un travail facile en semaine *i*, on obtient `l_i` euros ; on obtient `h_i` pour un travail difficile. Effectuer un travail difficile en semaine *i* nécessite d'avoir eu une **semaine de repos** en *i − 1*. Donner une organisation optimale étant donnés `l_1, …, l_n` et `h_1, …, h_n`.

Trois actions possibles chaque semaine :

- 🟢 **facile** — rapporte `l_i`, pas de contrainte ;
- 🟡 **difficile** — rapporte `h_i`, exige un repos en *i − 1* ;
- 💤 **repos** — rapporte 0.

Objectif : **maximiser** la somme des profits sur `n` semaines.

## Aperçu du package

Le package `consulting_scheduler` fournit :

- un solveur **O(n)** en temps et en mémoire (`solve`, `solve_schedule`) ;
- des types immuables et typés strictement (`Problem`, `ScheduleResult`, `WeekTask`) ;
- une **CLI** colorée `consulting-scheduler` (Typer + Rich) ;
- une **interface graphique** Streamlit avec deux modes de saisie ;
- un **notebook** d'illustration ;
- une **suite de tests** : unitaires, cohérence, property-based (`hypothesis`), oracle brute-force.

## Idée mathématique (résumé)

Soit `OPT(i)` le gain maximal sur les semaines `1..i`. On a

```
OPT(0) = 0
OPT(i) = max(
    OPT(i-1),           # repos en semaine i
    OPT(i-1) + l_i,     # facile en semaine i
    OPT(i-2) + h_i      # difficile en semaine i (force un repos en i-1)
)
```

La récurrence complète et sa preuve de correction sont développées dans [`docs/algorithm.md`](docs/algorithm.md).

## Installation

### Avec `uv` (recommandé)

`uv` installe automatiquement la bonne version de Python (3.11+), crée l'environnement virtuel et synchronise les dépendances.

```bash
# À la racine du projet
uv sync --all-extras          # crée .venv et installe prod + GUI + dev

# Activation optionnelle (uv run fonctionne sans) :
source .venv/bin/activate     # macOS / Linux
# .venv\Scripts\activate      # Windows
```

Pour installer uniquement la GUI :

```bash
uv sync --extra gui
```

Pour (re)générer le `uv.lock` reproductible :

```bash
uv lock
```

### Avec `pip`

```bash
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows
pip install -e ".[gui,dev]"
```

## Utilisation

### Interface graphique (Streamlit)

```bash
consulting-scheduler gui          # via la CLI
# ou
consulting-scheduler-gui          # script dédié
# ou
streamlit run src/consulting_scheduler/app.py
```

L'application ouvre un onglet de navigateur local avec :

| Section                 | Contenu                                                                                  |
|-------------------------|------------------------------------------------------------------------------------------|
| **Sidebar**             | rappel du problème, légende couleurs, bouton « Charger l'exemple », bouton « Effacer ». |
| **⚡ Saisie rapide**     | deux champs CSV (`l_i`, `h_i`) — équivalent à la CLI.                                    |
| **📋 Tableau éditable** | un tableau dynamique : ajout/suppression de semaines, validation des entiers.            |
| **Résultats**           | gain total, planning coloré, barres profits par semaine, gain cumulé, export CSV.        |

Aperçu textuel de l'écran :

```
📅 Consulting Scheduler                Planificateur d'affectations hebdomadaires
v0.1.0 — Sujet 06 (DP)                ──────────────────────────────────────────
                                       ⚡ Saisie rapide (CSV)  📋 Tableau éditable
🟢 facile  (l_i)
🟡 difficile (h_i, repos avant)        Profits faciles    : 10,1,10,10
💤 repos  (0)                          Profits difficiles : 5,50,5,50
                                       [ ▶ Résoudre depuis le CSV ]
[📦 Charger l'exemple]
[🗑 Tout effacer]                       💰 100 €  🟢 0  🟡 2  💤 2

                                       Planning optimal
                                       ┌──────┬──────────────┬─────────┐
                                       │  1   │ 💤 repos     │   0 €   │
                                       │  2   │ 🟡 difficile │  50 €   │
                                       │  3   │ 💤 repos     │   0 €   │
                                       │  4   │ 🟡 difficile │  50 €   │
                                       └──────┴──────────────┴─────────┘
```

### En ligne de commande

```bash
consulting-scheduler solve --easy 10,1,10,10 --hard 5,50,5,50
consulting-scheduler example          # exemple classique
consulting-scheduler --version
```

### Depuis Python

```python
from consulting_scheduler import solve_schedule

result = solve_schedule(easy=[10, 1, 10, 10], hard=[5, 50, 5, 50])
print(result.total_gain)     # 100
print(result.schedule)       # (REST, HARD, REST, HARD)
print(result.pretty())
```

## Structure du projet

```
consulting-scheduler/
├── docs/
│   └── algorithm.md              # Preuve & complexité
├── notebooks/
│   └── example_problem.ipynb     # Démo interactive
├── src/
│   └── consulting_scheduler/
│       ├── __init__.py
│       ├── models.py             # WeekTask, Problem, ScheduleResult
│       ├── solver.py             # Cœur du DP
│       ├── cli.py                # CLI Typer + Rich (+ run_gui)
│       └── app.py                # Interface graphique Streamlit
├── tests/
│   ├── test_models.py
│   ├── test_solver.py            # + property-based + oracle brute-force
│   └── test_app.py               # GUI : helpers + smoke import
├── main.py                       # Point d'entrée sans install
├── pyproject.toml
├── .pre-commit-config.yaml
├── .python-version
├── .gitignore
└── README.md
```

## Qualité & outillage

```bash
pytest --cov=consulting_scheduler     # tests + couverture
ruff check .                          # lint
ruff format .                         # formatage
mypy src                              # typage strict
pre-commit run --all-files            # tout d'un coup
```

## Pistes d'amélioration

- Extension à plusieurs équipes en parallèle.
- Contraintes supplémentaires (max de semaines difficiles consécutives, congés imposés…).
- Chargement CSV / import JSON depuis la GUI.
- Mode comparaison de scénarios côte-à-côte.
- Heatmap des profits sur de longues séries (`n ≫ 20`).
