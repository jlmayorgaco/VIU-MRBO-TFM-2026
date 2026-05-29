# CHANGELOG — Blindaje del Informe Intermedio de TFM

Rama: `blindaje-intermedio-v1` (desde `blindaje-v3`).
Documento: `docs/doc-02-mid-report/` (LaTeX, motor **XeLaTeX** por dependencia de
`fontspec`/fuentes Arial del sistema). PDF final: **44 páginas**.

> Nota de contexto: el `CLAUDE_TASK.md` se redactó contra una versión anterior y
> monolítica del documento (todo en una "§6"). En el estado real la metodología es
> la **sección 4** y el contenido está repartido en `sections/*.tex`. Buena parte de
> la TAREA 1 y de la TAREA 5 ya estaba aplicada; abajo se detalla lo realmente
> modificado. Las referencias §6.x del task se mapearon a `04-metodologia.tex`.

---

## TAREA 1 — Integridad de citas
**Commit:** `fix(refs+doc): flag DOIs no verificables; erratas ...`

- **Ya correctas (sin cambios):** `martinezpiazuelo2022tcss` (MP2022a: autores sin
  Ocampo-Martínez, vol. 52(11):7112–7122, DOI 10.1109/TSMC.2022.3151042);
  `dinh2026bsplines` (preprint SSRN 2025, `@misc`, DOI 10.2139/ssrn.5276334);
  H4 sin atribución de umbrales; proyección al símplex descrita como "algoritmo
  estándar de clasificación y umbral, O(K log K)" sin cita a Sandholm.
- **Modificado** `references.bib`: añadidos comentarios `% TODO: verificar`
  (fuera de las entradas, para no romper BibTeX) a `shan2024distributed` y
  `zhang2024coalition`.

## TAREA 2 — Errores de render
**Commit:** (mismo que T1)

- `sections/01-introduccion.tex`: `Consídere` → `Considérese`.
- `sections/04-metodologia.tex`: `Consídere` → `Considérese`; `homógeneas` →
  `homogéneas`; `hipotésis` → `hipótesis`.
- No había `§??` ni `m´ın`/`max´`; "catorce subsecciones" ya era correcto.

## TAREA 3 — Escalera comparativa y reformulación de hipótesis (CAMBIO ESTRUCTURAL)
**Commit:** `refactor(method): escalera comparativa T1-T5 y reformulacion de hipotesis`

- **Reframe de-Smith** (decisión confirmada: reframe completo):
  - `main.tex` (abstract): de "propone una ley basada en Smith" a escalera
    comparativa de cinco tratamientos; el método propuesto es **T4**.
  - `sections/02-objetivos.tex`: objetivo general → "consenso + dinámicas
    poblacionales", escalera de cinco tratamientos.
  - `sections/01-introduccion.tex`: §1.2 retitulada "El papel de la política de
    revisión: replicador y Smith"; lista de tratamientos renombrada.
- **Renumeración (confirmada): T4 = Smith propuesto, T5 = centralizado.**
  - `sections/04-metodologia.tex`: bloque de tratamientos reescrito —
    T1 voraz · T2 DAC+voraz · T3 replicador modificado (doble consenso) ·
    T4 Smith+μ modulada (propuesto, ablación μ const vs. modulada) ·
    T5 referencia centralizada replanificada (ΔT_c=1 s + eventos, misma cinemática).
  - `sections/00-nomenclatura.tex`: ΔT_c "(T4)" → "(T5)".
  - Criterios de aceptación: "tratamiento~T5" → "T4"; ablación valida **H5**.
- **Hipótesis H1–H6** (`sections/03-hipotesis.tex`, reescrito): seis hipótesis sin
  umbrales numéricos + subsección "Criterios cuantitativos de contraste" con los
  umbrales (40 %/15 % → H5; F≥0,85; ΔJ<0,25/0,40 → H6) conservando los valores.
- **Tabla 3** (`tab:hipescenario`) reescrita: 6 filas
  hipótesis | comparación | escenarios | métrica.

## TAREA 4 — Contribución y encaje narrativo
**Commit:** `docs(intro): contribucion de cuatro puntos y pregunta de investigacion recalibrada`

- `sections/01-introduccion.tex` §1.3: enumerate Smith-céntrico → **cuatro
  contribuciones** en prosa (payoff sigmoidal compatible con replicador y Smith;
  adaptación comparada de ambos; tasa modulada; coste de descentralización).
- Frase **defensiva de alcance** al cierre de §1.
- Pregunta de investigación recalibrada (no Smith-céntrica) en
  `sections/03-hipotesis.tex` (cumple TAREA 4.3; alojada en §3 por coherencia).

