"""Cuatro plantas de tipo industrial para el banco hold-out de SP1.

Los cinco generadores de SP1 ---uniform, clustered, separated, ring, corridor---
se usaron para DESARROLLAR el metodo, de modo que todo lo que el capitulo afirma
sobre el orden de revision se ha medido sobre el mismo banco con el que se
diseno. Este modulo anade cuatro geometrias que no participaron en ese diseno.

El generador original (`scripts/sp1_a1_hungarian.generate_positions`) no se
modifica: estas plantas viven aparte y comparten unicamente el contrato de la
funcion ---(count, role, rng) -> array (count, 2)--- y el ORDEN DE EXTRACCION de
`sp1_n3.worlds.make_world`, que es lo que hace comparables los mundos: primero
las posiciones de los AMR, despues las de las cargas, despues el reparto de
Dirichlet; las capacidades salen de su propio flujo.

Las cuatro plantas se describen por su topologia, no por su aspecto:

cross_aisle
    Pasillos principales cruzados por transversales. La vecindad es una rejilla:
    hay muchos caminos alternativos entre dos puntos.
parallel_aisles
    Pasillos paralelos sin transversales. La vecindad es casi unidimensional
    dentro de cada pasillo y muy debil entre pasillos.
docks_staging
    Muelles en un borde y zona de preparacion enfrente. AMR y cargas ocupan
    bandas separadas, de modo que toda asignacion cruza el hueco.
open_bottleneck
    Dos areas abiertas unidas por un unico paso estrecho, con AMR y cargas
    repartidos de forma desigual e invertida entre ambas.
"""

from __future__ import annotations

import numpy as np

INDUSTRIAL_LAYOUTS = (
    "cross_aisle",
    "parallel_aisles",
    "docks_staging",
    "open_bottleneck",
)

LAYOUT_LABELS = {
    "cross_aisle": "Pasillos cruzados",
    "parallel_aisles": "Pasillos paralelos",
    "docks_staging": "Muelles y preparación",
    "open_bottleneck": "Áreas con paso estrecho",
}

# Parametros geometricos. Se declaran aqui y no se ajustan despues de mirar
# resultados: son descripciones de la planta, no grados de libertad del metodo.
CROSS_MAIN_AISLES = 3          # pasillos principales, verticales
CROSS_TRANSVERSALS = 3         # transversales, horizontales
CROSS_JITTER_FRAC = 0.018      # dispersion de la carga en la interseccion
PARALLEL_AISLES = 4
PARALLEL_HALF_WIDTH_FRAC = 0.035
DOCK_BAND_FRAC = 0.12          # ancho relativo de la banda de muelles
STAGING_BAND_FRAC = 0.16
BOTTLENECK_GAP_FRAC = 0.07     # media anchura del paso
BOTTLENECK_ROBOT_SPLIT = 0.70  # fraccion de AMR en el area izquierda
BOTTLENECK_LOAD_SPLIT = 0.30   # fraccion de cargas en el area izquierda


def _cross_aisle(count, role, w, h, rng):
    xs = np.linspace(w / (CROSS_MAIN_AISLES + 1), w * CROSS_MAIN_AISLES
                     / (CROSS_MAIN_AISLES + 1), CROSS_MAIN_AISLES)
    ys = np.linspace(h / (CROSS_TRANSVERSALS + 1), h * CROSS_TRANSVERSALS
                     / (CROSS_TRANSVERSALS + 1), CROSS_TRANSVERSALS)
    if role == "load":
        # Las cargas se depositan en las intersecciones, con jitter.
        ix = rng.integers(0, len(xs), size=count)
        iy = rng.integers(0, len(ys), size=count)
        pts = np.column_stack((xs[ix], ys[iy]))
        pts = pts + rng.normal(0.0, CROSS_JITTER_FRAC * max(w, h),
                               size=(count, 2))
    else:
        # Los AMR circulan por los pasillos: se elige pasillo y se recorre.
        vertical = rng.random(count) < 0.5
        pts = np.empty((count, 2), dtype=np.float64)
        n_v = int(vertical.sum())
        if n_v:
            pts[vertical, 0] = xs[rng.integers(0, len(xs), size=n_v)]
            pts[vertical, 1] = rng.uniform(0.0, h, size=n_v)
        n_hz = count - n_v
        if n_hz:
            pts[~vertical, 0] = rng.uniform(0.0, w, size=n_hz)
            pts[~vertical, 1] = ys[rng.integers(0, len(ys), size=n_hz)]
    return pts


def _parallel_aisles(count, role, w, h, rng):
    xs = np.linspace(w / (PARALLEL_AISLES + 1),
                     w * PARALLEL_AISLES / (PARALLEL_AISLES + 1),
                     PARALLEL_AISLES)
    idx = rng.integers(0, len(xs), size=count)
    half = PARALLEL_HALF_WIDTH_FRAC * w
    x = xs[idx] + rng.uniform(-half, half, size=count)
    y = rng.uniform(0.0, h, size=count)
    return np.column_stack((x, y))


def _docks_staging(count, role, w, h, rng):
    if role == "robot":
        y = rng.uniform(0.0, DOCK_BAND_FRAC * h, size=count)
    else:
        low = (1.0 - STAGING_BAND_FRAC) * h
        y = rng.uniform(low, h, size=count)
    x = rng.uniform(0.0, w, size=count)
    return np.column_stack((x, y))


def _open_bottleneck(count, role, w, h, rng):
    gap = BOTTLENECK_GAP_FRAC * h
    mid = w / 2.0
    share = BOTTLENECK_ROBOT_SPLIT if role == "robot" else BOTTLENECK_LOAD_SPLIT
    left = rng.random(count) < share
    pts = np.empty((count, 2), dtype=np.float64)
    n_left = int(left.sum())
    if n_left:
        pts[left, 0] = rng.uniform(0.0, mid - gap, size=n_left)
        pts[left, 1] = rng.uniform(0.0, h, size=n_left)
    n_right = count - n_left
    if n_right:
        pts[~left, 0] = rng.uniform(mid + gap, w, size=n_right)
        pts[~left, 1] = rng.uniform(0.0, h, size=n_right)
    return pts


_LAYOUTS = {
    "cross_aisle": _cross_aisle,
    "parallel_aisles": _parallel_aisles,
    "docks_staging": _docks_staging,
    "open_bottleneck": _open_bottleneck,
}


def generate_industrial_positions(
    count: int,
    *,
    role: str,
    layout: str,
    workspace_width: float,
    workspace_height: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Posiciones de una planta industrial, con el contrato del generador base."""

    if layout not in _LAYOUTS:
        raise KeyError("layout desconocido: %r" % layout)
    if role not in ("robot", "load"):
        raise ValueError("role debe ser 'robot' o 'load'")
    if count <= 0:
        return np.empty((0, 2), dtype=np.float64)
    pts = _LAYOUTS[layout](count, role, float(workspace_width),
                           float(workspace_height), rng)
    pts = np.asarray(pts, dtype=np.float64)
    pts[:, 0] = np.clip(pts[:, 0], 0.0, workspace_width)
    pts[:, 1] = np.clip(pts[:, 1], 0.0, workspace_height)
    return pts


__all__ = [
    "INDUSTRIAL_LAYOUTS",
    "LAYOUT_LABELS",
    "generate_industrial_positions",
]
