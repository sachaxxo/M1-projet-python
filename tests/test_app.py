"""Tests des helpers de l'interface graphique Streamlit.

Ces tests sont automatiquement ignorés si l'extra ``[gui]`` n'est pas
installé (streamlit / pandas / altair absents). Ils n'exercent pas les
fonctions ``_render_*`` qui exigent un vrai runtime Streamlit (ces
dernières sont marquées ``# pragma: no cover``).
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

# Skip propre si la GUI n'est pas installée.
pd = pytest.importorskip("pandas")
pytest.importorskip("streamlit")
alt = pytest.importorskip("altair")

from consulting_scheduler import WeekTask  # noqa: E402
from consulting_scheduler.app import (  # noqa: E402
    EASY_COL,
    EASY_DEFAULT,
    HARD_COL,
    HARD_DEFAULT,
    _build_problem_from_table,
    _clear_all,
    _color_action_cell,
    _cumulative_gain_chart,
    _default_table,
    _gain_for_week,
    _init_session_state,
    _parse_csv_ints,
    _profits_chart,
    _reset_to_example,
    _result_dataframe,
)
from consulting_scheduler.models import Problem  # noqa: E402

# ---------------------------------------------------------------------------
# Parsing CSV
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Tableau éditable -> Problem
# ---------------------------------------------------------------------------


class TestBuildProblemFromTable:
    def test_basic_round_trip(self) -> None:
        df = pd.DataFrame({EASY_COL: [10, 1, 10, 10], HARD_COL: [5, 50, 5, 50]})
        problem = _build_problem_from_table(df)
        assert problem.easy == (10, 1, 10, 10)
        assert problem.hard == (5, 50, 5, 50)

    def test_drops_fully_empty_rows(self) -> None:
        df = pd.DataFrame({EASY_COL: [10, None, 5], HARD_COL: [5, None, 8]})
        problem = _build_problem_from_table(df)
        assert problem.n == 2
        assert problem.easy == (10, 5)

    def test_partial_nan_filled_with_zero(self) -> None:
        df = pd.DataFrame({EASY_COL: [10, None], HARD_COL: [5, 7]})
        problem = _build_problem_from_table(df)
        assert problem.n == 2
        assert problem.easy == (10, 0)
        assert problem.hard == (5, 7)

    def test_default_table_matches_canonical_example(self) -> None:
        df = _default_table()
        assert list(df[EASY_COL]) == EASY_DEFAULT
        assert list(df[HARD_COL]) == HARD_DEFAULT


# ---------------------------------------------------------------------------
# DataFrame des résultats
# ---------------------------------------------------------------------------


class TestResultDataframe:
    def test_columns_and_gains(self) -> None:
        problem = Problem.from_sequences([10, 1, 10, 1], [5, 50, 5, 50])
        schedule = (WeekTask.REST, WeekTask.HARD, WeekTask.REST, WeekTask.HARD)
        df = _result_dataframe(problem, schedule)
        assert list(df["Gain retenu (€)"]) == [0, 50, 0, 50]
        assert df.shape == (4, 5)


# ---------------------------------------------------------------------------
# Gain par semaine
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Style pandas pour la colonne « Action »
# ---------------------------------------------------------------------------


class TestColorAction:
    def test_easy_is_green(self) -> None:
        assert "22c55e" in _color_action_cell("🟢 facile")

    def test_hard_is_orange(self) -> None:
        assert "f59e0b" in _color_action_cell("🟡 difficile")

    def test_rest_is_grey(self) -> None:
        assert "94a3b8" in _color_action_cell("💤 repos")

    def test_unknown_value_returns_empty_style(self) -> None:
        assert _color_action_cell("???") == ""

    def test_accepts_non_string_input(self) -> None:
        # _color_action_cell est appelé par pandas Styler avec des cellules
        # de type arbitraire ; il doit accepter autre chose qu'une str.
        assert _color_action_cell(123) == ""


# ---------------------------------------------------------------------------
# Graphiques altair
# ---------------------------------------------------------------------------


class TestProfitsChart:
    def test_returns_altair_chart(self) -> None:
        p = Problem.from_sequences([10, 1, 10, 10], [5, 50, 5, 50])
        schedule = (WeekTask.REST, WeekTask.HARD, WeekTask.REST, WeekTask.HARD)
        chart = _profits_chart(p, schedule)
        assert isinstance(chart, alt.Chart)
        # 4 semaines × 2 types (facile/difficile) = 8 enregistrements
        assert len(chart.data) == 8
        # Chaque semaine apparaît deux fois (une par type).
        assert sorted(chart.data["Semaine"].tolist()) == [1, 1, 2, 2, 3, 3, 4, 4]


class TestCumulativeGainChart:
    def test_returns_altair_chart_with_monotonic_data(self) -> None:
        p = Problem.from_sequences([10, 1, 10, 10], [5, 50, 5, 50])
        schedule = (WeekTask.REST, WeekTask.HARD, WeekTask.REST, WeekTask.HARD)
        chart = _cumulative_gain_chart(p, schedule)
        assert isinstance(chart, alt.Chart)
        gains = chart.data["Gain cumulé (€)"].tolist()
        # Strictement croissant ou stable.
        assert gains == sorted(gains)
        # Dernière valeur = gain total optimal = 100.
        assert gains[-1] == 100


# ---------------------------------------------------------------------------
# session_state : utilise un dict mocké à la place de st.session_state
# ---------------------------------------------------------------------------


class FakeSessionState(dict):  # type: ignore[type-arg]
    """Mime st.session_state : accès par attribut ET par clé."""

    def __getattr__(self, name: str):  # type: ignore[no-untyped-def]
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name, value):  # type: ignore[no-untyped-def]
        self[name] = value


@pytest.fixture
def fake_state():  # type: ignore[no-untyped-def]
    state = FakeSessionState()
    with patch("consulting_scheduler.app.st") as mock_st:
        mock_st.session_state = state
        yield state


class TestSessionStateHelpers:
    def test_init_session_state_sets_defaults(self, fake_state) -> None:  # type: ignore[no-untyped-def]
        _init_session_state()
        assert fake_state["easy_csv"] == "10,1,10,10"
        assert fake_state["hard_csv"] == "5,50,5,50"
        assert fake_state["problem"] is None
        assert fake_state["error"] is None
        assert isinstance(fake_state["table"], pd.DataFrame)

    def test_init_session_state_preserves_existing(self, fake_state) -> None:  # type: ignore[no-untyped-def]
        fake_state["easy_csv"] = "preserved"
        _init_session_state()
        assert fake_state["easy_csv"] == "preserved"

    def test_reset_to_example(self, fake_state) -> None:  # type: ignore[no-untyped-def]
        fake_state["easy_csv"] = "junk"
        fake_state["hard_csv"] = "junk"
        fake_state["problem"] = "stale"
        fake_state["error"] = "stale"
        _reset_to_example()
        assert fake_state["easy_csv"] == "10,1,10,10"
        assert fake_state["hard_csv"] == "5,50,5,50"
        assert fake_state["problem"] is None
        assert fake_state["error"] is None
        assert list(fake_state["table"][EASY_COL]) == EASY_DEFAULT

    def test_clear_all(self, fake_state) -> None:  # type: ignore[no-untyped-def]
        fake_state["easy_csv"] = "1,2"
        fake_state["hard_csv"] = "3,4"
        fake_state["problem"] = "stale"
        fake_state["error"] = "stale"
        _clear_all()
        assert fake_state["easy_csv"] == ""
        assert fake_state["hard_csv"] == ""
        assert fake_state["problem"] is None
        assert fake_state["error"] is None
        assert fake_state["table"].empty
        assert list(fake_state["table"].columns) == [EASY_COL, HARD_COL]
