---
name: citation-hygiene
description: Auditoría de citas y atribución antes de entregar un capítulo o el TFM completo. Comprueba que cada entrada citada existe, que sus metadatos son reales (DOI/Crossref/arXiv), que respalda exactamente lo que el texto le atribuye, y que todo texto ajeno está citado y entrecomillado. Úsala antes de cualquier depósito, entrega al tutor o congelación de un subdocumento.
---

# Higiene de citas

Tres comprobaciones, en este orden: **existencia**, **metadatos**, **adecuación
contextual**. La tercera es la que fallan casi todos los borradores asistidos
por IA: la fuente existe y está bien citada, pero no dice lo que el texto le
atribuye.

El precedente en este repositorio es `Subdocuments/SP2/CITATION_AUDIT.md` y su
`CITATION_AUDIT.json`. Reprodúcelo por subdocumento.

## 1. Existencia

```bash
# entradas realmente citadas en el texto
grep -oE '\\cite[a-zA-Z]*\{[^}]*\}' ARCHIVO.tex | grep -oE '\{.*\}' | tr -d '{}' | tr ',' '\n' | sort -u
# claves declaradas en la bibliografia
grep -oE '^@[a-zA-Z]+\{[^,]+,' references.bib | sed 's/.*{//;s/,//' | sort -u
```

- Toda clave citada debe existir en `references.bib`.
- Toda entrada en `references.bib` debe estar citada, o se retira.
- **Cita inventada = fallo bloqueante.** Un modelo de lenguaje puede producir
  una referencia con autor, año, revista y DOI plausibles y completamente falsa.
  Ninguna entrada entra en el `.bib` sin haberse resuelto contra la fuente.

## 2. Metadatos

Para cada entrada: resolver el DOI y contrastar título, autores, año y venue.
Preprints, contra arXiv. Manuales y normas, contra el documento original.
Registra el resultado; no lo des por hecho.

Si una entrada no tiene DOI ni copia verificable, decláralo explícitamente en la
auditoría en vez de dejar el hueco.

Formato: **APA 7** (requisito VIU). Comprueba mayúsculas de títulos, iniciales de
autor, cursivas y el año, que es el error más frecuente al importar de BibTeX.

## 3. Adecuación contextual — la comprobación que importa

Para cada cita, responde por escrito: **¿qué afirmación exacta respalda esta
fuente, y lo dice de verdad?**

Errores típicos, con ejemplos reales de este repositorio:

- Atribuir a una fuente un método vecino pero distinto (a Lee se le atribuyó
  DMPC vecinal cuando respalda la conmutación MILP–QP).
- Usar un manual de equipamiento para respaldar instrumentación **añadida**
  (el manual Pioneer sólo respalda equipamiento de serie; LiDAR, IMU, cámara y
  transductor se declaran como añadidos).
- Citar un clásico como respaldo genérico de un concepto que el clásico no trata.
- Dejar sin atribución inmediata el primer uso técnico de un término prestado
  (RBPF, grafo relativo, matriz de agarre, LQR, MPC, CBF, caging).

**Regla:** cada término o técnica prestada se cita en su **primera aparición
técnica**, no al final del párrafo ni al final de la sección.

## 4. Texto ajeno

- Cita literal: entrecomillada, con página, y corta. En un TFM técnico, la cita
  literal larga casi nunca hace falta: parafrasea y atribuye.
- Paráfrasis: atribuida igualmente. Reformular no exime de citar.
- Figura, tabla o dato tomados de otra fuente: la fuente va **en el pie**
  (requisito VIU explícito).
- Material propio ya publicado o entregado en otra asignatura: declararlo. El
  TFM debe ser personal, original e inédito.
- Texto redactado con asistencia de IA: declararlo según pida la normativa VIU.
  Comprueba `docs/01_VIU_REQUIREMENTS.md` y, si no lo cubre, pregunta al tutor.
  Declararlo abiertamente es más barato que cualquier alternativa.

Esto es lo que mantiene limpio un informe de similitud, y por la razón correcta.

## 5. Entregable de la auditoría

Genera dos ficheros junto al subdocumento, como en SP2:

- `CITATION_AUDIT.md` — resumen legible: fecha, número de entradas citadas,
  dictamen, correcciones incorporadas, cobertura por entrada.
- `CITATION_AUDIT.json` — dictamen máquina: `verdict`, `reason_code`, `summary`,
  `audited_input_hashes` (sha256 de `references.bib` y de cada `.tex` auditado).

Dictámenes: `PASS`, `ERROR` (fallo de procedimiento, no hallazgo adverso),
`FAIL` (cita inventada, metadatos falsos o atribución incorrecta sin corregir).

Los hashes importan: una auditoría vale para el estado exacto del texto que
auditó. Si el `.tex` cambia, la auditoría caduca.

## 6. Antes del depósito institucional

Última pasada con gestor externo (Zotero o similar) para exportar APA 7 desde
metadatos verificados, en vez de confiar en el `.bib` acumulado.
