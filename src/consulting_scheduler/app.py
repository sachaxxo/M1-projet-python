"""Interface graphique Streamlit pour ``consulting-scheduler``.

Le module définit une application Streamlit autonome offrant deux modes de
saisie (CSV rapide ou tableau éditable), résout l'instance avec le même
solveur DP que la CLI et affiche le planning optimal de manière visuelle.

Lancement :

.. code-block:: bash

    consulting-scheduler gui            # via la CLI Typer
    consulting-scheduler-gui            # script dédié
    streamlit run src/consulting_scheduler/app.py
"""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from consulting_scheduler import __version__
from consulting_scheduler.models import Problem, WeekTask
from consulting_scheduler.solver import solve

# ---------------------------------------------------------------------------
# Constantes & helpers
# ---------------------------------------------------------------------------

EASY_DEFAULT: list[int] = [10, 1, 10, 10]
HARD_DEFAULT: list[int] = [5, 50, 5, 50]

TASK_COLOR: dict[WeekTask, str] = {
    WeekTask.EASY: "#22c55e",   # vert
    WeekTask.HARD: "#f59e0b",   # orange
    WeekTask.REST: "#94a3b8",   # gris
}
TASK_EMOJI: dict[WeekTask, str] = {
    WeekTask.EASY: "🟢",
    WeekTask.HARD: "🟡",
    WeekTask.REST: "💤",
}

EASY_COL = "Profit facile (l_i)"
HARD_COL = "Profit difficile (h_i)"


def _parse_csv_ints(value: str) -> list[int]:
    """Parse ``"1, 2, 3"`` en ``[1, 2, 3]``. Lève ``ValueError`` au besoin."""
    return [int(x.strip()) for x in value.split(",") if x.strip()]


def _default_table() -> pd.DataFrame:
    """Tableau initial (exemple canonique du sujet)."""
    return pd.DataFrame(
        {
            EASY_COL: EASY_DEFAULT,
            HARD_COL: HARD_DEFAULT,
        }
    )


def _build_problem_from_table(df: pd.DataFrame) -> Problem:
    """Convertit le DataFrame éditable en :class:`Problem`."""
    cleaned = df.dropna(how="all").fillna(0)
    easy = [int(x) for x in cleaned[EASY_COL].tolist()]
    hard = [int(x) for x in cleaned[HARD_COL].tolist()]
    return Problem.from_sequences(easy, hard)


def _gain_for_week(problem: Problem, i: int, task: WeekTask) -> int:
    """Profit retenu pour la semaine ``i`` (1-based) selon l'action."""
    if task is WeekTask.EASY:
        return problem.easy[i - 1]
    if task is WeekTask.HARD:
        return problem.hard[i - 1]
    return 0


def _result_dataframe(
    problem: Problem, schedule: tuple[WeekTask, ...]
) -> pd.DataFrame:
    """Tableau récapitulatif : semaine / action / profits / gain retenu."""
    rows = [
        {
            "Semaine": i,
            "Action": f"{TASK_EMOJI[task]} {task.value}",
            EASY_COL: problem.easy[i - 1],
            HARD_COL: problem.hard[i - 1],
            "Gain retenu (€)": _gain_for_week(problem, i, task),
        }
        for i, task in enumerate(schedule, start=1)
    ]
    return pd.DataFrame(rows)


def _color_action_cell(value: str) -> str:
    """Style pandas pour la colonne « Action » (badge coloré)."""
    for task in WeekTask:
        if task.value in value:
            color = TASK_COLOR[task]
            return f"background-color: {color}; color: white; font-weight: 600;"
    return ""


def _profits_chart(problem: Problem, schedule: tuple[WeekTask, ...]) -> alt.Chart:
    """Barres groupées facile/difficile, l'action retenue est mise en avant."""
    records: list[dict[str, object]] = []
    for i, (e, h, task) in enumerate(
        zip(problem.easy, problem.hard, schedule, strict=True), start=1
    ):
        records.append(
            {
                "Semaine": i,
                "Type": "facile",
                "Profit": e,
                "Retenu": task is WeekTask.EASY,
            }
        )
        records.append(
            {
                "Semaine": i,
                "Type": "difficile",
                "Profit": h,
                "Retenu": task is WeekTask.HARD,
            }
        )
    df = pd.DataFrame(records)

    return (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("Semaine:O", title="Semaine"),
            xOffset="Type:N",
            y=alt.Y("Profit:Q", title="Profit (€)"),
            color=alt.Color(
                "Type:N",
                scale=alt.Scale(
                    domain=["facile", "difficile"],
                    range=[TASK_COLOR[WeekTask.EASY], TASK_COLOR[WeekTask.HARD]],
                ),
                legend=alt.Legend(title="Type de travail"),
            ),
            opacity=alt.condition(
                alt.datum.Retenu, alt.value(1.0), alt.value(0.25)
            ),
            tooltip=[
                alt.Tooltip("Semaine:O"),
                alt.Tooltip("Type:N"),
                alt.Tooltip("Profit:Q", format="d"),
                alt.Tooltip("Retenu:N", title="Action retenue"),
            ],
        )
        .properties(height=320)
    )


