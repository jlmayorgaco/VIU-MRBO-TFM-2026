"""Estilo unico para las figuras finales de SP1.

Diseno sobrio para memoria impresa en A4 a 12 pt:
- una sola familia tipografica y una escala de tamanos coherente;
- sin degradados ni adornos;
- rotulos legibles al 100 % de zoom;
- salida vectorial PDF mas vista previa PNG;
- CSV fuente junto a cada figura.

No se codifica ningun valor medido en este modulo: todo procede del RAW.
"""
from __future__ import annotations

import csv
import hashlib
import os
import subprocess

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                    "..", "..", "..", ".."))
RAW = os.path.join(REPO, "scripts", "results", "sp1_levels")
FIGDIR = os.path.join(REPO, "Subdocuments", "SP1", "assets", "figures", "sp1-final")
CSVDIR = os.path.join(REPO, "Subdocuments", "SP1", "generated", "sp1-final")

# Paleta sobria: azul (referencia), naranja (propuesta), verde (oraculo),
# violeta (continuo), gris (control). Contraste suficiente en gris de imprenta.
C_BLUE = "#2F5D8C"
C_ORANGE = "#C4622D"
C_GREEN = "#2E7D5B"
C_PURPLE = "#6A4C93"
C_GRAY = "#6B6B6B"
C_RED = "#A62B2B"
SCEN_COLORS = {
    "uniform": C_BLUE,
    "clustered": C_ORANGE,
    "separated": C_GREEN,
    "ring": C_PURPLE,
    "corridor": C_GRAY,
}
SCEN_LABEL = {
    "uniform": "Aleatorio",
    "clustered": "Agrupado",
    "separated": "Separado",
    "ring": "Anillo",
    "corridor": "Pasillo",
}
SCEN_MARKER = {
    "uniform": "o",
    "clustered": "s",
    "separated": "^",
    "ring": "D",
    "corridor": "v",
}

BASE_FS = 9.0


def apply_style() -> None:
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans"],
        "font.size": BASE_FS,
        "axes.titlesize": BASE_FS + 0.5,
        "axes.labelsize": BASE_FS,
        "xtick.labelsize": BASE_FS - 0.5,
        "ytick.labelsize": BASE_FS - 0.5,
        "legend.fontsize": BASE_FS - 0.5,
        "figure.titlesize": BASE_FS + 1.5,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.7,
        "axes.edgecolor": "#444444",
        "axes.labelcolor": "#222222",
        "text.color": "#222222",
        "xtick.color": "#444444",
        "ytick.color": "#444444",
        "xtick.major.width": 0.7,
        "ytick.major.width": 0.7,
        "xtick.major.size": 3.0,
        "ytick.major.size": 3.0,
        "grid.color": "#D9D9D9",
        "grid.linewidth": 0.5,
        "legend.frameon": False,
        "lines.linewidth": 1.4,
        "lines.markersize": 5.0,
        "figure.dpi": 120,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })


def read_raw(rel: str) -> list[dict]:
    """Lee un CSV del arbol RAW congelado."""
    path = os.path.join(RAW, rel)
    with open(path, newline="", encoding="utf-8", errors="replace") as fh:
        return list(csv.DictReader(fh))


def fnum(value):
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    return v if v == v else None  # descarta NaN


def fbool(value) -> bool:
    return str(value).strip().lower() in ("true", "1", "yes")


def median(values):
    vs = sorted(v for v in values if v is not None)
    if not vs:
        return None
    n = len(vs)
    return vs[n // 2] if n % 2 else 0.5 * (vs[n // 2 - 1] + vs[n // 2])


def boot_ci(values, stat=median, n_boot=2000, alpha=0.05, seed=20260819):
    """IC por bootstrap de percentiles. Semilla fija: generacion determinista."""
    import random

    # El orden de entrada debe ser irrelevante: varias listas provienen de
    # iterar conjuntos de Python, cuyo orden depende de PYTHONHASHSEED. Sin
    # ordenar, el remuestreo por indice cambia entre ejecuciones y el IC baila.
    vs = sorted(v for v in values if v is not None)
    if len(vs) < 2:
        return (None, None)
    rng = random.Random(seed)
    n = len(vs)
    reps = []
    for _ in range(n_boot):
        reps.append(stat([vs[rng.randrange(n)] for _ in range(n)]))
    reps.sort()
    lo = reps[int((alpha / 2) * n_boot)]
    hi = reps[int((1 - alpha / 2) * n_boot) - 1]
    return (lo, hi)


def wilson_ci(k: int, n: int, z: float = 1.959963985):
    """IC de Wilson para una proporcion. Apropiado con k=0 o k=n."""
    if n == 0:
        return (None, None, None)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (p, max(0.0, centre - half), min(1.0, centre + half))


def _git_sha() -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                             cwd=REPO, capture_output=True, text=True, timeout=20)
        return out.stdout.strip() or "desconocido"
    except Exception:
        return "desconocido"