## TAREA 5 — Núcleo técnico
**Commit:** `feat(method): Teorema base + Proposicion de perturbacion, look-ahead, Lema entero`

- *Ya aplicado en versiones previas:* DAC sin reinicialización (innovación Δy);
  factor `r/N` en el potencial; Hessiana `−rNβ/4`; Lipschitz `β/4` y `rNβ/4`;
  `μ_min = 0,02 μ₀`; APF con `ε_r²`; histéresis `ρ_s` (eq. `eq:hysteresis`).
- **5.3:** caso base convertido a **Teorema 1** (`teorema`), enunciado con
  R=∞, Ψ≡1, homogéneo, N=Kn, sin transición de modo; nueva **Proposición 2**
  (`prop:perturbacion`): `|δf_ik| ≤ (r_k β N/4) ē`; el sistema implementado se
  describe como versión perturbada → "convergencia práctica a una vecindad",
  evaluada por F, D(R), Δchg, ΔJ. Propagado Proposición→Teorema en abstract,
  intro, hipótesis, resultados y criterios.
- **5.5/5.6:** navegación reformulada con **punto adelantado** `h_i`
  (`eq:lookahead`), campo `F_i(h_i)` con repulsión `‖h_i−h_j‖²+ε_r²`, conversión
  por **jacobiano invertido** (`eq:lookahead_cmd`, det = ℓ); Bloque 4 del
  Algoritmo actualizado. `K_θ` retirado (ya no se usa).
- **5.7:** **Lema "Criterio entero de factibilidad"** (`lema:entero`).
- **5.8:** `ℓ` añadido a Tabla 5 (`ℓ=0,15 m`) y a Nomenclatura; `μ_min`, `ρ_s` ya
  estaban en ambas.

## TAREA 6 — Métricas y validación
**Commit:** `feat(eval): metricas E_DAC y N_fail; alcance honesto de CoppeliaSim`

- `sections/04-metodologia.tex` Tabla 4: añadidas **E_DAC** (error medio de
  estimación) y **N_fail** (episodios fallidos). Conteo de métricas 9 → 11.
- §"Validación en CoppeliaSim": párrafo explícito — verifica **viabilidad
  cinemática**, NO la manipulación cooperativa por contacto (capa complementaria,
  Ebel 2024 / Rosenfelder 2024); carga = cuboide pasivo acoplado al centroide.

## TAREA 7 — Pulido de estilo
**Commit:** `style: lexico academico (idle->inactivo, ...)`

- `idle` → `inactivo (\textit{idle})`; "ningún enfoque existente" → "en el corpus
  revisado no se identifica un enfoque que".
- *Ya migrados previamente:* `bodega`→`almacén automatizado`,
  `codicia local`→`heurística voraz local`, `huella de carbono`→`proxy de consumo
  energético`. No quedaban `óptimo centralizado` ni analogía P/PD.