def _cumulative_gain_chart(
    problem: Problem, schedule: tuple[WeekTask, ...]
) -> alt.Chart:
    """Aire du gain cumulé semaine après semaine."""
    cumul: list[int] = []
    running = 0
    for i, task in enumerate(schedule, start=1):
        running += _gain_for_week(problem, i, task)
        cumul.append(running)
    df = pd.DataFrame({"Semaine": range(1, problem.n + 1), "Gain cumulé (€)": cumul})
    return (
        alt.Chart(df)
        .mark_area(line=True, opacity=0.35, color="#22c55e")
        .encode(
            x=alt.X("Semaine:O", title="Semaine"),
            y=alt.Y("Gain cumulé (€):Q"),
            tooltip=["Semaine", "Gain cumulé (€)"],
        )
        .properties(height=240)
    )


# ---------------------------------------------------------------------------
# Initialisation du session_state
# ---------------------------------------------------------------------------


def _init_session_state() -> None:
    """Crée les clés persistées si elles n'existent pas encore."""
    defaults = {
        "easy_csv": ",".join(str(x) for x in EASY_DEFAULT),
        "hard_csv": ",".join(str(x) for x in HARD_DEFAULT),
        "table": _default_table(),
        "problem": None,
        "error": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _reset_to_example() -> None:
    st.session_state.easy_csv = ",".join(str(x) for x in EASY_DEFAULT)
    st.session_state.hard_csv = ",".join(str(x) for x in HARD_DEFAULT)
    st.session_state.table = _default_table()
    st.session_state.problem = None
    st.session_state.error = None


def _clear_all() -> None:
    st.session_state.easy_csv = ""
    st.session_state.hard_csv = ""
    st.session_state.table = pd.DataFrame(
        {EASY_COL: pd.Series(dtype=int), HARD_COL: pd.Series(dtype=int)}
    )
    st.session_state.problem = None
    st.session_state.error = None


# ---------------------------------------------------------------------------
# Rendus
# ---------------------------------------------------------------------------


def _render_sidebar() -> None:
    with st.sidebar:
        st.title("📅 Consulting Scheduler")
        st.caption(f"v{__version__} — Sujet 06 (DP)")
        st.markdown(
            "Maximise le gain hebdomadaire d'une équipe de consultants.\n\n"
            "Chaque semaine, choisir entre :"
        )
        st.markdown(
            "- 🟢 **facile** — rapporte `l_i`\n"
            "- 🟡 **difficile** — rapporte `h_i`, "
            "exige un repos en *i − 1*\n"
            "- 💤 **repos** — gain nul"
        )
        st.divider()
        st.markdown("### Actions rapides")
        if st.button("📦 Charger l'exemple", use_container_width=True):
            _reset_to_example()
            st.rerun()
        if st.button("🗑 Tout effacer", use_container_width=True):
            _clear_all()
            st.rerun()
        st.divider()
        st.caption(
            "Solveur en O(n) — voir `docs/algorithm.md` pour la récurrence "
            "et la preuve de correction."
        )


def _render_csv_tab() -> None:
    col1, col2 = st.columns(2)
    with col1:
        st.text_input(
            f"Profits **faciles** ({EASY_COL.split('(')[1][:-1]})",
            key="easy_csv",
            help="Liste d'entiers séparés par des virgules. Ex : 10,1,10,10",
        )
    with col2:
        st.text_input(
            f"Profits **difficiles** ({HARD_COL.split('(')[1][:-1]})",
            key="hard_csv",
            help="Liste d'entiers séparés par des virgules. Ex : 5,50,5,50",
        )
    st.caption(
        "Astuce : `10,1,10,10` / `5,50,5,50` reproduit l'exemple canonique du sujet."
    )

    if st.button("▶ Résoudre depuis le CSV", type="primary", key="solve_csv"):
        try:
            easy = _parse_csv_ints(st.session_state.easy_csv)
            hard = _parse_csv_ints(st.session_state.hard_csv)
        except ValueError as exc:
            st.session_state.problem = None
            st.session_state.error = (
                f"Erreur de saisie : {exc}. Utilise des entiers séparés par des "
                "virgules."
            )
            return
        if len(easy) != len(hard):
            st.session_state.problem = None
            st.session_state.error = (
                f"Longueurs incohérentes : easy={len(easy)}, hard={len(hard)}."
            )
            return
        st.session_state.problem = Problem.from_sequences(easy, hard)
        st.session_state.error = None


def _render_table_tab() -> None:
    st.markdown(
        "Édite directement les profits, ajoute ou supprime des lignes "
        "avec le `+` en bas du tableau. Le numéro de ligne correspond au "
        "numéro de semaine."
    )
    edited = st.data_editor(
        st.session_state.table,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            EASY_COL: st.column_config.NumberColumn(
                EASY_COL,
                min_value=0,
                step=1,
                format="%d €",
                help="Profit obtenu pour un travail facile cette semaine.",
            ),
            HARD_COL: st.column_config.NumberColumn(
                HARD_COL,
                min_value=0,
                step=1,
                format="%d €",
                help="Profit obtenu pour un travail difficile (exige repos en i-1).",
            ),
        },
        key="table_editor",
    )
    st.session_state.table = edited

    if st.button("▶ Résoudre depuis le tableau", type="primary", key="solve_table"):
        try:
            problem = _build_problem_from_table(edited)
        except (ValueError, TypeError) as exc:
            st.session_state.problem = None
            st.session_state.error = f"Erreur : {exc}"
            return
        st.session_state.problem = problem
        st.session_state.error = None


