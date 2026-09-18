# BASELINE_REPORT — congelación previa al endurecimiento final

Medido el **2026-09-18** sobre el árbol **sin modificar** en esta fase.
Todo número de este fichero procede de una compilación limpia ejecutada hoy o de
una medición directa sobre el PDF resultante. Nada está estimado.

---

## 1. Estado de git

| Campo | Valor |
|---|---|
| Rama | `sp1-final-refactor` |
| HEAD inicial | `3a320428b94f33a4ea49114104f6a03a1c3ef67c` |
| Último commit | `review: close prior art and record follow-up campaigns` |
| Ficheros tracked modificados | 224 |
| Ficheros untracked | 319 |
| **`pre-thesis/` en git** | **0 ficheros tracked** — y no está en `.gitignore` |

### Decisión sobre la rama

El árbol de trabajo **no está limpio** (224 modificados + 319 sin seguimiento).
Siguiendo la regla §2.4, **permanezco en `sp1-final-refactor`** y no creo
`research/tfm-final-hardening`. Motivo concreto, no genérico: los 224 ficheros
modificados pertenecen a trabajo anterior no relacionado con `pre-thesis/`
(SP1, `academic-review/`, `Makefile`, `docs/`), y crear una rama ahora los
arrastraría a ella, mezclando dos líneas de trabajo en el mismo conjunto de
commits. Los cambios permanecen exactamente donde están.

### Riesgo activo de pérdida de datos

**La memoria completa vive fuera del control de versiones.** `git ls-files
pre-thesis` devuelve cero. No está ignorada: simplemente nunca se añadió. Son 89
ficheros `.tex` activos más figuras, datos y scripts. Un `git clean -fd` en la
raíz del repositorio los borraría sin recuperación posible.

La fase 1 de commits (§47) resuelve esto y es lo primero que debe ejecutarse.

---

## 2. Compilación del documento principal

Orquestada por `pre-thesis/build-v2.ps1` (LuaLaTeX → Biber → LuaLaTeX ×2).
Código de salida **0**.

| Métrica | Valor |
|---|---|
| Errores LaTeX (`^!`) | **0** |
| Referencias indefinidas | **0** |
| Etiquetas multiplemente definidas | **0** |
| `Overfull \hbox` | 8 |
| `Underfull \hbox/\vbox` | 40 |
| Avisos de Biber (`main-v2.blg`) | **0** |

Los 8 *overfull* miden entre 0,67 pt y 4,80 pt. El mayor equivale a 1,7 mm: por
debajo del umbral de detección visual en página impresa. Ninguno requiere
intervención antes del depósito.

### Ficheros y resultados activos

Resuelto recursivamente desde `main-v2.tex` con
`pre-thesis/scripts/census_formal_results.py` (añadido en esta fase):

| Métrica | Valor |
|---|---|
| Ficheros `.tex` realmente incluidos | 89 |
| Entornos formales (teorema/proposición/lema/corolario) | 29 |
| Ecuaciones con `\label{eq:...}` | 55 |
| Ecuaciones etiquetadas y **nunca citadas** | 5 |
| Etiquetas duplicadas | 0 |

Las 5 ecuaciones sin citar están todas en el bloque «epistémico» de
`sections/v2/appendix-megajuego-detail.tex`
(`eq:megajuego-epistemic-{state,message,belief,commit,delta}`). VIU exige que
toda ecuación numerada se cite por su número, de modo que o se citan o pierden
la numeración.

De los 29 entornos formales, aproximadamente 11 son **reenunciados** cuerpo ↔
anexo del mismo resultado (por ejemplo `thm:sp2-compact-e6-exact-potential` en
el cuerpo y `thm:sp6-exact-potential` en el anexo). El número de resultados
distintos ronda 18 y debe fijarse con precisión en `MATH_AUDIT.md`.

---

## 3. Reparto de páginas — documento principal

**146 páginas** en total.

| Bloque | Páginas |
|---|---:|
| Preliminares | 16 |
| **Cuerpo** | **68** |
| **Anexos** | **50** |

### Cuerpo, por capítulo

| Capítulo | Páginas |
|---|---:|
| 1 Introducción | 5 |
| 2 Objetivos | 2 |
| 3 Hipótesis de partida | 3 |
| 4 Metodología | 8 |
| 5 Marco teórico y estado del arte | 15 |
| **6 Resultados y análisis** | **29** |
| 7 Conclusiones y recomendaciones | 6 |
| 8 Referencias bibliográficas | 11 |

### Anexos, por apéndice

| Anexo | Páginas |
|---|---:|
| A Reproducibilidad y disponibilidad | 0 † |
| B Demostraciones seleccionadas de SP1 | 1 |
| C Demostraciones seleccionadas de SP2 | 3 |
| D Demostraciones compactas de recuperación | 2 |
| E Demostraciones seleccionadas de SP3 | 1 |
| F Detalle completo de la revisión | 7 |
| G Detalle completo de SP1 | 7 |
| H Detalle completo de SP2 | 15 |
| I Detalle completo de SP3 | 6 |
| J Detalle completo del juego de integración | 8 |
| **Total** | **50** |

† Los repartos marcados 0 y el «Abstract 9 pág.» son artefactos de marcadores
PDF, no del contenido: `03-contents.tex` emite los tres índices sin
`\phantomsection` + `\addcontentsline`, de modo que carecen de marcador y el
tramo anterior absorbe sus páginas. Afecta a la atribución por capítulo, **no** a
los totales de cuerpo y anexos, que se calculan por límites de bloque.

---

## 4. Conformidad VIU — estado del *gate* mecánico

`python .claude/skills/viu-compliance/scripts/viu_check.py pre-thesis/build-v2/main-v2.pdf`

