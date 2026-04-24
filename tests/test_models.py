"""Tests des structures de données."""

from __future__ import annotations

import pytest

from consulting_scheduler import Problem, ScheduleResult, WeekTask


class TestProblem:
    def test_from_sequences_builds_tuples(self) -> None:
        p = Problem.from_sequences([1, 2, 3], [4, 5, 6])
        assert p.easy == (1, 2, 3)
        assert p.hard == (4, 5, 6)
        assert p.n == 3

    def test_empty_problem_is_valid(self) -> None:
        p = Problem.from_sequences([], [])
        assert p.n == 0

    def test_mismatched_lengths_raise(self) -> None:
        with pytest.raises(ValueError, match="même longueur"):
            Problem.from_sequences([1, 2], [1])

    def test_problem_is_immutable(self) -> None:
        p = Problem.from_sequences([1], [2])
        with pytest.raises(Exception):  # noqa: B017 — FrozenInstanceError est OK
            p.easy = (9,)  # type: ignore[misc]


class TestScheduleResult:
    def test_pretty_output(self) -> None:
        r = ScheduleResult(
            total_gain=100,
            schedule=(WeekTask.REST, WeekTask.HARD, WeekTask.REST, WeekTask.HARD),
        )
        out = r.pretty()
        assert "Gain optimal : 100" in out
        assert "Semaine 1 : repos" in out
        assert "Semaine 2 : difficile" in out
        assert r.n == 4

    def test_week_task_is_string_comparable(self) -> None:
        # Héritage de str : doit être comparable comme une chaîne.
        assert WeekTask.EASY == "facile"
        assert WeekTask.HARD.value == "difficile"
