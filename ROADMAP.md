# ROADMAP.md — Plan maestro Codex para cerrar el TFM submit-ready

> **Destino:** copiar este archivo en la raíz del repositorio como `ROADMAP.md`.
>
> **Rol de Codex:** actuar como ingeniero de cierre académico: limpiar el repositorio, congelar evidencia, generar scripts faltantes, regenerar figuras/tablas, ejecutar solo experimentos permitidos, redactar y pulir la memoria final hasta quedar lista para predepósito/depósito.
>
> **Fecha de bloqueo narrativo:** 2026-07-10.

---

## 0. Contrato duro de ejecución

### 0.1 Reglas no negociables

1. **No renumerar SP1–SP8.** Los códigos SP existentes son evidencia canónica. La narrativa puede reencuadrarlos por ejes E1–E8, pero los nombres/rutas/códigos no se cambian.
2. **No regenerar campañas high-power SP1–SP8.** Usar resultados canónicos de `docs/CANONICAL_RESULTS.md` y `results/sp*/.../tables/*.csv`. Solo se permiten smoke/compact runs si una refactorización rompe tests o auditorías.
3. **No inventar resultados.** Si CoppeliaSim, Zenodo, vídeos o capturas no se pueden ejecutar/generar en el entorno, dejar scripts/configs/lista de ejecución y marcarlo como `PENDIENTE DE EJECUCIÓN HUMANA`. Nunca escribir resultados simulados como si fueran datos reales.
4. **No vender un método campeón.** La contribución no es “Smith-QR gana”. La contribución es: formulación físico-económica + comparación sistemática entre familias + mapa de regímenes + brecha teoría→implementación.
5. **Toda frase fuerte del TFM debe mapear a una de estas fuentes:**
   - resultado propio canónico (`CANONICAL_RESULTS`, `results/sp*/...`, `theory_validation`, `sp9` si existe);
   - claim autorizado en `docs/CLAIM_LEDGER.md`;
   - cita bibliográfica real en `references.bib`;
   - limitación/trabajo futuro explícitamente marcado.
6. **Idioma final:** español académico. Referencias APA 7. Figuras y tablas en español con tildes correctas.
7. **Normativa VIU:** cuerpo principal entre 50–80 páginas; anexos oficiales máximo 20 páginas. Borradores en Word si el tutor lo pide; entrega final en PDF. No generar anexos de 25–30 páginas dentro del TFM oficial.
8. **Originalidad y trazabilidad:** no copiar manuscritos completos sin integración. Los manuscritos se condensan en teoría, figuras y anexos compactos. Material largo va a repositorio/suplemento, no al cuerpo principal.
9. **No usar lenguaje industrial/hardware no demostrado.** Usar “simulación reproducible”, “simulador físico CoppeliaSim”, “plausibilidad robótica”, “brecha teoría→implementación”. No usar “validado industrialmente”, “hardware real”, “garantía 3D completa”.
10. **No ocultar resultados negativos.** SP con hipótesis no rechazadas o métodos propios no dominantes se mantienen y se redactan como conocimiento experimental.

### 0.2 Fuente de verdad ante conflictos

| Conflicto | Gana |
|---|---|
| Rutas/resultados/artefactos SP1–SP8 | `docs/CANONICAL_RESULTS.md` |
| Redacción segura de claims | `docs/CLAIM_LEDGER.md` |
| Narrativa global y orden de cierre | este `ROADMAP.md` |
| Normativa formal de entrega | documentos VIU oficiales |
| Pruebas matemáticas | manuscritos Doc-II/Doc-III/anexo matemático ya existentes |
| Resultados SP9 | solo `results/sp9/...` si existe con CSV, figuras, reporte y manifest |

---

## 1. Tesis bloqueada

### 1.1 Frase madre

> **El transporte cooperativo de cargas heterogéneas por AMR se formula como un juego físico-económico de llave —wrench— gobernado por una señal común de déficit. Sobre esa señal se comparan sistemáticamente familias de solución poblacionales, primal-dual/Nash seeking, de mercado, clásicas, centralizadas y aprendidas; se caracterizan los regímenes en los que cada familia conserva valor; y se cuantifica la brecha entre teoría, simulación reproducible y ejecución robótica de mayor fidelidad en CoppeliaSim/Pioneer.**

### 1.2 Versión corta para introducción y defensa

> Las cargas no compran robots; compran capacidad física efectiva. Esa capacidad empieza como quórum, se refina como capacidad heterogénea, se certifica como wrench, se ejecuta mediante movimiento y control seguro, y se evalúa bajo obstáculos, fallos, comunicación local, escala y brecha de implementación.

### 1.3 Regla narrativa central

No escribir:

> “Nuestro método Smith-QR supera al estado del arte.”

Escribir:

> “Bajo cada restricción dominante —quórum entero, heterogeneidad, wrench vectorial, obstáculos, fallos, comunicación local o escala— la comparación revela qué familia de métodos conserva mejor valor, con métricas de calidad, coste físico, coste computacional, comunicación y significancia estadística.”

### 1.4 Título administrativo

1. **Primero comprobar el título exacto aprobado en Anexo I.** Si el tutor no autoriza cambio, usarlo tal cual en portada.
2. Título científico recomendado para portada si se permite refinamiento:

> **Coordinación distribuida acoplada de múltiples AMR para el transporte cooperativo de cargas heterogéneas**

3. Subtítulo interno opcional:

> **Dinámicas poblacionales, mercados wrench, Nash seeking y validación por escalera experimental SP1–SP9**

---

## 2. SP definitivos y narrativa progresiva

### 2.1 Códigos SP inmutables