**11 comprobaciones en verde, 2 fallos duros.**

| Comprobación | Estado | Medido |
|---|---|---|
| Tamaño de página | ok | A4 vertical (595 × 842 pt) |
| Arial incrustada | ok | 4 cortes, sin sustitución silenciosa |
| Resumen 200–300 palabras | ok | 299 |
| Palabras clave 3–5 | ok | 5 |
| Encabezado con el estudiante | ok | presente |
| Cuerpo 50–80 páginas | ok | 68 |
| **Anexos ≤ 20 páginas** | **FALLO** | **50** |
| **Resultados ≥ 50 % del cuerpo** | **FALLO** | **29 / 68 = 43 %** |

### Aritmética de los dos fallos

**Anexos.** Hay que migrar **30 páginas** al documento suplementario.
F + G + H + I suman 35 páginas de «detalle completo» y son el candidato natural;
B + C + D + E suman 7 páginas de demostraciones esenciales que deben
permanecer, porque sostienen afirmaciones activas.

**Resultados.** Con R = 29 y B = 68, la condición (R+x)/(B−c+x) ≥ 0,5 se reduce a

    x + c >= 10

donde `x` son páginas de resultado añadidas y `c` páginas de cuerpo no-resultado
retiradas. El Marco teórico (15 pp) es el único bloque con holgura suficiente
para aportar `c` sin dañar el argumento.

---

## 5. Márgenes

Medidos con `pre-thesis/scripts/check_margins_v2.py` (añadido en esta fase), que
excluye las bandas de encabezado y pie que la plantilla VIU sitúa fuera de la
caja por diseño. Regla: izq/der 3 cm, sup/inf 2,5 cm; tolerancia 0,10 cm.

| Página PDF | Medida | Lectura |
|---|---|---|
| p.1 | 0,00 cm en los cuatro lados | Portada a sangre completa, por diseño |
| p.19 | sup 2,12 cm | Apertura de capítulo, posición de plantilla |
| **p.44** | **izq 2,26 · der 2,26 cm** | **Invasión real de 0,74 cm por lado** |
| p.55, p.64, p.74 | der 2,86–2,89 cm | ≤ 0,14 cm: redondeo de justificación |
| p.105, p.108 | izq/der 2,88–2,89 cm | ≤ 0,12 cm: filetes de tabla |
| p.125 | inf 2,38 cm | Vuelo de descendentes, no caja |

**Una sola invasión real: la p.44.** Corresponde a una figura de
`sections/source-snapshot/mainmatter/05-theoretical-framework.tex`, fichero de
la v1 sellada. No se ha tocado.

---

## 6. Documento suplementario

`pre-thesis/build-supplementary.ps1` → `supplementary/build/supplementary.pdf`

| Métrica | Valor |
|---|---|
| Páginas | 114 |
| Errores LaTeX | 0 |
| Referencias indefinidas | 0 |

Compila limpio y tiene espacio sin límite normativo. Es el destino previsto de
las 30 páginas de anexo que deben salir del documento principal.

---

## 7. Infraestructura disponible para las fases siguientes

Verificado en esta máquina, no supuesto:

| Recurso | Estado |
|---|---|
| CoppeliaSim Edu | **instalado** en `C:\Program Files\CoppeliaRobotics\CoppeliaSimEdu` (`coppeliaSim.exe`) |
| Cliente ZMQ remote API | **instalado** (`coppeliasim_zmqremoteapi_client`) |
| Escenas CoppeliaSim | `coppeliasim/real_scenes/` — escena AWS Industrial 2 (`.ttt` + `.lua` + `.yaml`) y `cargo_primary_mujoco_v1.ttt` con manifiesto y log de construcción |
| numpy / scipy / pandas / statsmodels | instalados |
| pypdf / pdfplumber | instalados |

La consecuencia operativa es que **las campañas confirmatorias de §25 y la
reestadística de §22/§28 son ejecutables en esta máquina**, no solo
planificables. Falta comprobar que las escenas arrancan en modo headless y que
los guiones de campaña existentes son reutilizables.

---

## 8. Rutas canónicas confirmadas

Verificadas una a una; la única que no está donde el encargo suponía es
`viu_check.py`.

| Ruta | Estado |
|---|---|
| `pre-thesis/main-v2.tex` | existe |
| `pre-thesis/sections/v2/` | existe |
| `pre-thesis/sections/v2/thesis-results-v2.tex` | existe |
| `pre-thesis/sections/v2/01-introduction-impact-v2.tex` | existe |
| `pre-thesis/sections/v2/megajuego-compact.tex` | existe |
| `pre-thesis/sections/v2/appendix-megajuego-detail.tex` | existe |
| `pre-thesis/sections/v2/review-compact.tex` | existe |
| `pre-thesis/supplementary/` | existe |
| `pre-thesis/scripts/check_margins_v2.py` | existe |
| `scripts/viu_check.py` | **no existe**; está en `.claude/skills/viu-compliance/scripts/viu_check.py` |

---

## 9. Contadores de referencia

Cualquier medida posterior se compara contra esta fila.

| Métrica | Baseline |
|---|---:|
| Páginas totales | 146 |
| Cuerpo | 68 |
| Resultados / análisis / validación | 29 (43 %) |
| Anexos | 50 |
| Errores LaTeX | 0 |
| Referencias indefinidas | 0 |
| Etiquetas duplicadas | 0 |
| Overfull boxes | 8 (máx. 4,80 pt) |
| Avisos de bibliografía | 0 |
| Invasiones reales de margen | 1 (p.44) |
| Fallos duros VIU | 2 |
| Suplementario | 114 pp, 0 errores |
