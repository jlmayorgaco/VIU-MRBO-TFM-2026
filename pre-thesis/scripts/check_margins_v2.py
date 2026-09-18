"""Mide la caja de contenido real de cada pagina del PDF y reporta las que
invaden los margenes VIU (izq/der 3 cm, sup/inf 2,5 cm).

Uso: python scripts/check_margins_v2.py build-v2/main-v2.pdf [tolerancia_cm]
"""
import sys

import pdfplumber

PT_PER_CM = 28.3464567
LEFT_CM = 3.0
RIGHT_CM = 3.0
TOP_CM = 2.5
BOTTOM_CM = 2.5


HEADER_BAND_CM = 2.2  # encabezado y regla de plantilla: fuera de la caja por diseno
FOOTER_BAND_CM = 2.2  # folio centrado


def page_bbox(page):
    """Extremos del contenido de la caja de texto, excluidas las bandas de
    encabezado y pie que la plantilla VIU coloca fuera de los margenes."""
    top_limit = HEADER_BAND_CM * PT_PER_CM
    bottom_limit = page.height - FOOTER_BAND_CM * PT_PER_CM
    x0s, x1s, t0s, b1s = [], [], [], []
    for key in ("chars", "lines", "rects", "curves", "images"):
        for o in getattr(page, key, []) or []:
            if o["bottom"] <= top_limit or o["top"] >= bottom_limit:
                continue
            x0s.append(o["x0"])
            x1s.append(o["x1"])
            t0s.append(o["top"])
            b1s.append(o["bottom"])
    if not x0s:
        return None
    return min(x0s), max(x1s), min(t0s), max(b1s)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "build-v2/main-v2.pdf"
    tol = float(sys.argv[2]) if len(sys.argv) > 2 else 0.10
    offenders = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            bb = page_bbox(page)
            if bb is None:
                continue
            x0, x1, top, bottom = bb
            left_cm = x0 / PT_PER_CM
            right_cm = (page.width - x1) / PT_PER_CM
            top_cm = top / PT_PER_CM
            bottom_cm = (page.height - bottom) / PT_PER_CM
            bad = []
            if left_cm < LEFT_CM - tol:
                bad.append("izq %.2f" % left_cm)
            if right_cm < RIGHT_CM - tol:
                bad.append("der %.2f" % right_cm)
            if top_cm < TOP_CM - tol:
                bad.append("sup %.2f" % top_cm)
            if bottom_cm < BOTTOM_CM - tol:
                bad.append("inf %.2f" % bottom_cm)
            if bad:
                offenders.append((i, right_cm, ", ".join(bad)))
    if not offenders:
        print("Sin invasiones de margen por encima de %.2f cm de tolerancia." % tol)
        return 0
    print("Paginas que invaden margen (tolerancia %.2f cm):" % tol)
    for i, _right, why in offenders:
        print("  p.%-4d %s" % (i, why))
    print("%d pagina(s)." % len(offenders))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
