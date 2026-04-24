"""Interface en ligne de commande pour le solveur.

Exemples :

.. code-block:: bash

    consulting-scheduler solve --easy 10,1,10,10 --hard 5,50,5,50
    consulting-scheduler example
    consulting-scheduler gui              # ouvre l'interface Streamlit
"""

from __future__ import annotations

import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from consulting_scheduler import __version__
from consulting_scheduler.models import WeekTask
from consulting_scheduler.solver import solve_schedule

app = typer.Typer(
    name="consulting-scheduler",
    help="Résolution optimale d'un problème d'affectation hebdomadaire.",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()


def _parse_csv_ints(value: str, name: str) -> list[int]:
    """Parse une chaîne ``"1,2,3"`` en liste d'entiers."""
    try:
        return [int(x.strip()) for x in value.split(",") if x.strip()]
    except ValueError as exc:
        raise typer.BadParameter(
            f"--{name} : attendu une liste d'entiers séparés par des virgules."
        ) from exc


def _version_callback(show: bool) -> None:
    if show:
        console.print(f"consulting-scheduler {__version__}")
        raise typer.Exit()


@app.callback()
def _root(
    _version: bool = typer.Option(  # noqa: B008
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Affiche la version et quitte.",
    ),
) -> None:
    """Point d'entrée racine (utilisé pour l'option ``--version``)."""


@app.command()
def solve(
    easy: str = typer.Option(  # noqa: B008
        ...,
        "--easy",
        "-e",
        help="Profits faciles, séparés par des virgules. Ex: 10,1,10,10",
    ),
    hard: str = typer.Option(  # noqa: B008
        ...,
        "--hard",
        "-H",
        help="Profits difficiles, séparés par des virgules. Ex: 5,50,5,50",
    ),
) -> None:
    """Résout une instance du problème et affiche le planning optimal."""
    easy_profits = _parse_csv_ints(easy, "easy")
    hard_profits = _parse_csv_ints(hard, "hard")

    if len(easy_profits) != len(hard_profits):
        console.print(
            "[bold red]Erreur[/bold red] : --easy et --hard doivent avoir "
            "le même nombre d'éléments "
            f"(reçu easy={len(easy_profits)}, hard={len(hard_profits)})."
        )
        raise typer.Exit(code=1)

    if not easy_profits:
        console.print("[yellow]Aucune semaine fournie : gain = 0.[/yellow]")
        raise typer.Exit(code=0)

    result = solve_schedule(easy_profits, hard_profits)

    # Panel récapitulatif
    console.print(
        Panel.fit(
            f"[bold green]{result.total_gain} €[/bold green]",
            title="Gain optimal",
            border_style="green",
        )
    )

    # Table du planning
    table = Table(title="Planning optimal", show_lines=False)
    table.add_column("Semaine", justify="right", style="cyan", no_wrap=True)
    table.add_column("Action", style="magenta")
    table.add_column("Gain (€)", justify="right", style="green")

    style_for = {
        WeekTask.EASY: "green",
        WeekTask.HARD: "bold yellow",
        WeekTask.REST: "dim",
    }

    for i, task in enumerate(result.schedule, start=1):
        if task is WeekTask.EASY:
            gain = easy_profits[i - 1]
        elif task is WeekTask.HARD:
            gain = hard_profits[i - 1]
        else:
            gain = 0
        table.add_row(
            str(i),
            f"[{style_for[task]}]{task.value}[/{style_for[task]}]",
            str(gain),
        )

    console.print(table)


@app.command()
def example() -> None:
    """Exécute l'exemple classique ``l=[10,1,10,10]``, ``h=[5,50,5,50]``."""
    easy_profits = [10, 1, 10, 10]
    hard_profits = [5, 50, 5, 50]
    console.print(f"[cyan]Exemple :[/cyan] easy={easy_profits}, hard={hard_profits}")
    result = solve_schedule(easy_profits, hard_profits)
    console.print(result.pretty())


def _silence_streamlit_first_run() -> None:
    """Évite le prompt email du premier lancement et coupe la télémétrie.

    Streamlit demande une adresse e-mail au tout premier lancement si
    ``~/.streamlit/credentials.toml`` n'existe pas. On crée un fichier
    minimal vide pour qu'il considère l'utilisateur comme « déjà accueilli ».
    """
    creds_dir = Path.home() / ".streamlit"
    creds_file = creds_dir / "credentials.toml"
    if not creds_file.exists():
        creds_dir.mkdir(parents=True, exist_ok=True)
        creds_file.write_text('[general]\nemail = ""\n', encoding="utf-8")


def run_gui() -> None:  # pragma: no cover
    """Lance l'interface graphique Streamlit ``consulting_scheduler.app``.

    Utilisable comme script (``consulting-scheduler-gui``) ou via la
    sous-commande ``consulting-scheduler gui``.
    """
    try:
        from streamlit.web import cli as stcli
    except ImportError as exc:  # extra [gui] non installé
        console.print(
            "[bold red]Streamlit n'est pas installé.[/bold red]\n"
            "Installe l'extra GUI :\n"
            "  [cyan]uv sync --extra gui[/cyan]   ou   "
            "[cyan]pip install -e \".[gui]\"[/cyan]"
        )
        raise typer.Exit(code=1) from exc

    _silence_streamlit_first_run()

    app_path = Path(__file__).with_name("app.py")
    sys.argv = [
        "streamlit",
        "run",
        str(app_path),
        "--browser.gatherUsageStats=false",
    ]
    sys.exit(stcli.main())


@app.command()
def gui() -> None:
    """Ouvre l'interface graphique Streamlit (saisie CSV ou tableau)."""
    run_gui()


def main() -> None:  # pragma: no cover
    """Entrée utilisée par le script ``consulting-scheduler``."""
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