def _spanish_decimals(fig) -> None:
    """Sustituye el punto decimal por coma en todo el texto de la figura.

    Se ejecuta con el dibujo ya resuelto, de modo que las marcas automaticas de
    matplotlib ya tienen su texto definitivo. La sustitucion es puntual: solo el
    punto que separa dos digitos. Los identificadores del tipo N4.E7 o SP1.2 se
    dejan intactos.
    """

    import re as _re

    between_digits = _re.compile(r"(?<=\d)\.(?=\d)")
    identifier = _re.compile(r"[A-Za-z]\w*\.\d")

    def fix(text: str) -> str:
        if not text or "." not in text or identifier.search(text):
            return text
        return between_digits.sub(",", text)

    fig.canvas.draw()
    for ax in fig.get_axes():
        for axis in (ax.xaxis, ax.yaxis):
            labels = [t.get_text() for t in axis.get_ticklabels()]
            if any(fix(t) != t for t in labels):
                axis.set_ticks(axis.get_ticklocs())
                axis.set_ticklabels([fix(t) for t in labels])
        # Cada posicion de titulo se lee y se reescribe por separado: leer el
        # central y escribirlo a la izquierda borraba el que si existia.
        for loc in ("left", "center", "right"):
            current = ax.get_title(loc=loc)
            if current:
                ax.set_title(fix(current), loc=loc)
        ax.set_xlabel(fix(ax.get_xlabel()))
        ax.set_ylabel(fix(ax.get_ylabel()))
        for text in list(ax.texts):
            text.set_text(fix(text.get_text()))
        legend = ax.get_legend()
        if legend is not None:
            for item in legend.get_texts():
                item.set_text(fix(item.get_text()))
    for text in list(fig.texts):
        text.set_text(fix(text.get_text()))


def save(fig, name: str, table: list[dict] | None = None,
         columns: list[str] | None = None) -> None:
    """Guarda PDF vectorial, PNG de vista previa y el CSV fuente."""
    os.makedirs(FIGDIR, exist_ok=True)
    os.makedirs(CSVDIR, exist_ok=True)
    pdf = os.path.join(FIGDIR, name + ".pdf")
    png = os.path.join(FIGDIR, name + ".png")
    _spanish_decimals(fig)
    fig.savefig(pdf)
    fig.savefig(png)
    plt.close(fig)
    line = "  %s.pdf/.png" % name
    if table:
        cols = columns or list(table[0].keys())
        csv_path = os.path.join(CSVDIR, name + ".csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            for row in table:
                w.writerow({c: row.get(c) for c in cols})
        with open(csv_path, "rb") as fh:
            digest = hashlib.sha256(fh.read()).hexdigest()[:12]
        line += "  | %s.csv (%d filas, sha %s)" % (name, len(table), digest)
    print(line)


def stamp(fig, source: str) -> None:
    """Nota de procedencia al pie, solo para renders de auditoria.

    En el capitulo la procedencia vive en el CSV que acompana a cada figura y en
    canonical_metrics.csv; imprimirla dentro de la figura es ruido editorial.
    Se activa con SP1_FIG_STAMP=1 para revisar de donde salio un panel.
    """
    if os.environ.get("SP1_FIG_STAMP") != "1":
        return
    fig.text(0.005, 0.002, "fuente: %s · git %s" % (source, _git_sha()),
             fontsize=BASE_FS - 3.0, color="#9A9A9A", ha="left", va="bottom")


def err_pair(point, lo, hi):
    """Barras de error asimetricas seguras.

    Con datos discretos o con empates, el IC de percentiles del bootstrap puede
    no envolver exactamente al estimador puntual. Se recorta a cero en lugar de
    fallar o de desplazar el punto: la barra nunca cruza al otro lado.
    """
    if point is None or lo is None or hi is None:
        return (0.0, 0.0)
    return (max(0.0, point - lo), max(0.0, hi - point))
