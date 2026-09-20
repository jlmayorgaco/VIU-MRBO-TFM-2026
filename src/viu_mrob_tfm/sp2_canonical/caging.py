"""Resolution-complete escape check for the exploratory SP2-E branch."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class CagingResult:
    status: str
    escape_found: bool
    visited_cells: int
    path: tuple[tuple[int, int], ...]
    resolution_label: str


def verify_grid_caging(
    free_configuration: np.ndarray,
    start: tuple[int, int],
    *,
    resolution_label: str,
) -> CagingResult:
    """Search a 4-connected configuration grid for a path to its boundary."""

    free = np.asarray(free_configuration, dtype=bool)
    if free.ndim != 2:
        raise ValueError("free_configuration must be a 2-D boolean grid")
    row, column = map(int, start)
    if (
        not (0 <= row < free.shape[0] and 0 <= column < free.shape[1])
        or not free[row, column]
    ):
        return CagingResult(
            status="invalid_start",
            escape_found=False,
            visited_cells=0,
            path=(),
            resolution_label=resolution_label,
        )

    queue = deque([(row, column)])
    parent: dict[tuple[int, int], tuple[int, int] | None] = {
        (row, column): None
    }
    terminal: tuple[int, int] | None = None
    while queue:
        current = queue.popleft()
        if current[0] in {0, free.shape[0] - 1} or current[1] in {
            0,
            free.shape[1] - 1,
        }:
            terminal = current
            break
        for delta_row, delta_column in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            candidate = (current[0] + delta_row, current[1] + delta_column)
            if candidate in parent or not free[candidate]:
                continue
            parent[candidate] = current
            queue.append(candidate)

    if terminal is None:
        return CagingResult(
            status="no_escape_at_resolution",
            escape_found=False,
            visited_cells=len(parent),
            path=(),
            resolution_label=resolution_label,
        )

    reverse_path = []
    cursor: tuple[int, int] | None = terminal
    while cursor is not None:
        reverse_path.append(cursor)
        cursor = parent[cursor]
    return CagingResult(
        status="escape_found",
        escape_found=True,
        visited_cells=len(parent),
        path=tuple(reversed(reverse_path)),
        resolution_label=resolution_label,
    )


__all__ = ["CagingResult", "verify_grid_caging"]