| SP | Nombre final en memoria | Eje narrativo | Estado | Acción Codex |
|---:|---|---|---|---|
| SP0 | Infraestructura experimental y trazabilidad | Comparabilidad, seeds, métricas, auditorías | Metodológico | Documentar, no tratar como experimento de resultados |
| SP1 | Reclutamiento por quórum | Una carga pide robots | Cerrado | Usar resultados canónicos |
| SP2 | Capacidad efectiva heterogénea | Una carga no pide robots; pide capacidad | Cerrado | Usar resultados canónicos + conectar con teoría de potencial |
| SP3 | Llave/wrench y geometría | La capacidad escalar no basta; se requiere fuerza+par | Cerrado, central | Dar máxima visibilidad; figura estrella |
| SP4 | Movimiento y llegada segura | Una asignación debe poder ejecutarse | Cerrado | Usar trade-offs llegada/energía/colisión |
| SP5 | Transporte cooperativo con obstáculos y formación | La carga se mueve manteniendo formación | Cerrado | Separar cargo/caging/push según `transport_mode` |
| SP6 | Robustez operativa | Fallos, batería, cargas inviables, recuperación | Cerrado | Conservar matices y resultados negativos |
| SP7 | Grafo endógeno y comunicación | Radio, pérdidas, retardos, conectividad temporal λ₂ | Cerrado | Reencuadrar como topología dependiente del estado |
| SP8 | Escala e intratabilidad | Nada sirve si no escala | Cerrado | Mantener como argumento industrial fuerte |
| SP9 | Brecha teoría→CoppeliaSim/Pioneer | La teoría se mide contra robots simulados de mayor fidelidad | Nuevo condicionado | Implementar y ejecutar si hay entorno; no inventar |

### 2.2 Escalera narrativa obligatoria

Usar esta progresión en Introducción, Metodología, inicio de Resultados y Defensa:

```text
SP1: Una carga pide robots.
SP2: Una carga no pide robots; pide capacidad efectiva.
SP3: Una carga no pide solo capacidad; pide fuerza y par.
SP4: Fuerza y par no sirven si los robots no llegan.
SP5: Llegar no basta si no se mantiene formación y se evitan obstáculos.
SP6: Formación y transporte no bastan si fallan robots, baterías o viabilidad.
SP7: Robustez no basta si depende de comunicación global perfecta.
SP8: Nada sirve industrialmente si no escala.
SP9: La teoría no está cerrada hasta medir la brecha con una plataforma robótica de mayor fidelidad.
```

---

## 3. Taxonomía de soluciones: resultado central

### 3.1 Familias al mismo nivel narrativo

Ninguna familia se presenta como “la” solución. Todas son lentes sobre el mismo problema.

| Familia | Métodos esperados | Rol narrativo |
|---|---|---|
| Clásicas locales | greedy, nearest, APF, direct-to-target | Baseline barato y honesto |
| Referencias centralizadas | Hungarian, MILP/oracle, MPC-CBF/reference | Cotas superiores, no desplegables a escala |
| Mercado/subasta | CBBA, capacity market, wrench market, hierarchical market | Asignación por precios/déficit |
| Dinámicas poblacionales | Smith, Smith-QR, replicator, logit, Brown/BNN | Revisión distribuida interpretable |
| Primal-dual / Nash seeking | primal-dual capacity/wrench, tensor-game, vGNE explícito | Equilibrio bajo restricciones compartidas |
| Aprendidas | MAPPO-CTDE, imitation, neural scorer | Contraste data-driven y coste de aprender |
| Control/safety | CBF/HOCBF, vGNE-CBF, Hamiltonian cargo, tensor-flow | Ejecución física y seguridad |
| Oráculos | oracle, resilient oracle, wrench oracle, time-expanded CBF | Techo experimental, no implementación realista |

### 3.2 Entregable obligatorio A3 — matriz método×SP

Crear:

```text
scripts/generate_method_matrix.py
docs/generated/method_matrix.csv
docs/generated/method_matrix.tex
docs/generated/regime_map.csv
docs/generated/regime_map.tex
```

**Entrada:**

```text
results/sp*/<campaign_canónica>/tables/performance_ranking.csv
src/viu_mrob_tfm/experiments/registry.py
METHOD_META, si existe
```

**Salida:**

1. Matriz familias × SP1–SP9 con celdas:
   - `✓` = familia evaluada;
   - `—` = no aplica/no evaluada;
   - `★` = mejor de su familia en ese SP según métrica primaria;
   - `†` = referencia/oráculo no desplegable;
   - `!` = resultado negativo relevante.
2. Mapa de regímenes:

| Restricción dominante | Familia que conserva valor | Evidencia mínima |
|---|---|---|
| Quórum entero | Poblacional+QR / referencias centralizadas | SP1, métrica primaria, Δ, p-Holm |
| Heterogeneidad | Payoff marginal / capacity-aware | SP2 |
| Wrench vectorial | Métodos con verificación explícita de contactos/wrench | SP3 |
| Seguridad local | CBF/reference sobre asignador | SP4–SP5 |
| Fallos y batería | guarded/recovery-aware/wrench-market | SP6 |
| Comunicación degradada | connectivity-aware/relay/λ₂-aware | SP7 |
| Escala | distribuidas/jerárquicas/mean-field-like | SP8 |
| Física de mayor fidelidad | teoría-vs-medido + control explícito | SP9 si existe |

**DoD:**

- El script falla con error claro si falta un `performance_ranking.csv` canónico.
- El `.tex` compila sin edición manual.
- Cada `★` incluye métrica y ranking asociado.
- No usar SP9 si no tiene resultados promovidos.

---

