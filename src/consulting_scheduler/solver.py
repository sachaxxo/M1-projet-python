r"""Résolution par programmation dynamique du problème d'affectation.

Le problème (Sujet 06)
----------------------
Une société de conseil doit organiser les affectations d'une équipe sur
``n`` semaines. Chaque semaine, on peut choisir une de trois actions :

* **facile** : rapporte ``l_i`` ;
* **difficile** : rapporte ``h_i``, mais *uniquement* si la semaine
  ``i - 1`` est une semaine de **repos** ;
* **repos** : rapporte 0.

Objectif : maximiser la somme des profits sur ``n`` semaines.

Récurrence
----------
Soit ``OPT(i)`` le gain maximal atteignable pour les semaines ``1..i``.

.. math::

    OPT(0) = 0

    OPT(i) = \\max \\bigl(
        OPT(i-1),           \\quad\\text{# repos en } i  \\\\
        OPT(i-1) + l_i,     \\quad\\text{# facile en } i  \\\\
        OPT(i-2) + h_i      \\quad\\text{# difficile en } i
    \\bigr)

La convention ``OPT(-1) = 0`` permet le cas ``i = 1`` (un travail difficile
en semaine 1 ne demande pas de repos préalable puisqu'il n'y a pas de
semaine 0).

Correction
----------
La récurrence énumère exhaustivement les trois actions possibles pour la
dernière semaine. Pour un choix donné, la suite optimale sur les semaines
précédentes est un sous-problème de même nature, indépendant du choix
présent (sauf pour *difficile*, qui force un repos en ``i-1`` — ce qui
est capturé en sautant à ``OPT(i-2)``). Le principe d'optimalité de
Bellman s'applique donc.

Complexité
----------
Temps : :math:`O(n)`. Mémoire : :math:`O(n)` (nécessaire pour la
reconstruction du planning).
"""

from __future__ import annotations

from collections.abc import Sequence

from consulting_scheduler.models import Problem, ScheduleResult, WeekTask


def solve(problem: Problem) -> ScheduleResult:
    """Calcule le gain optimal et le planning associé.

    Args:
        problem: instance du problème à résoudre.

    Returns:
        Un :class:`ScheduleResult` contenant le gain optimal et le planning.
    """
    n = problem.n
    if n == 0:
        return ScheduleResult(total_gain=0, schedule=())

    easy = problem.easy
    hard = problem.hard

    # dp[i] = OPT(i), gain maximal pour les semaines 1..i
    dp: list[int] = [0] * (n + 1)

    # choice[i] = action retenue pour la semaine i dans la solution optimale
    # (initialisée à REST ; les semaines effectivement REST dans le planning
    # final sont celles imposées par un travail difficile en i+1 ou,
    # rarement, un pur repos volontaire si les profits sont négatifs).
    choice: list[WeekTask] = [WeekTask.REST] * (n + 1)

    for i in range(1, n + 1):
        rest_gain = dp[i - 1]
        easy_gain = dp[i - 1] + easy[i - 1]
        # dp[-1] traité comme 0 (aucun historique avant la semaine 1)
        hard_gain = (dp[i - 2] if i >= 2 else 0) + hard[i - 1]

        # On choisit strictement la meilleure action ; en cas d'égalité,
        # on privilégie EASY > HARD > REST pour produire un planning stable.
        best_gain = rest_gain
        best_choice = WeekTask.REST
        if easy_gain > best_gain:
            best_gain = easy_gain
            best_choice = WeekTask.EASY
        if hard_gain > best_gain:
            best_gain = hard_gain
            best_choice = WeekTask.HARD

        dp[i] = best_gain
        choice[i] = best_choice

    # Reconstruction du planning en remontant depuis la semaine n.
    schedule: list[WeekTask] = [WeekTask.REST] * n
    i = n
    while i >= 1:
        action = choice[i]
        schedule[i - 1] = action
        if action is WeekTask.HARD:
            # La semaine i-1 est forcément un repos imposé.
            if i - 2 >= 0:
                schedule[i - 2] = WeekTask.REST
            i -= 2
        else:
            i -= 1

    return ScheduleResult(total_gain=dp[n], schedule=tuple(schedule))


def solve_schedule(
    easy: Sequence[int], hard: Sequence[int]
) -> ScheduleResult:
    """Variante pratique prenant directement deux séquences d'entiers.

    Équivalent à ``solve(Problem.from_sequences(easy, hard))``.
    """
    return solve(Problem.from_sequences(easy, hard))
