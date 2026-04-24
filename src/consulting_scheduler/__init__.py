"""Résolution optimale d'un problème d'affectation hebdomadaire."""

from consulting_scheduler.models import Problem, ScheduleResult, WeekTask
from consulting_scheduler.solver import solve, solve_schedule

__all__ = [
    "Problem",
    "ScheduleResult",
    "WeekTask",
    "solve",
    "solve_schedule",
]
__version__ = "0.1.0"