## 4. Teoría que debe quedar en el TFM

### 4.1 Reglas de integración teórica

1. En el cuerpo se enuncian resultados y se explica su rol experimental.
2. En Anexo A se dejan demostraciones compactas.
3. No insertar manuscritos completos.
4. No inventar teoremas nuevos.
5. Toda notación debe coincidir entre cuerpo, anexo, código y figuras.

### 4.2 Resultados propios permitidos

| ID | Resultado | Destino en memoria | Validación/figura |
|---|---|---|---|
| T1 | NE cerrado del juego cuadrático de transporte y residuo de free-riding | Cap. 5.3 + Anexo A | figura PoA / discusión NE vs vGNE |
| T2 | PoA exacto y cota \((N+1)^2/(4N)\) | Cap. 5.3 | `fig_v2_poa_curve` |
| T3 | vGNE = pseudoinversa ponderada; reparto proporcional a salud \(\eta_i\) | Cap. 5.4 | `fig_v1_share_vs_theory` |
| T4 | Tasa \(\rho_L=\sqrt{k_p}\), condición Nash seeking \(c\lambda_2\mu>\vartheta^2\), discretización | Cap. 5.5 | `fig_v3_stability_boundary` |
| T5 | Cotas operativas: \(N_{min}\), deriva de batería, ISS ante CBF | Cap. 5.5 | SP6/SP9 discusión |
| T6 | Ascenso de potencial Smith y cierre entero aproximado | Cap. 5.2 + Anexo A | SP1/SP2 |
| T7 | Déficit de capacidad y residual wrench como distancia a conjunto admisible | Cap. 5.1–5.2 | SP3 figura estrella |
| T8 | Ley explícita sensor→motor de 9 pasos | Cap. 5.6 + SP9 | tabla pipeline |
| T9 | Comparación de dinámicas de revisión bajo el mismo payoff de déficit | Cap. 5.2bis | matriz método×SP y SP1/SP2/SP7 |

### 4.3 Teoría de literatura: citar, no reclamar

Actualizar `references.bib` y Cap. 4 con estas familias:

- MRTA/coaliciones: Gerkey & Matarić; Korsah; Choi–Brunet–How/CBBA.
- Juegos poblacionales: Sandholm; Quijano et al.; Barreiro-Gómez & Quijano; Martínez-Piazuelo et al.
- GNEP/VI: Facchinei & Kanzow; Facchinei & Pang.
- Nash seeking distribuido: Gadjov & Pavel; Yi & Pavel; Koshal–Nedić–Shanbhag.
- CBF/HOCBF: Ames; Xiao & Belta; Wang–Ames–Egerstedt.
- Consenso dinámico: Kia et al.
- Transporte cooperativo: Tuci; Farivarnejad & Berman; Feinerman.
- Cooperative game theory en asignación de actuadores: usar Wu et al. solo como antecedente periférico de reparto cooperativo de esfuerzo, no como analogía central de AMR.
- MFG/mean-field: solo ½ página de perspectiva futura.

---

## 5. Experimentos y scripts

### 5.1 No tocar SP1–SP8 high-power

SP1–SP8 quedan congelados. Codex puede leer, resumir, graficar y convertir. No puede reoptimizar resultados para hacerlos “bonitos”.

**Prohibido:**

```text
python scripts/run_sp1_experiment.py --high-power
python scripts/run_sp2_experiment.py --high-power
...
python scripts/run_sp8_experiment.py --high-power
```

**Permitido:**

```text
make test
make reproduce-figures
python scripts/run_spX_experiment.py --config configs/experiments/spX/SPX_DEBUG_smoke.yaml
```

Solo si un test rompe tras limpieza.

### 5.2 A2 — validación cuantitativa de teoría

Crear/ajustar:

```text
scripts/validate_theory_vgne_share.py
scripts/validate_theory_poa.py
scripts/validate_theory_stability.py
scripts/build_theory_validation_report.py
results/theory_validation/manifest.json
results/theory_validation/tables/*.csv
results/theory_validation/figures/*.png
results/theory_validation/figures/*.pdf
```

#### V1 — reparto vGNE vs teoría

Pregunta: ¿el reparto medido sigue \(\eta_i/H\)?

Entradas:

```text
control/explicit_law.py::vgne_force_share
v2_7_theory_* si existe
seeds fijas
```

Métricas:

```text
RMSE share
max_abs_error
corr Pearson/Spearman
violaciones de saturación
```

Figura:

```text
fig_v1_share_vs_theory.png/pdf
```

#### V2 — PoA medido vs curva cerrada

Barrido:

```text
gamma in logspace(-2, 2, 80)
N in {2,3,4,5,6}
```

Salida:

```text
fig_v2_poa_curve.png/pdf
poa_validation.csv
```

DoD:

- Curva teórica y puntos medidos superpuestos.
- Pico en \(\gamma=1\) marcado.
- RMSE por N reportado.

#### V3 — frontera de estabilidad Nash seeking

Barrido:

```text
c_gain
lambda2
mu
theta
Ts
```

Salida:

```text
fig_v3_stability_boundary.png/pdf
stability_boundary.csv
```

DoD:

- Clasificación estable/inestable.
- Frontera teórica \(c\lambda_2\mu=\vartheta^2\) dibujada.
- Falsos positivos/falsos negativos reportados.

### 5.3 A1 — SP9 CoppeliaSim gap study

SP9 no es “validar Smith-QR”. SP9 es medir la brecha teoría→implementación con al menos tres familias.

#### Archivos a crear

