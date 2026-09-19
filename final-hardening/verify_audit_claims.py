"""Verifica las afirmaciones numericas de una auditoria externa contra el PDF real.

Las auditorias externas de este TFM han llegado repetidamente con conteos de
frecuencia inventados o medidos sobre una extraccion de texto defectuosa. Antes
de actuar sobre ninguna, se comprueba.

Dos trampas frecuentes que este guion evita:

  1. LaTeX parte palabras al justificar ("estructu-
rada"). En una extraccion
     ingenua parecen erratas; no lo son. Aqui la juntura se deshace antes de
     contar.
  2. Los indices de figuras y tablas extraen sus numeros de pagina sueltos y
     parecen "lineas de numeros huerfanos". Son artefactos de extraccion.

Uso: python final-hardening/verify_audit_claims.py
"""
import io, json, os, re, sys
import pdfplumber

ROOT = r"C:\Users\walla\Documents\Github\VIU-MRBO-TFM-2026"
PDF = os.path.join(ROOT, "pre-thesis", "build-v2", "main-v2.pdf")
CENSUS = os.path.join(ROOT, "final-hardening", "census.json")

# 1) texto del PDF, con la juntura de guion de fin de linea deshecha
pdf = pdfplumber.open(PDF)
pages = [(p.extract_text() or "") for p in pdf.pages]
raw = "\n".join(pages)
# LaTeX parte palabras al justificar: "estructu-\nrada" -> "estructurada"
dehyph = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", raw)
flat = re.sub(r"\s+", " ", dehyph)

print("=== CONTEOS SOBRE EL PDF (texto con guiones de linea deshechos) ===")
claims = [
    ("Sin embargo", 47), ("Ademas/Además", 38), ("Por tanto", 31),
    ("constituye", 24), ("A su vez", 19),
    ("Es importante senalar/señalar", 12), ("Cabe destacar", 9),
    ("En este sentido", 15), ("En el contexto de", 11), ("A modo de resumen", 7),
]
pats = {
    "Sin embargo": r"[Ss]in embargo",
    "Ademas/Además": r"[Aa]dem[aá]s",
    "Por tanto": r"[Pp]or tanto",
    "constituye": r"constituye",
    "A su vez": r"[Aa] su vez",
    "Es importante senalar/señalar": r"[Ee]s importante se[nñ]alar",
    "Cabe destacar": r"[Cc]abe destacar",
    "En este sentido": r"[Ee]n este sentido",
    "En el contexto de": r"[Ee]n el contexto de",
    "A modo de resumen": r"[Aa] modo de resumen",
}
print("%-32s %8s %8s  %s" % ("expresion", "afirma", "real", "veredicto"))
for name, claimed in claims:
    real = len(re.findall(pats[name], flat))
    verdict = "coincide" if abs(real - claimed) <= 2 else ("NO: " + ("sobreestima" if claimed > real else "subestima"))
    print("%-32s %8d %8d  %s" % (name, claimed, real, verdict))

print()
print("=== CALCOS DEL INGLES QUE AFIRMA ENCONTRAR ===")
for c in ["cuello de botella", "l[ií]der del sector", "panorama industrial",
          "rol crucial", "punto de inflexi[oó]n", "visi[oó]n de futuro"]:
    n = len(re.findall(c, flat, re.I))
    print("  %-26s %d" % (c.replace("[ií]", "i").replace("[oó]", "o"), n))

print()
print("=== NUMERACION DEL INDICE: existe '5.4.6'? ===")
toc = "\n".join(pages[3:8])
for m in re.finditer(r"5\.4\.\d", toc):
    print("  encontrado:", toc[max(0, m.start()-60):m.start()+40].replace("\n", " | "))
if not re.search(r"5\.4\.\d", toc):
    print("  NO aparece '5.4.x' en el indice")
print("  secciones 4.x que si aparecen:")
for m in re.finditer(r"\n(4\.\d+)\.?\s+([^\n]{0,55})", toc):
    print("    %-6s %s" % (m.group(1), m.group(2)))

print()
print("=== SUPUESTOS CARACTERES CORRUPTOS ===")
for pno in (1, 12, 13, 15, 20, 24):
    t = pages[pno] if pno < len(pages) else ""
    weird = re.findall(r"[ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞß]{3,}", t)
    print("  PDF p.%-3d secuencias raras: %d %s" % (pno + 1, len(weird), weird[:2]))

print()
print("=== FIGURAS SIN FUENTE ===")
census = json.load(io.open(CENSUS, encoding="utf8"))
nofig = []
for rel in census["files"]:
    p = os.path.join(ROOT, "pre-thesis", rel)
    if not os.path.exists(p):
        continue
    s = io.open(p, encoding="utf8", errors="ignore").read()
    for m in re.finditer(r"\\begin\{figure\}.*?\\end\{figure\}", s, re.S):
        blk = m.group(0)
        if "viusource" not in blk and "viuownsource" not in blk:
            cap = re.search(r"\\caption(?:\[[^\]]*\])?\{([^}]{0,60})", blk)
            nofig.append((os.path.basename(p), cap.group(1) if cap else "(sin caption)"))
print("  figuras activas sin \\viusource ni \\viuownsource: %d" % len(nofig))
for f, c in nofig[:8]:
    print("    %-34s %s" % (f, c))
