# CLAUDE_TASK_v4.md — Blindaje del Informe Intermedio TFM (entrega hasta Metodología)

## 0. Contexto y reglas

Soy Jorge Luis Mayorga Taborda, Máster en Robótica y Automatización de Procesos
(MROB), Universidad Internacional de Valencia (VIU). Tutor: José Ignacio Iñíguez
Amigot. Preparo el INFORME INTERMEDIO del TFM (cubre hasta el final de Metodología;
Marco teórico, Resultados y Conclusiones son stubs y SE QUEDAN como stubs). El objetivo es cumplir con el TFM con las reglas que esta en guidelines
Mi objetivo es sacar un cum laude en esta tesis de amestria, pERO quiero que quede de tal nivel que pareza un poco entre tesis de maestria y aglo ya de nivel doctorado. 
Mi objetivo es enviar esto a comitesd e doctorado para pedir que me acepten asi que ese debe ser lenivel qeu espero.
Tus resultados escribelos en docs/doc-02-mid-report/CLAUDE_TASK.md

### Reglas absolutas (léelas dos veces)
1. Trabaja en docs/doc-02-mid-report`.
2. PRIMERO explora el repo y devuélveme un PLAN (estructura de archivos, mapeo de
   cada tarea a archivo y líneas, riesgos). NO modifiques nada hasta que confirme.
3. Commits atómicos, en español, formato `tipo(scope): descripción`.
4. Tras cada tarea: compila (`latexmk -pdf main.tex` o el flujo del repo) y confirma
   que NO hay referencias/citas indefinidas ni `??`.
5. NO añadas referencias bibliográficas nuevas. NO inventes números, autores,
   teoremas ni resultados.
6. NO toques el paquete Python (`viu_mrob_tfm/` o equivalente).
7. NO infles el alcance: nada de CBF, sistemas híbridos formales, blending, hardware.
8. NO desarrolles los stubs de Marco teórico, Resultados ni Conclusiones.
9. Español, registro académico, coherente con el estilo existente.
10. Cuando una tarea diga "reescribe en voz propia", NO la ejecutes: márcala con
    `% TODO-VOZ:` y déjala para el autor. Esas son tres y están al final.

---

## TAREA 0 — Título y alineación con el Anexo I

### 0.1 Cambiar el título (portada + cualquier \title{} + cabeceras)
Título nuevo:
> Coordinación distribuida para la formación de coaliciones multi-AGV en el
> transporte cooperativo de cargas heterogéneas

Subtítulo (si la plantilla lo admite; si no, omitir):
> Un análisis comparativo de consenso, dinámicas poblacionales y políticas de revisión

### 0.2 Resumen — primera oración puente
Asegura que la primera oración del Resumen contenga el vocabulario del Anexo I
("transporte cooperativo de cargas heterogéneas", "coordinación distribuida").
La versión actual ya empieza bien; solo verifica que "coordinación distribuida"
aparezca explícita en el resumen al menos una vez.

### 0.3 Objetivo general — orientar al título
En §2.1, ajusta el objetivo general para que arranque con "coordinación distribuida"
y mantenga el resto. Texto objetivo:
> Diseñar y evaluar, mediante simulación cuantitativa reproducible, un esquema de
> coordinación distribuida local para flotas multi-AGV que transportan
> cooperativamente cargas heterogéneas, formalizando la heterogeneidad como
> requisito mínimo de cardinalidad y resolviendo la formación adaptativa de
> coaliciones mediante consenso dinámico de media y dinámicas poblacionales,
> caracterizado mediante una escalera comparativa de cinco tratamientos (T1–T5)
> que aísla el papel de la estimación distribuida, la dinámica poblacional y la
> política de revisión, y contrastado con una referencia centralizada
> replanificada bajo seis escenarios experimentales.

### 0.4 §1.6.1 — cerrar el bucle con el Anexo I
Tras la frase existente "El Anexo I de este TFM mencionaba 'cargas heterogéneas'...",
añade una oración:
> El problema central y el objeto de estudio del Anexo I se mantienen; este informe
> concreta la terminología (formación de coaliciones) y la metodología adoptada para
> resolverlos.

**Commit:** `docs(title): alineación de título y objetivos con el Anexo I`

---

## TAREA 1 — Teorema 4.1: nota de régimen de aplicación

En §4.10, tras el enunciado del Teorema 4.1 (entre los límites β_mín/β_máx y el
"Demostración (esbozo)"), inserta:
> Las hipótesis del teorema corresponden a un régimen sin manipulación: la coalición
> no transita al destino, de modo que el equilibrio se analiza en la fase estacionaria
> de reclutamiento. La transición a transporte y la robustez ante perturbaciones se
> evalúan empíricamente en los Escenarios B, C y E (§4.11.2).

**Commit:** `docs(theorem): régimen de aplicación del Teorema 4.1`

---

## TAREA 2 — Lema 4.2: cota correcta

En §4.10, en el enunciado del Lema 4.2, sustituye:
> "En régimen estacionario, una vez que los robots asignados alcanzan el radio de
> detección r_det, se cumple |C_k| = N x̃_k."
por:
> "En general |C_k(t)| ≤ N x̃_k(t), con igualdad cuando todos los robots con s_i = k
> se encuentran dentro de r_det de la tarea k; el régimen estacionario posterior a
> T_coal satisface esta condición."
La demostración NO cambia (parte de x̃_k, no de |C_k|).

**Commit:** `fix(lemma): cota |C_k| ≤ N·x̃_k con condición de igualdad`

---

## TAREA 3 — Algoritmo 1: contador τ_s explícito

Reemplaza las líneas de "Actualización del grafo y modo de tarea" (27–33 actuales)
por una versión con contador. Añade `count_k` al `Require:` e inicialízalo a 0 al
arranque (menciónalo en el texto que introduce el Algoritmo 1 en §4.9):

<!-- ⚠ EL SPEC SE CORTA AQUÍ: falta el bloque de código del Algoritmo 1 y las
     TAREAS 4+ (incl. las tres `% TODO-VOZ` de la Regla 10). -->

---
---

# PLAN DE EJECUCIÓN (Claude Code) — pendiente de tu confirmación

> Regla 2: no modifico la tesis hasta que confirmes. Aquí va el plan + hallazgos.

## A. Estado del repositorio (ya explorado)
- **Motor real: XeLaTeX** (`fontspec` + Arial del sistema). `latexmk`/`pdflatex`
  FALLAN aquí (falta Perl; fontspec exige XeTeX/LuaTeX). Flujo válido desde
  `docs/doc-02-mid-report/`: `xelatex → bibtex → xelatex ×2–3`.
- PDF actual `TFM_InformeIntermedio_v3_blindado.pdf` (46 pp): compila limpio
  (0 refs/citas indefinidas, sin `??`; único overfull 52 pt en bibliografía).
- Título actual en `main.tex:11` (macro `\setviutitle`). La plantilla **no tiene
  comando de subtítulo**; las cabeceras usan título genérico ("Trabajo Fin de
  Máster"), así que el cambio de título afecta **solo a `\setviutitle`**.

## B. Hallazgo clave: TAREAS 1, 2 y 3 YA están aplicadas
En el commit de revisión P1/P2 (`06828ae`) ya se implementó su sustancia:
- **T1** nota de régimen tras Teorema 4.1 (existe `Nota (alcance de las hipótesis)`).
- **T2** Lema 4.2 ya dice `|C_k(t)| ≤ N·x̃_k(t)` con condición de igualdad.
- **T3** Algoritmo 1 ya cuenta `τ_s` pasos consecutivos con `cnt⁺_k/cnt⁻_k` y reinicio.
⇒ Para v4 solo resta **alinear redacción/nombres exactos** (citar §4.11.2; renombrar
a `count_k`). Es reconciliación, no trabajo nuevo.

## C. Mapeo por tarea (archivo · línea · diff)
- **T0.1** `main.tex:11–12` → nuevo título. Subtítulo: la plantilla no lo soporta →
  (a) omitir [defecto] o (b) añadirlo a la portada tocando `viu-mrob-midreport.sty:417`.
- **T0.2** `main.tex` resumen: hoy dice "control distribuido"; insertar "coordinación
  distribuida" explícita ≥1 vez (1 frase).
- **T0.3** `sections/02-objetivos.tex:8–15` → reescribir objetivo general con tu texto.
- **T0.4** `sections/01-introduccion.tex:156` → añadir oración de cierre del Anexo I.
- **T1** `sections/04-metodologia.tex` (nota Teorema 4.1) → alinear a tu texto + citar
  §4.11.2; conservar la frase "cotas suficientes, no necesarias".
- **T2** `sections/04-metodologia.tex` (Lema 4.2) → alinear frase de igualdad a tu texto.
- **T3** `sections/04-metodologia.tex` (Algoritmo 1 + intro §4.9) → renombrar a
  `count_k`, añadir a `Require:`, init 0 mencionado en §4.9. **Falta tu bloque exacto.**

## D. Bloqueantes antes de ejecutar
1. **Spec truncado** a mitad de la TAREA 3. Reenvía: bloque de código del Algoritmo,
   TAREAS 4+, y las tres `% TODO-VOZ` (Regla 10).
2. **¿Confirmas el cambio de título?** Contradice el "título aprobado por el tutor"
   de specs/memoria previas; idealmente visado por el tutor.
3. **Subtítulo:** ¿omitir (a) o añadirlo a la portada modificando el `.sty` (b)?

## E. TODOs heredados aún abiertos
- `references.bib`: verificar `shan2024` (178/104722 vs 179/104724) y `zhang2024`
  (DOI + páginas). `04-metodologia.tex`: verificar Sandholm "Cap. 3" y "Prop. 5.6.1".
- Escenario D: ~1500 sims solo en D; confirmar viabilidad o reducir a 6 puntos de R.

## F. Nota sobre el nivel "máster→doctorado / cum laude"
Lo registro como criterio de calidad transversal para todas las ediciones (rigor en
enunciados, honestidad de alcance, prosa sobria sin AI-smell). No requiere tareas
extra por ahora; lo aplico al redactar.

---
---

# RESULTADOS — TAREA 12 (verificación bibliográfica) · 2026-05-29

Fuentes: Crossref (lookup directo de DOI), IEEE Xplore, e índice oficial del libro
de Sandholm (PDF del autor). Commit: `fix(refs): verificación de granularidad y DOIs`.

## (a) Confirmadas (sin cambio)
- **`shan2024distributed`**: vol.~178, art.~104722, DOI `10.1016/j.robot.2024.104722`
  (Crossref). El "179/104724" era OTRO paper (Wang et al.). TODO eliminado.
- **`martinezpiazuelo2022tcss`** (datos): vol.~52(11), pp.~7112–7122, DOI
  `10.1109/TSMC.2022.3151042` (Crossref). Correcto.
- **Sandholm "Cap.~3"**: el índice confirma Cap.~3 = "Potential Games, Stable Games,
  and Supermodular Games" (juegos de congestión en §3.1.3/§3.1.7). Mantenido.

## (b) Corregidas a valores verificados
- **`zhang2024coalition`**: tenía autores erróneos y DOI inexistente (404). Corregido
  (Crossref + IEEE Xplore doc 10801429) a: autores **Liwang Zhang, Dong Liang,
  Minglong Li, Wenjing Yang, Shaowu Yang**; pp.~**3439–3446**; DOI
  `10.1109/IROS58592.2024.10801429`. → conviene que reconfirmes en IEEE Xplore.

## (c) Degradadas a granularidad verificable + `% TODO-CITA`
- **Sandholm "Prop.~5.6.1"** → **"§5.6 y §7.1"** (§5.6 Pairwise Comparison Dynamics;
  §7.1 Potential Functions as Lyapunov Functions). El nº de proposición exacto no es
  verificable desde el índice.
- **`martinezpiazuelo2022tcss` "Sección III, Teorema 3"** → cita genérica; prosa
  ajustada a "dinámicas de población distribuidas en tiempo discreto". `% TODO-CITA`
  para que confirmes localizador exacto y cobertura del caso Smith.

## Pendiente para ti
1. (`% TODO-CITA`) Confirmar contra el paper de Martínez-Piazuelo el localizador y
   que el resultado cubre Smith/pairwise.
2. (recomendado) Reconfirmar en IEEE Xplore la entrada corregida de `zhang2024`.