```text
configs/experiments/sp9/SP9_COPPELIA_gap_study.yaml
scripts/run_sp9_experiment.py
scripts/postprocess_sp9_gap_study.py
scripts/extract_sp9_keyframes.py
scripts/build_sp9_video_catalog.py
src/viu_mrob_tfm/coppelia/__init__.py
src/viu_mrob_tfm/coppelia/remote_api.py
src/viu_mrob_tfm/coppelia/scene_loader.py
src/viu_mrob_tfm/coppelia/controller_loop.py
src/viu_mrob_tfm/coppelia/metrics.py
tests/test_sp9_config.py
tests/test_sp9_metrics.py
tests/test_sp9_theory_predictions.py
```

#### Escenarios base

Usar escenas existentes como semilla:

```text
coppeliasim/scenes/nominal_smith_qr.yaml/.lua
coppeliasim/scenes/robot_failure_smith_qr.yaml/.lua
coppeliasim/scenes/human_crossing_smith_qr.yaml/.lua
coppeliasim/scenes/comm_r3_smith_qr.yaml/.lua
coppeliasim/scenes/sensor_degraded_smith_qr.yaml/.lua
```

Generar variantes por método:

```text
smith_qr
replicator
ours_primal_dual_wrench_or_vgne
```

Si la implementación de una familia no existe en Coppelia, crear adaptador y fallback explícito. No reportar fallback como ejecución real si no corre.

#### Diseño mínimo

Ideal:

```text
5 escenarios × 3 métodos × 10 semillas = 150 ejecuciones
```

Mínimo defendible:

```text
3 escenarios × 3 métodos × 5 semillas = 45 ejecuciones
```

Quality gate:

- Si no hay CoppeliaSim/API ZMQ disponible, producir scripts/configs/tests dry-run y marcar `SP9_STATUS=PENDING_RUNTIME`.
- Si solo hay una o dos corridas manuales, usarlas como demostración visual, no como capítulo estadístico.
- Si hay CSV completos con seeds, reportar SP9 como estudio de brecha.

#### Métricas SP9

Por ejecución:

```text
scenario
method
seed
success
final_pose_error_m
final_yaw_error_rad
transport_time_s
collision_count
min_clearance_m
formation_break_count
energy_proxy_J
message_count
control_loop_hz_mean
control_loop_hz_std
api_delay_ms_mean
api_delay_ms_p95
motor_saturation_fraction
sensor_false_echo_count
caging_slip_events
```

Predicho-vs-medido:

```text
rho_L_pred = sqrt(kp)
rho_L_measured
share_pred_eta_over_H
share_measured
Nmin_pred
N_used
CBF_clearance_pred
min_clearance_measured
consensus_time_pred = 1/(c * lambda2)
consensus_time_measured
```

Causas de brecha por ablación:

```text
ideal_sensor vs real_sensor
ideal_contact vs corner_contact
ideal_motor vs motor_deadband_saturation
zero_delay vs api_delay_Ts
ideal_caging vs friction_slip
```

Figura obligatoria:

```text
fig_sp9_gap_causes.png/pdf
```

Tabla obligatoria:

```text
sp9_predicted_vs_measured.csv
```

#### Redacción segura SP9

Permitido:

> “SP9 caracteriza la brecha entre fórmulas cerradas y ejecución en simulador físico con Pioneer 3-DX bajo sensores, saturaciones y retardos.”

Prohibido:

> “SP9 valida el sistema en hardware/entorno industrial.”

---

## 6. Estadística robusta y Monte Carlo

### 6.1 SP1–SP8

Usar los CSV existentes:

```text
results/sp*/<campaign>/tables/hypothesis_results.csv
results/sp*/<campaign>/tables/performance_ranking.csv
results/sp*/<campaign>/tables/summary.csv
```

No recalcular salvo que falte una tabla para el anexo consolidado. Si se recalcula, debe coincidir con los CSV canónicos.

### 6.2 SP9 y nuevas validaciones

Para SP9 y V1–V3, implementar estadísticas pre-registradas en YAML:

```yaml
statistics:
  paired: true
  primary_metric: success_or_gap_metric
  omnibus: friedman
  pairwise: wilcoxon_signed_rank
  correction: holm
  effect_sizes:
    - cohen_dz
    - rank_biserial
  confidence_intervals:
    method: bootstrap
    level: 0.95
    n_boot: 10000
  report_negative_results: true
```

### 6.3 Script de anexo estadístico

Crear:

```text
scripts/build_stats_annex.py
docs/generated/stats_master_table.csv
docs/generated/stats_master_table.tex
```

La tabla debe incluir:

```text
SP
hipótesis
comparación
métrica primaria
n
media/mediana método A
media/mediana método B
Δ
p_raw
p_Holm
effect_size
effect_CI95
veredicto
claim_id
```

DoD:

- Ninguna hipótesis queda sin n, p-Holm y efecto si tiene CSV.
- Resultados no significativos se reportan como “no se rechaza H0”, no se esconden.
- El texto nunca dice “mejor” sin régimen, métrica y evidencia.

---

## 7. Figuras, TikZ, plots, capturas y vídeos

### 7.1 Manifiesto de figuras

Crear:

```text
docs/generated/figure_manifest.csv
scripts/build_figure_manifest.py
```

Columnas:

```text
figure_id
section
caption_es
source_script
source_data
output_png
output_pdf_or_tex
claim_id
status
```

DoD:

- Toda figura del TFM aparece en el manifiesto.
- Toda figura usada se cita en el texto.
- Toda figura tiene fuente de datos o se etiqueta como esquema conceptual.

### 7.2 Figuras obligatorias del TFM

