"""Audited theory and evidence utilities for SP4."""

from .theory import (
    closed_loop_energy_derivative,
    dissipation_upper_bound,
    pairwise_game_gradient,
    pairwise_game_hessian,
    pairwise_game_potential,
)

__all__ = [
    "closed_loop_energy_derivative",
    "dissipation_upper_bound",
    "pairwise_game_gradient",
    "pairwise_game_hessian",
    "pairwise_game_potential",
]