- **"garantiza":** revisado en todo el documento; los usos restantes son
  negaciones, hechos demostrados (lemas) o el caso base del Teorema 1 — no hay
  sobreafirmación del método en el caso general (tras T5 ya se usa "convergencia
  práctica / se evalúa empíricamente").

## TAREA 8 — Compilación final
**Commit:** `build: compilacion final del informe intermedio blindado`

- Flujo: `xelatex → bibtex → xelatex ×3` (XeLaTeX por `fontspec`).
- **Sin** referencias indefinidas, **sin** citas indefinidas, **sin `??`** en el
  PDF (verificado con `pdftotext`), refs cruzadas estables.
- toc/lof/lot regenerados (46/5/6 líneas). Bibliografía completa (bibtex sin
  warnings).
- PDF final: `docs/doc-02-mid-report/TFM_InformeIntermedio_v3_blindado.pdf`.

---

---

## Revisión P1/P2 (2026-05-29) — segunda pasada de blindaje
**Commit:** `fix(review): coherencia tecnica, contadores, anti-AI-smell y formato (P1/P2)`

Núcleo técnico / coherencia:
- **(3)** Nota tras el Teorema~4.1: las hipótesis corresponden a un escenario sin
  manipulación (sin transición de modo, $\Psi\equiv 1$); el equilibrio se analiza
  solo en la fase de reclutamiento; el transporte se evalúa en B, C, E.
- **(7)** Frase explícita: $\beta_{\min},\beta_{\max}$ son condiciones
  \emph{suficientes} (Lyapunov), no necesarias.
- **(4)** Lema~4.2 reformulado: $|\mathcal{C}_k| \leq N\tilde{x}_k$ en general, con
  igualdad cuando todos los robots con $s_i=k$ están dentro de $r_{\det}$.
- **(5)** Algoritmo~1: materializados los contadores $\mathrm{cnt}^{\pm}_k$ de
  $\tau_s$ pasos consecutivos, con reinicio al cruzar $n_k$.
- **(6)** Obs. del tiempo de DAC: sustituido el anillo $C_6$ por "Fiedler de
  configuraciones densas en 2D" ($\lambda_2\approx 1$), con el caso $R=\infty$
  ($\lambda_2=N$) como cota.
- **(8)** Umbral H5 relajado 40 % → **30 %** y justificación reescrita (meta
  conservadora, a afinar con datos).

Anti-AI-smell:
- **(9)** Reducidos los em-dashes parentéticos (resumen, §1, objetivos, tratamientos):
  ~8 convertidos a paréntesis/comas.
- **(10)** §1.3: "Primero/Segundo/…" → "La primera/La segunda/…".
- **(11)** Tratamientos: 5× "Pregunta que responde:" → prosa (responde/aísla/examina/evalúa/cuantifica).
- **(12)** Frase defensiva §1: reescrita en afirmativo (sin pivote "no X, sino Y").
- **(13)** Podadas cursivas retóricas (`continuamente`, `individuales`).

Formato:
- **(14)** Quitado `\textbf` del resumen. **(17)** Añadidos *Keywords* en inglés.
- **(18)** Figura 1: `|C_2|=3 ≥ n_2` → `=`. **(19)** "catorce" → "quince" subsecciones.
- **(20)** `bullo2009distributed` citado por segunda vez (apertura de §4.7).
- **(P2)** `ρ_s=0,05` mencionado en el texto de la regla; `v_max` conservador
  justificado (escena reducida); §5 Marco renumerado 7.x → 5.x; eliminada la
  segunda variante de "no puede descartarse … corpus revisado".

PDF final: **46 páginas**.

---

## TODOs pendientes (`% TODO: verificar`)

En `references.bib`:
1. **`shan2024distributed`** — confirmar volumen/artículo (178/104722 vs. 179/104724)
   y rango de páginas contra IEEE/Elsevier.
2. **`zhang2024coalition`** — confirmar DOI (`10.1109/IROS58592.2024.10801234`) y
   añadir rango de páginas; no verificable contra IEEE Xplore en esta sesión.

En `sections/04-metodologia.tex` (revisión P1, item 21):
3. **Sandholm 2010, "Cap. 3"** (juego potencial de congestión) — verificar el número
   de capítulo contra el libro.
4. **Sandholm 2010, "Prop. 5.6.1"** (Smith asciende el potencial) — verificar el
   número exacto contra el libro.

Pendientes de decisión del autor (no editados):
- **(item 22)** Escenario D: 10 puntos de $R$ × 30 rep. × 5 tratamientos ⇒ ~1500
  simulaciones solo en D (~4500+ en total). Confirmar viabilidad de cómputo o
  reducir a 6 puntos.
- **(§4.7 signo)** El signo del término atractivo $+\tfrac{\alpha}{2}\|h-\ell\|^2$ es
  correcto ($-\nabla F$ apunta al objetivo); reverificar a ojo en el código Python.

## Referencias cruzadas añadidas / modificadas

- **Nuevas etiquetas:** `eq:lookahead`, `eq:lookahead_cmd` (navegación look-ahead);
  `prop:perturbacion` (Proposición 2); `lema:entero` (Lema criterio entero).
- **Reetiquetado semántico:** `prop:convergencia` ahora es un **Teorema** (entorno
  `teorema`); todas sus `\ref` (abstract, §1, §3, §4 ×varias, §6) actualizadas de
  "Proposición" a "Teorema" con concordancia de artículo.
- **Eliminadas:** `eq:gradient`, `eq:speed`, `eq:angular` (sustituidas por la
  formulación look-ahead); el `\eqref` del Bloque 4 ahora apunta a `eq:lookahead_cmd`.
- TAREA 2.1: los tres `§??` que el task esperaba **no existían** en esta versión
  (ya resueltos); `\S\ref{sec:alcance}` y las refs de §1.2 ya estaban presentes y
  resuelven.

## Decisión que requiere tu visto bueno

- **Nomenclatura desactivada:** en `main.tex` la sección Nomenclatura está comentada
  ("pendiente de rediseño"). Por tanto **no aparece en el PDF**. Mis ediciones a
  `sections/00-nomenclatura.tex` (ΔT_c, ℓ) quedan listas para cuando se reactive.
  Los símbolos `μ_min`, `ρ_s`, `ℓ` SÍ aparecen en la **Tabla 5** (Parámetros), que
  es la fuente operativa actual (TAREA 5.8 satisfecha vía Tabla 5). ¿Reactivamos la
  Nomenclatura para la entrega?