| ID | Figura | Fuente | Sección |
|---|---|---|---|
| F0 | Pipeline narrativo SP1→SP9 | TikZ | Introducción/Metodología |
| F1 | Matriz familia×SP | `generate_method_matrix.py` | Metodología/Resultados |
| F2 | Mapa de regímenes | `generate_regime_map.py` | Conclusiones |
| F3 | SP3 falso positivo escalar vs wrench factible | resultados SP3 + TikZ | Resultados SP3 |
| F4 | PoA teórico vs medido | V2 | Cap. 5 |
| F5 | Reparto vGNE \(\eta_i/H\) | V1 | Cap. 5 |
| F6 | Frontera estabilidad Nash seeking | V3 | Cap. 5/SP7 |
| F7 | Pareto calidad-recursos SP1/SP2/SP8 | resultados canónicos | Resultados |
| F8 | Comunicación: radio/λ₂ vs performance | SP7 | Resultados SP7 |
| F9 | Escala: runtime/timeout/completion | SP8 | Resultados SP8 |
| F10 | SP9 predicho-vs-medido | SP9 | Cap. 7 si existe |
| F11 | SP9 degradación por causa | SP9 | Cap. 7 si existe |

### 7.3 Reglas visuales

1. Exportar `.png` 300 dpi y `.pdf` vectorial cuando sea posible.
2. Etiquetas en español, con unidades.
3. No usar nombres crípticos de métodos en ejes. Crear mapping limpio:

```text
ours_smith_qr -> Smith-QR
ours_primal_dual_wrench -> Primal-dual wrench
mappo_ctde -> MAPPO-CTDE
reference_time_expanded_cbf -> Ref. CBF temporal
```

4. Captions deben explicar qué prueba la figura, no solo describirla.
5. Si una figura es conceptual/TikZ, debe decir “Elaboración propia”.
6. Si una figura usa datos, caption debe incluir campaña y métrica.

### 7.4 Vídeos y keyframes

No meter vídeos pesados en el PDF. Crear catálogo:

```text
results/VIDEO_CATALOG.md
results/video_catalog.csv
scripts/build_video_catalog.py
scripts/extract_keyframes.py
```

Columnas:

```text
video_id
SP
scenario
method
seed
path_local
sha256
duration_s
fps
keyframe_paths
used_in_doc
caption
```

Para documento:

- Usar solo keyframes/capturas.
- 4 fotogramas por escenario SP9 máximo.
- Elegir 8–12 vídeos clave para release/suplemento.
- No subir raw pesados al TFM ni al release principal.

---

## 8. Limpieza y reparación del repositorio

### 8.1 Objetivo

Que un entorno limpio pueda ejecutar:

```bash
pip install -e .
make test
make method-matrix
make theory-validation
make reproduce-figures
make thesis
```

### 8.2 Consolidación de duplicados

Acción conservadora: archivar, no borrar agresivamente.

| Duplicado | Decisión | DoD |
|---|---|---|
| `src/viu_mrob_tfm/simulations/` vs `simulation/` | `simulations/` vivo; legacy a `_archive/` si no lo importan SP canónicos | `grep` sin imports legacy |
| `src/viu_mrob_tfm/control/` vs `controllers/` | `control/` vivo para `explicit_law.py`, `wrench.py`; revisar `controllers/` antes de archivar | tests verdes |
| `output/` vs `outputs/` | dejar `outputs/`; `output/` a `_archive/` o `.gitignore` | rutas actualizadas |
| `tmp/`, debug, smoke results | mantener local; excluir release | manifest de limpieza |

Comandos de comprobación:

```bash
grep -R "from viu_mrob_tfm.simulation " src scripts tests || true
grep -R "import viu_mrob_tfm.simulation" src scripts tests || true
pytest -q
python -m compileall src scripts
```

### 8.3 Entorno

Crear/actualizar:

```text
requirements.lock
pyproject.toml
.env.example
REPRODUCIBILITY.md
```

Registrar:

```text
python_version
platform
pip_freeze_hash
git_commit
canonical_results_hash
```

### 8.4 Makefile targets

Agregar o corregir:

```makefile
.PHONY: test method-matrix theory-validation figures-paper reproduce-figures sp9 thesis stats-annex video-catalog clean-check

test:
	pytest -q

method-matrix:
	python scripts/generate_method_matrix.py

theory-validation:
	python scripts/validate_theory_vgne_share.py
	python scripts/validate_theory_poa.py
	python scripts/validate_theory_stability.py
	python scripts/build_theory_validation_report.py

stats-annex:
	python scripts/build_stats_annex.py

figures-paper:
	python scripts/generate_paper_figures.py
	python scripts/build_figure_manifest.py

video-catalog:
	python scripts/build_video_catalog.py

sp9:
	python scripts/run_sp9_experiment.py --config configs/experiments/sp9/SP9_COPPELIA_gap_study.yaml
	python scripts/postprocess_sp9_gap_study.py

thesis:
	cd docs/doc-05-final-report && latexmk -pdf main.tex

reproduce-figures: method-matrix theory-validation stats-annex figures-paper video-catalog
```

Si `latexmk` no está disponible, documentar alternativa exacta usada.

### 8.5 Release académico

Antes de depósito:

```text
GitHub release v1.0-tfm-submit
Zenodo DOI
```

Excluir:

```text
raw videos pesados
runs debug
caches
__pycache__
.ipynb_checkpoints
tmp
```

Incluir:

```text
source code
configs
canonical reports
compressed figures
CSV tables
README reproduce
ROADMAP.md
CLAIM_LEDGER.md
CANONICAL_RESULTS.md
VIDEO_CATALOG.md
```

---

## 9. Documento final

### 9.1 Restricciones VIU

