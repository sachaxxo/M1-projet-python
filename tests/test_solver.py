"""Tests du solveur : cas simples, cas limites, cohérence, property-based."""

from __future__ import annotations

import random

import pytest
from hypothesis import given
from hypothesis import strategies as st

from consulting_scheduler import Problem, WeekTask, solve, solve_schedule

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _brute_force_max_gain(easy: list[int], hard: list[int]) -> int:
    """Recherche exhaustive du gain optimal — référence pour tester le DP.

    Destinée aux petites instances (n <= 8).
    """
    n = len(easy)
    if n == 0:
        return 0

    best = -(10**18)

    def rec(i: int, rested_prev: bool, gain: int) -> None:
        nonlocal best
        if i == n:
            best = max(best, gain)
            return
        rec(i + 1, True, gain)
        rec(i + 1, False, gain + easy[i])
        if rested_prev or i == 0:
            rec(i + 1, False, gain + hard[i])

    rec(0, True, 0)
    return best


def _gain_of_schedule(
    schedule: tuple[WeekTask, ...], easy: list[int], hard: list[int]
) -> int:
    total = 0
    for i, task in enumerate(schedule):
        if task is WeekTask.EASY:
            total += easy[i]
        elif task is WeekTask.HARD:
            total += hard[i]
    return total


def _schedule_is_valid(schedule: tuple[WeekTask, ...]) -> bool:
    """Chaque HARD doit être précédé d'un REST (ou être en semaine 1)."""
    for i, task in enumerate(schedule):
        if task is WeekTask.HARD and i >= 1 and schedule[i - 1] is not WeekTask.REST:
            return False
    return True


# ---------------------------------------------------------------------------
# Cas limites
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_empty(self) -> None:
        result = solve_schedule([], [])
        assert result.total_gain == 0
        assert result.schedule == ()

    def test_single_week_easy_better(self) -> None:
        result = solve_schedule([10], [5])
        assert result.total_gain == 10
        assert result.schedule == (WeekTask.EASY,)

    def test_single_week_hard_better(self) -> None:
        result = solve_schedule([5], [10])
        assert result.total_gain == 10
        assert result.schedule == (WeekTask.HARD,)

    def test_zero_profits(self) -> None:
        result = solve_schedule([0, 0, 0], [0, 0, 0])
        assert result.total_gain == 0
        assert len(result.schedule) == 3

    def test_mismatched_lengths_raise(self) -> None:
        with pytest.raises(ValueError):
            Problem.from_sequences([1, 2], [1])


# ---------------------------------------------------------------------------
# Cas classiques
# ---------------------------------------------------------------------------


class TestClassicExamples:
    def test_subject_example(self) -> None:
        """Exemple canonique : repos / difficile / repos / difficile."""
        result = solve_schedule([10, 1, 10, 1], [5, 50, 5, 50])
        assert result.total_gain == 100
        assert result.schedule == (
            WeekTask.REST,
            WeekTask.HARD,
            WeekTask.REST,
            WeekTask.HARD,
        )

    def test_all_easy_dominates(self) -> None:
        """Quatre faciles (40) battent deux difficiles avec repos (24)."""
        result = solve_schedule([10, 10, 10, 10], [5, 12, 5, 12])
        assert result.total_gain == 40
        assert all(t is WeekTask.EASY for t in result.schedule)

    def test_two_weeks_hard_then_easy(self) -> None:
        # HARD en semaine 1 (pas de repos requis) puis EASY en semaine 2.
        result = solve_schedule([1, 1], [100, 1])
        assert result.total_gain == 101
        assert result.schedule == (WeekTask.HARD, WeekTask.EASY)

    def test_hard_requires_rest_constraint(self) -> None:
        # Deux difficiles consécutifs interdits : il faut un repos entre.
        result = solve_schedule([0, 0, 0], [100, 100, 100])
        assert result.total_gain == 200
        assert result.schedule == (WeekTask.HARD, WeekTask.REST, WeekTask.HARD)


# ---------------------------------------------------------------------------
# Cohérence planning <-> gain renvoyé
# ---------------------------------------------------------------------------


class TestConsistency:
    @given(
        easy=st.lists(st.integers(min_value=0, max_value=100), min_size=0, max_size=15),
    )
    def test_schedule_sum_matches_total_gain(self, easy: list[int]) -> None:
        hard = [2 * x + 3 for x in easy]
        result = solve_schedule(easy, hard)
        assert _gain_of_schedule(result.schedule, easy, hard) == result.total_gain

    @given(
        easy=st.lists(st.integers(min_value=0, max_value=100), min_size=0, max_size=15),
    )
    def test_schedule_is_feasible(self, easy: list[int]) -> None:
        hard = [3 * x + 1 for x in easy]
        result = solve_schedule(easy, hard)
        assert _schedule_is_valid(result.schedule)


# ---------------------------------------------------------------------------
# Property-based vs brute-force
# ---------------------------------------------------------------------------


class TestAgainstBruteForce:
    @given(data=st.data())
    def test_matches_brute_force(self, data: st.DataObject) -> None:
        n = data.draw(st.integers(min_value=0, max_value=8))
        easy = data.draw(st.lists(st.integers(0, 50), min_size=n, max_size=n))
        hard = data.draw(st.lists(st.integers(0, 100), min_size=n, max_size=n))
        expected = _brute_force_max_gain(easy, hard)
        result = solve_schedule(easy, hard)
        assert result.total_gain == expected
        assert _schedule_is_valid(result.schedule)
        assert _gain_of_schedule(result.schedule, easy, hard) == expected


# ---------------------------------------------------------------------------
# Instance large (non-régression perf + cohérence)
# ---------------------------------------------------------------------------


class TestLargeInstance:
    def test_one_thousand_weeks(self) -> None:
        rng = random.Random(42)
        n = 1000
        easy = [rng.randint(0, 100) for _ in range(n)]
        hard = [rng.randint(0, 300) for _ in range(n)]
        result = solve_schedule(easy, hard)
        assert result.n == n
        assert _schedule_is_valid(result.schedule)
        assert _gain_of_schedule(result.schedule, easy, hard) == result.total_gain


# ---------------------------------------------------------------------------
# API orientée objet
# ---------------------------------------------------------------------------


class TestSolveWithProblem:
    def test_solve_accepts_problem_directly(self) -> None:
        p = Problem.from_sequences([10, 1, 10, 1], [5, 50, 5, 50])
        result = solve(p)
        assert result.total_gain == 100
