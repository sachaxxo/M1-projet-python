"""Types de données pour le problème d'affectation hebdomadaire.

Ce module définit l'ensemble des structures de données immuables utilisées
par le solveur : l'énumération des actions possibles sur une semaine, la
classe ``Problem`` qui encode une instance, et ``ScheduleResult`` qui
encode la sortie du solveur.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum


class WeekTask(str, Enum):  # noqa: UP042
    """Action réalisable durant une semaine.

    Hériter de str et Enum donne la comparaison naturelle avec une
    chaîne (WeekTask.EASY == "facile") tout en gardant la sécurité
    d'un Enum. (Python 3.11+ permet d'utiliser StrEnum directement
    pour le même résultat.)
    """

    EASY = "facile"
    HARD = "difficile"
    REST = "repos"


@dataclass(frozen=True, slots=True)
class Problem:
    """Instance du problème : profits faciles et difficiles pour n semaines.

    Attributes:
        easy:  Tuple des profits ``l_i`` pour un travail facile.
        hard:  Tuple des profits ``h_i`` pour un travail difficile.

    Raises:
        ValueError: si ``easy`` et ``hard`` n'ont pas la même longueur.
    """

    easy: tuple[int, ...]
    hard: tuple[int, ...]

    def __post_init__(self) -> None:
        """Valide la cohérence des champs à la construction."""
        if len(self.easy) != len(self.hard):
            raise ValueError(
                "easy et hard doivent avoir la même longueur "
                f"(easy={len(self.easy)}, hard={len(self.hard)})"
            )

    @property
    def n(self) -> int:
        """Nombre de semaines."""
        return len(self.easy)

    @classmethod
    def from_sequences(cls, easy: Sequence[int], hard: Sequence[int]) -> Problem:
        """Construit un :class:`Problem` à partir de deux séquences quelconques."""
        return cls(tuple(easy), tuple(hard))


@dataclass(frozen=True, slots=True)
class ScheduleResult:
    """Résultat du solveur : gain optimal + planning semaine par semaine.

    Attributes:
        total_gain:  Somme des profits des semaines où on travaille.
        schedule:    Tuple de :class:`WeekTask` de longueur ``n``.
    """

    total_gain: int
    schedule: tuple[WeekTask, ...]

    @property
    def n(self) -> int:
        """Nombre de semaines planifiées."""
        return len(self.schedule)

    def pretty(self) -> str:
        """Retourne une représentation lisible du résultat."""
        lines = [f"Gain optimal : {self.total_gain}", "Planning :"]
        lines.extend(
            f"  Semaine {i} : {task.value}"
            for i, task in enumerate(self.schedule, start=1)
        )
        return "\n".join(lines)