def _render_results(problem: Problem) -> None:
    if problem.n == 0:
        st.warning("Aucune semaine à planifier — gain optimal = 0 €.")
        return

    result = solve(problem)

    n_easy = sum(1 for t in result.schedule if t is WeekTask.EASY)
    n_hard = sum(1 for t in result.schedule if t is WeekTask.HARD)
    n_rest = sum(1 for t in result.schedule if t is WeekTask.REST)

    st.success(
        f"Planning optimal calculé pour {problem.n} semaine(s) — "
        f"gain total **{result.total_gain} €**."
    )

    cols = st.columns(4)
    cols[0].metric("💰 Gain optimal", f"{result.total_gain} €")
    cols[1].metric("🟢 Faciles", n_easy)
    cols[2].metric("🟡 Difficiles", n_hard)
    cols[3].metric("💤 Repos", n_rest)

    st.subheader("Planning optimal")
    df_result = _result_dataframe(problem, result.schedule)
    styled = df_result.style.map(_color_action_cell, subset=["Action"]).format(
        {EASY_COL: "{} €", HARD_COL: "{} €", "Gain retenu (€)": "{} €"}
    )
    st.dataframe(styled, use_container_width=True, hide_index=True)

    st.subheader("Profits par semaine")
    st.caption(
        "Les barres pleines correspondent à l'action retenue par le solveur "
        "(les autres sont estompées)."
    )
    st.altair_chart(
        _profits_chart(problem, result.schedule), use_container_width=True
    )

    st.subheader("Gain cumulé")
    st.altair_chart(
        _cumulative_gain_chart(problem, result.schedule), use_container_width=True
    )

    st.download_button(
        "⬇ Exporter le planning (CSV)",
        df_result.to_csv(index=False).encode("utf-8"),
        file_name="planning_optimal.csv",
        mime="text/csv",
    )


# ---------------------------------------------------------------------------
# Entrée Streamlit
# ---------------------------------------------------------------------------


def main() -> None:
    """Point d'entrée Streamlit (exécuté par ``streamlit run app.py``)."""
    st.set_page_config(
        page_title="Consulting Scheduler",
        page_icon="📅",
        layout="wide",
    )

    _init_session_state()
    _render_sidebar()

    st.title("Planificateur d'affectations hebdomadaires")
    st.write(
        "Saisis les profits faciles et difficiles pour chaque semaine, "
        "puis lance la résolution. Le solveur trouve le planning qui "
        "**maximise le gain total** sous la contrainte « difficile ⇒ repos "
        "en semaine précédente »."
    )

    tab_csv, tab_table = st.tabs(
        ["⚡ Saisie rapide (CSV)", "📋 Tableau éditable"]
    )
    with tab_csv:
        _render_csv_tab()
    with tab_table:
        _render_table_tab()

    if st.session_state.error:
        st.error(st.session_state.error)

    problem = st.session_state.problem
    if problem is not None:
        st.divider()
        _render_results(problem)


if __name__ == "__main__":  # pragma: no cover
    main()