- Cuerpo principal: **50–80 páginas**.
- Anexos oficiales: **máximo 20 páginas**.
- Resultados, análisis y validación deben ser el bloque dominante del trabajo.
- APA 7.
- Portada/estilos de plantilla VIU o equivalencia exacta en PDF.
- Índice de contenido, figuras, tablas y símbolos/acrónimos.

### 9.2 Presupuesto de páginas recomendado

| Bloque | Páginas objetivo | Comentario |
|---|---:|---|
| Portada, resumen, abstract, índices, nomenclatura | 5–7 | No cuenta como cuerpo principal si plantilla lo separa |
| 1. Introducción | 5–6 | Problema, brecha, frase-tesis, contribuciones |
| 2. Objetivos e hipótesis | 3–4 | O1–O6, H1–H9, test asociado |
| 3. Metodología | 5–6 | SP0, seeds, métricas, estadística, auditoría |
| 4. Marco teórico y estado del arte | 8–10 | MRTA, juegos poblacionales, GNEP, CBF, MARL |
| 5. Modelo y teoría del juego de llave | 9–11 | T1–T9 resumidos, figuras V1–V3 |
| 6. Resultados SP1–SP8 | 28–34 | Núcleo del TFM |
| 7. SP9 brecha teoría→implementación | 0–5 | Solo si hay resultados trazables |
| 8. Conclusiones, límites y futuro | 4–5 | Mapa de regímenes, O/H, límites |
| Anexos oficiales | ≤20 | Proofs compactas, reproducibilidad, tabla estadística grande |

### 9.3 Estructura final

```text
Portada
Resumen
Palabras clave
Abstract
Keywords
Índice de contenido
Índice de figuras
Índice de tablas
Símbolos, acrónimos y abreviaturas

1. Introducción
2. Objetivos e hipótesis
3. Metodología experimental y reproducibilidad
4. Marco teórico y estado del arte
5. Modelo físico-económico de coaliciones multi-AMR
6. Resultados y análisis: escalera SP1–SP8
7. Brecha teoría–implementación en CoppeliaSim/Pioneer (SP9, si procede)
8. Conclusiones, limitaciones y trabajo futuro
Referencias bibliográficas
Anexos
```

### 9.4 Capítulo 5 — estructura obligatoria

```text
5.1 Déficit como señal común: de quórum a capacidad y wrench
5.2 Dinámicas poblacionales y comparación de protocolos de revisión
5.2bis T9: Smith, Smith-QR, replicator, logit, Brown/BNN bajo el mismo payoff
5.3 NE cerrado, free-riding y PoA exacto
5.4 vGNE, pseudoinversa ponderada y precio dual
5.5 Nash seeking, λ₂, estabilidad, discretización y cotas operativas
5.6 Ley explícita sensor→motor de 9 pasos
```

### 9.5 Capítulo 6 — plantilla fija por SP

Cada SP ocupa 2–3 páginas y usa esta estructura exacta:

```text
6.x SPx — Título corto

Pregunta y eje narrativo.
Una frase que explique qué limitación del SP anterior tensiona.

Diseño experimental.
Escenarios, seeds, métodos comparados, referencia/oráculo, métrica primaria.

Métodos.
Familias evaluadas. Referencia a matriz método×SP.

Resultado principal.
Una figura principal y lectura explícita con cifras.

Contraste estadístico.
Tabla compacta: hipótesis, comparación, n, p-Holm, efecto, veredicto.

Lectura y límite.
Qué se confirma, qué no se confirma, qué abre el SP siguiente.

Claim seguro.
Una frase defendible.

No afirmar.
Una frase peligrosa que queda prohibida.
```

Ejemplo de `No afirmar`:

```text
SP3 no afirma manipulación 3D real ni contacto industrial completo; afirma insuficiencia de criterios escalares en simulación planar/quasi-static con geometría wrench.
```

### 9.6 Conclusiones

Las conclusiones deben cerrar con tres tablas:

1. **Objetivos → evidencia**

```text
Objetivo
SP/teoría que lo responde
Resultado clave
Limitación
```

2. **Hipótesis → veredicto**

```text
H
métrica primaria
test
p-Holm
efecto
veredicto
```

3. **Mapa de regímenes**

```text
restricción dominante
familia que conserva valor
evidencia
claim seguro
```

No cerrar con “ganó X”. Cerrar con:

> “La arquitectura demuestra que la formulación del déficit físico organiza la comparación: según la restricción dominante, cambian las familias que conservan valor.”

---

## 10. Redacción de claims y lenguaje seguro

### 10.1 Claims fuertes permitidos

- “Se formula el transporte cooperativo multi-AMR como asignación distribuida de capacidad física efectiva.”
- “SP3 muestra que cardinalidad y capacidad escalar son insuficientes cuando la demanda incluye fuerza y par.”
- “SP1–SP8 constituyen una escalera experimental reproducible y auditada.”
- “El mapa de regímenes resume qué familias conservan valor bajo distintas restricciones dominantes.”
- “La ley explícita sensor→motor traduce el vGNE y el filtro CBF a una secuencia programable.”
- “SP9, si se ejecuta, caracteriza la brecha entre predicciones cerradas y un simulador robótico de mayor fidelidad.”

### 10.2 Claims prohibidos o a degradar

