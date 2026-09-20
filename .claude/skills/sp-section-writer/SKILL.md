---
name: sp-section-writer
description: Microestructura obligatoria y notación canónica al crear, completar o revisar una sección SP (SP1, SP2, SP3) del capítulo 6. Úsala antes de añadir o reordenar bloques en Subdocuments/SP*/ o thesis/sections/mainmatter/06-results-and-analysis/. Impide la deriva de notación entre los ~460 ficheros .tex del repositorio.
---

# Escribir una sección SP

Fuentes vinculantes, en este orden (ver `AGENTS.md` §2):
`docs/07_SP_SECTION_TEMPLATE.md` → `docs/05_NOTATION.md` →
`docs/02_RESEARCH_MATRIX.md` → `docs/01_VIU_REQUIREMENTS.md`.

Lee la plantilla completa antes de escribir. Este documento resume las reglas
que más se incumplen; no la sustituye.

## 1. Antes de escribir una línea

1. ¿Qué subproblema es y qué nivel de evidencia le corresponde en
   `docs/02_RESEARCH_MATRIX.md`? Una etapa de evidencia C **puede ser más
   breve**; no se rellena para igualar longitudes.
2. ¿Qué macros generadas existen ya (`generated/*.tex`)? Toda cifra saldrá de
   ahí. Si la cifra no existe, se genera en el script antes de escribir la frase.
3. ¿Qué símbolos usa esta sección y cómo se llaman en `docs/05_NOTATION.md`?

## 2. Reglas estructurales duras

- Cada SP canónico es una `\subsection` del capítulo 6 y **empieza en página
  nueva** con `\clearpage`.
- Etapas internas: `\subsubsection`. Bloques: `\paragraph`.
- **Nunca dos encabezados consecutivos sin texto entre ellos.** Cada nivel
  comienza con prosa introductoria.
- El contenido común (protocolo Monte Carlo, generadores, métricas, estadística)
  va en `index.tex` o en Metodología, **no repetido en cada SP**. Tres SP no son
  tres miniartículos.
- Nunca se inventa una sección de control, una prueba o una comparación sólo
  para llenar la plantilla.

## 3. Ampliaciones obligatorias de la plantilla maestra

Cada SP debe, además:

1. incluir un **contraejemplo incremental** (qué deja de valer al retirar el
   supuesto anterior);
2. declarar la **cadena de información realmente ejecutada** (qué sabe cada AMR,
   cuándo, y por qué mensaje);
3. **clasificar el estado de sus aportes** (demostrado / medido / no afirmado)
   — en prosa corrida, sin cajas ni etiquetas visibles;
4. **separar límite teórico de límite práctico**.

## 4. Qué va al cuerpo y qué al anexo

El cuerpo es caro: el capítulo 6 tiene 34–39 páginas para tres SP, y la VIU
exige que ≥50 % del cuerpo principal sea resultados y análisis.

| Al anexo | En el cuerpo |
|---|---|
| Pseudocódigos completos de baselines | El resultado y su lectura |
| Tablas estadísticas completas | La cifra que se cita en prosa |
| Trazas individuales | La figura núcleo de la sección |
| Regresiones de escalado detalladas | La pendiente y su intervalo |
| Fichas de método | La comparación |
| Protocolo Monte Carlo y generadores | (van a Metodología general) |

Regla de figuras: se conserva un núcleo pequeño. **Toda figura adicional debe
justificar su espacio frente a ese núcleo.** Objetivo SP1: ≤ 48 elementos
visuales y 0 bandas negras de plantilla en el `main`.

## 5. Notación

- Antes de introducir un símbolo, búscalo en `docs/05_NOTATION.md`. Si existe,
  úsalo tal cual. Si no existe y hace falta, **añádelo allí** en el mismo cambio.
- Nunca dos nombres para el mismo objeto en dos SP distintos.
- $h_c^\star$ (no $h^\star$) en leyendas de figura.
- **AMR** en prosa, pies, tablas y dentro de los TikZ.
- Ecuaciones, figuras y tablas: numeradas, citadas en el texto y con fuente
  declarada (requisito VIU, APA 7).

## 6. Interfaces entre SP

Los SP se conectan por **interfaces verificables**, no por narrativa. Al cerrar
un SP, declara qué objeto entrega al siguiente y bajo qué supuestos (SP1 entrega
una coalición; SP2 decide si es físicamente realizable). Si el objeto de salida
cambia, actualiza también el SP receptor.

## 7. Restricciones científicas que no se negocian

De `AGENTS.md` §3.2:

- Sin RL multiagente como método principal.
- Arquitectura distribuida; el optimizador central sólo como baseline u oráculo.
- Algoritmo white-box: estados, payoffs, restricciones y leyes de control
  interpretables.
- Sin FSM global de alto nivel.
- Distinguir siempre modelo continuo de ejecución digital muestreada.
- **No afirmar optimalidad, convergencia, estabilidad, robustez ni escalabilidad
  sin definición formal y evidencia.** Ver la habilidad `claims-evidence-guard`.

## 8. Al terminar

- Pasa `tfm-voice` sobre la prosa nueva.
- Pasa `claims-evidence-guard` sobre toda afirmación de rendimiento.
- Comprueba numeración consecutiva, sin página huérfana y sin `Overfull`.
