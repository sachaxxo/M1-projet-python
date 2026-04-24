"""Tests des helpers de l'interface graphique Streamlit.

Ces tests sont automatiquement ignorés si l'extra ``[gui]`` n'est pas
installé (streamlit / pandas / altair absents).
"""

from __future__ import annotations

import pytest

# Skip propre si la GUI n'est pas installée.
pd = pytest.importorskip("pandas")
pytest.importorskip("streamlit")
pytest.importorskip("altair")

from consulting_scheduler import WeekTask  # noqa: E402
from consulting_scheduler.app import (  # noqa: E402
    EASY_COL,
    HARD_COL,
    _build_problem_from_table,
    _color_action_cell,
    _gain_for_week,
    _parse_csv_ints,
    _result_dataframe,
)
from consulting_scheduler.models import Problem  # noqa: E402


class TestParseCsv:
    def test_parses_clean_csv(self) -> None:
        assert _parse_csv_ints("1,2,3") == [1, 2, 3]

    def test_handles_spaces_and_trailing_commas(self) -> None:
        assert _parse_csv_ints(" 1 , 2,  3, ") == [1, 2, 3]

    def test_empty_string_returns_empty_list(self) -> None:
        assert _parse_csv_ints("") == []

    def test_invalid_raises(self) -> None:
        with pytest.raises(ValueError):
            _parse_csv_ints("1,abc,3")


class TestBuildProblemFromTable:
    def test_basic_round_trip(self) -> None:
        df = pd.DataFrame(
            {
                EASY_COL: [10, 1, 10, 10],
                HARD_COL: [5, 50, 5, 50],
            }
        )
        problem = _build_problem_from_table(df)
        assert problem.easy == (10, 1, 10, 10)
        assert problem.hard == (5, 50, 5, 50)

    def test_drops_fully_empty_rows(self) -> None:
        df = pd.DataFrame(
            {
                EASY_COL: [10, None, 5],
                HARD_COL: [5, None, 8],
            }
        )
        problem = _build_problem_from_table(df)
        assert problem.n == 2
        assert problem.easy == (10, 5)


class TestResultDataframe:
    def test_columns_and_gains(self) -> None:
        problem = Problem.from_sequences([10, 1, 10, 1], [5, 50, 5, 50])
        schedule = (WeekTask.REST, WeekTask.HARD, WeekTask.REST, WeekTask.HARD)
        df = _result_dataframe(problem, schedule)
        assert list(df["Gain retenu (€)"]) == [0, 50, 0, 50]
        assert df.shape == (4, 5)


class TestGainForWeek:
    def test_easy_uses_l_i(self) -> None:
        p = Problem.from_sequences([10, 20], [99, 99])
        assert _gain_for_week(p, 1, WeekTask.EASY) == 10

    def test_hard_uses_h_i(self) -> None:
        p = Problem.from_sequences([10, 20], [99, 88])
        assert _gain_for_week(p, 2, WeekTask.HARD) == 88

    def test_rest_is_zero(self) -> None:
        p = Problem.from_sequences([10, 20], [99, 88])
        assert _gain_for_week(p, 1, WeekTask.REST) == 0


class TestColorAction:
    def test_easy_is_green(self) -> None:
        assert "22c55e" in _color_action_cell("🟢 facile")

    def test_hard_is_orange(self) -> None:
        assert "f59e0b" in _color_action_cell("🟡 difficile")

    def test_rest_is_grey(self) -> None:
        assert "94a3b8" in _color_action_cell("💤 repos")