| No escribir | Escribir |
|---|---|
| “Smith-QR es el mejor método.” | “Smith-QR es una variante poblacional interpretable y competitiva en ciertos regímenes.” |
| “Validación industrial.” | “Validación por simulación reproducible y, si procede, simulador físico CoppeliaSim.” |
| “Hardware real.” | “Pioneer 3-DX en CoppeliaSim mediante API ZMQ.” |
| “Wrench garantiza transporte real.” | “Wrench certifica factibilidad planar/quasi-static en la capa de asignación.” |
| “MAPPO es SOTA universal.” | “MAPPO-CTDE se usa como comparador aprendido con coste de entrenamiento e inferencia.” |
| “Nash seeking probado en toda la arquitectura.” | “Nash seeking se analiza y se valida en los módulos donde hay evidencia trazable.” |
| “Resultados concluyentes en Coppelia” sin CSV | “Escenas y scripts preparados; ejecución pendiente.” |

---

## 11. Tareas por fases para Codex

### Fase 0 — Auditoría inicial y bloqueo

**Objetivo:** conocer el estado real sin modificar evidencia.

Tareas:

```bash
ls
python -V
pip install -e .
pytest -q
make test
```

Leer:

```text
README.md
docs/CANONICAL_RESULTS.md
docs/CLAIM_LEDGER.md
docs/REPRODUCIBILITY.md
docs/VIU_GUIDELINES_ALIGNMENT.md
docs/doc-05-final-report/main.tex
results/PAPER_FIGURES_INDEX.md
```

Crear:

```text
docs/THESIS_NARRATIVE_LOCK.md
```

Debe contener:

```text
frase madre
SP1–SP9
familias de métodos
claims prohibidos
estructura final
estado SP9
```

DoD:

- `pytest` ejecutado o error documentado.
- `THESIS_NARRATIVE_LOCK.md` creado.
- Nada en `results/sp1`–`results/sp8` modificado.

### Fase 1 — Repo sano

Tareas:

1. Archivar duplicados legacy con `git mv`, no borrar si no es seguro.
2. Actualizar imports.
3. Añadir tests de no-regresión.
4. Congelar entorno.
5. Agregar targets Makefile.

DoD:

```bash
pip install -e .
pytest -q
python -m compileall src scripts
make method-matrix
```

### Fase 2 — Matriz método×SP y mapa de regímenes

Tareas:

1. Implementar `scripts/generate_method_matrix.py`.
2. Implementar `scripts/generate_regime_map.py` o integrarlo en el anterior.
3. Exportar `.csv` y `.tex`.
4. Insertar matriz en Cap. 3/6 y mapa en Conclusiones.

DoD:

- `docs/generated/method_matrix.tex` compila.
- `docs/generated/regime_map.tex` compila.
- Todas las familias tienen descripción y régimen.

### Fase 3 — Validación teórica V1–V3

Tareas:

1. Implementar V1, V2, V3.
2. Generar figuras PNG/PDF.
3. Crear reporte `results/theory_validation/report.md`.
4. Insertar figuras en Cap. 5.

DoD:

- Figuras con RMSE reportado.
- Manifest con seeds.
- Cap. 5 cita cada figura.

### Fase 4 — Figuras, estadísticas y anexos automáticos

Tareas:

1. `scripts/build_stats_annex.py`.
2. `scripts/build_figure_manifest.py`.
3. `scripts/generate_thesis_figures.py` si `generate_paper_figures.py` no cubre TFM.
4. Regenerar figuras problemáticas.

DoD:

- `docs/generated/stats_master_table.tex` existe.
- `docs/generated/figure_manifest.csv` existe.
- Figuras sin solapes.
- Captions en español.

### Fase 5 — Redacción piloto SP3

SP3 es el piloto porque concentra la idea central.

Tareas:

1. Redactar sección SP3 con plantilla fija.
2. Seleccionar figura estrella:
   - falso positivo escalar;
   - wrench residual;
   - support/margin;
   - cargo/caging si aplica.
3. Crear tabla estadística compacta.
4. Declarar límite seguro.

DoD:

- SP3 cabe en 2–3 páginas.
- Toda cifra viene de CSV.
- Tiene claim seguro y claim prohibido.

### Fase 6 — Redacción SP1–SP8

Orden de redacción recomendado:

```text
SP3 → SP8 → SP6 → SP7 → SP5 → SP4 → SP2 → SP1
```

Orden final en memoria:

```text
SP1 → SP2 → SP3 → SP4 → SP5 → SP6 → SP7 → SP8
```

DoD por SP:

- Pregunta/eje.
- Diseño.
- Métodos.
- Figura.
- Tabla estadística.
- Lectura.
- Límite.
- Claim seguro/no afirmar.

### Fase 7 — SP9

Tareas:

1. Crear config SP9.
2. Crear interfaz Coppelia.
3. Ejecutar dry-run de config sin simulator.
4. Ejecutar real si entorno disponible.
5. Postprocesar.
6. Generar keyframes y vídeos.
7. Redactar Cap. 7 solo si hay evidencia.

DoD para SP9 cerrado:

```text
results/sp9/<campaign>/report.md
results/sp9/<campaign>/manifest.json
results/sp9/<campaign>/tables/sp9_runs.csv
results/sp9/<campaign>/tables/sp9_predicted_vs_measured.csv
results/sp9/<campaign>/figures/fig_sp9_gap_causes.png/pdf
results/sp9/<campaign>/figures/keyframes/*.png
results/sp9/<campaign>/videos/video_index.csv
```

Si no se cumple:

- Cap. 7 se degrada a “integración preparada y protocolo de validación”.
- No meter estadísticas SP9.
- No decir validación.

### Fase 8 — Ensamblaje de memoria

Tareas:

1. Introducción.
2. Objetivos e hipótesis.
3. Metodología.
4. Marco teórico.
5. Cap. 5 teoría.
6. Cap. 6 resultados.
7. Cap. 7 SP9 si existe.
8. Conclusiones.
9. Referencias APA 7.
10. Índices y nomenclatura.

DoD:

- Sin `??` ni `TODO`.
- Todas las figuras citadas.
- Todas las tablas citadas.
- Referencias compilan.
- Longitud dentro de límites.

### Fase 9 — Pulido final submit-ready

Tareas:

```bash
make thesis
make test
make reproduce-figures
```

Revisar:

- Ortografía.
- Tildes.
- Coherencia AMR/AGV. Recomendación: usar AMR en cuerpo, aclarar equivalencia con AGV industrial al inicio si Anexo I usa AGV.
- “CoppeliaSim” bien escrito.
- “wrench/llave” definido una vez y usado consistentemente.
- No hay claims prohibidos.
- Anexos ≤20 páginas.

DoD:

```text
docs/doc-05-final-report/build/main.pdf
checklist_submit_ready.md
```

---

## 12. Checklist submit-ready

### Documento

- [ ] Título administrativo validado contra Anexo I o autorizado por tutor.
- [ ] Resumen 200–300 palabras con objetivo, método, resultados y conclusión.
- [ ] Abstract en inglés.
- [ ] 3–5 palabras clave en ES/EN.
- [ ] Índice de contenido.
- [ ] Índice de figuras.
- [ ] Índice de tablas.
- [ ] Nomenclatura: \(\gamma, \eta, \lambda_2, \mu, \vartheta, \rho_L, W(C), PoA\), Kendall’s W, p-Holm.
- [ ] Objetivos e hipótesis alineados con SP.
- [ ] Metodología incluye seeds, pareado, tests, Holm, effect sizes, auditorías.
- [ ] Resultados/análisis/validación es el bloque dominante.
- [ ] Cap. 5 no excede teoría necesaria.
- [ ] Cada SP tiene figura + tabla estadística + límite.
- [ ] Conclusión incluye mapa de regímenes.
- [ ] No hay narrativa de método campeón.
- [ ] Limitaciones explícitas.
- [ ] Trabajo futuro no se confunde con resultado.
- [ ] APA 7 consistente.
- [ ] Anexos ≤20 páginas.

### Repo

- [ ] `pip install -e .` funciona.
- [ ] `pytest -q` verde o fallos documentados y no críticos.
- [ ] `make method-matrix` funciona.
- [ ] `make theory-validation` funciona.
- [ ] `make reproduce-figures` funciona.
- [ ] `make thesis` funciona.
- [ ] `requirements.lock` existe.
- [ ] `docs/generated/` contiene tablas finales.
- [ ] `results/theory_validation/` existe.
- [ ] `results/sp9/` existe si SP9 se reporta como resultado.
- [ ] Vídeos pesados excluidos del release principal.
- [ ] `VIDEO_CATALOG.md` existe si hay vídeos.

### Claims

- [ ] Ningún “garantiza” fuera de teoremas T1–T9 o CBF formal.
- [ ] Ningún “industrial/hardware real” para Coppelia.
- [ ] Ningún “gana siempre”.
- [ ] Resultados negativos presentes.
- [ ] Cada cifra importante tiene CSV o figura fuente.

---

## 13. Anti-metas absolutas

Codex no debe:

1. Reescribir la tesis como paper doctoral de wrench-market completo.
2. Quitar SP6, SP7 o SP8 para hacer sitio a Coppelia.
3. Convertir SP9 en sustituto de SP8.
4. Añadir GNN/MFG/baselines nuevos.
5. Reentrenar MARL salvo que ya exista pipeline y sea smoke.
6. Cambiar métricas para hacer ganador a un método.
7. Ocultar p-values no significativos.
8. Borrar resultados canónicos.
9. Crear datos falsos.
10. Meter vídeos raw en la entrega.
11. Ignorar límites de páginas VIU.
12. Cambiar el título administrativo sin validación del tutor.

---

## 14. Orden de trabajo recomendado para máxima probabilidad de entrega

### Sprint P0 — imprescindible para predepósito

1. Bloquear narrativa (`THESIS_NARRATIVE_LOCK.md`).
2. Generar matriz método×SP.
3. Generar validación teórica V1–V3.
4. Redactar SP3 piloto.
5. Redactar SP1–SP8.
6. Redactar Cap. 5 compacto.
7. Montar conclusiones con mapa de regímenes.
8. Pulir formato VIU.

### Sprint P1 — muy valioso si cabe

1. SP9 mínimo real.
2. Keyframes/vídeos.
3. Tabla predicho-vs-medido.
4. Figura degradación por causa.

### Sprint P2 — solo si todo lo anterior está cerrado

1. Zenodo DOI.
2. Release público.
3. Figuras TikZ más finas.
4. Suplemento largo de manuscritos.

---

## 15. Criterio final de éxito

La memoria queda submit-ready cuando un tribunal pueda leerla y responder claramente:

1. ¿Cuál es el problema?  
   **Transporte cooperativo de cargas heterogéneas con AMR bajo restricciones físicas y distribuidas.**

2. ¿Qué aporta el TFM?  
   **Una formulación físico-económica de déficit/wrench, una comparación sistemática de familias y un mapa de regímenes.**

3. ¿Qué evidencia hay?  
   **SP1–SP8 reproducibles, auditados y estadísticamente contrastados; V1–V3 para teoría; SP9 si existe para brecha CoppeliaSim.**

4. ¿Qué no se afirma?  
   **No se afirma hardware, validación industrial, manipulación 3D completa ni método universalmente ganador.**

5. ¿Por qué merece nota máxima?  
   **Porque conecta teoría, simulación, estadística, control y reproducibilidad sin sobreclaiming, conservando resultados negativos y delimitando regímenes de validez.**
