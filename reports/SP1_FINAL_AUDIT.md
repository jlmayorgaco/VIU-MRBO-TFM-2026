# SP1 — Auditoría de evidencia previa al refactor final

**Checkpoint A.** Documento de sólo lectura: no se ha modificado ninguna fuente
científica, no se ha regenerado ninguna figura y no se ha lanzado ninguna
simulación.

Fecha de auditoría: 2026-08-18
Raíz de evidencia: `scripts/results/sp1_levels/`
Manifiestos: `Subdocuments/SP1/provenance/results/<nivel>/manifest.json`

---

## 0. Estado de integridad del dato bruto

Se verificó **byte a byte y por SHA-256** todo el `frozen_raw` declarado en los
manifiestos frente al disco.

| Nivel | Ficheros RAW declarados | Existen | SHA-256 coincide |
|---|---|---|---|
| `n1_v2` | 4 | 4 | 4 / 4 |
| `n2_v1` | 5 | 5 | 5 / 5 |
| `n3_v2` | 5 | 5 | 5 / 5 |
| `n4_v2` | 4 | 4 | 4 / 4 |
| `n4_v3` | 4 (por inventario) | 4 | manifiesto sin `bytes` |
| `n4_v4` | 2 (por inventario) | 2 | manifiesto sin `bytes` |

**Conclusión: la evidencia bruta de SP1 está íntegra y es reproducible.**

En `n3_v2`, `n4_v2`, `n4_v3` y `n4_v4` el manifiesto no registra el campo
`bytes` (sí el `sha256`, que coincide). Es una inconsistencia de esquema entre
generaciones de manifiesto, no una pérdida de dato.

### Aviso de repositorio (bloqueante para el checkpoint de commit)

`git status` reporta **25 491 ficheros borrados** en el árbol de trabajo, todos
bajo `results/` (24 480 de ellos en `results/sp0`). **Ninguno pertenece a
`scripts/results/sp1_levels/`**, que es donde reside la evidencia de SP1.

No he creado el commit-snapshot solicitado en el punto 1.6 del encargo. Hacerlo
ahora registraría esas 25 491 supresiones como cambio intencionado. Requiere
decisión explícita antes de continuar (ver §7).

---

## 1. Tabla maestra de trazabilidad

Se listan **todos** los resultados científicos que el capítulo SP1 actual
utiliza. `RAW` es relativo a `scripts/results/sp1_levels/`.

### N1 — representación

| Resultado usado en el capítulo | ID | RAW | Generador | Config | Semillas | Post-proceso | Figura | Reproducible | Necesario | Destino |
|---|---|---|---|---|---|---|---|---|---|---|
| Ahorro LSAP vs voraz 6,53 % [6,34–6,71] | N1.E1 | `n1_v2/raw/quality_runs.csv` (4 500) | `scripts/sp1_n1.py` | `sp1_n1_confirmatory_v2.yaml` | `world_seed` por celda | `processed/quality_scenario_summary.csv` | `n1_quality_scenarios.pdf` | Sí | **No** (control de implementación) | **Anexo** |
| Falsos positivos de factibilidad 0→38,0/72,0/92,3/97,7 % | N1.E4 | `n1_v2/raw/heterogeneity_runs.csv` (1 500) | `scripts/sp1_n1.py` | idem | 25 celdas × 60 | `heterogeneity_summary.csv`, `heterogeneity_severity.csv` | `n1_heterogeneity_boundary.pdf` | Sí | **Sí (principal N1)** | **Cuerpo (F3)** |
| Pendiente GEE β_CV = 8,58 [7,46–9,69] | N1.E4 | idem | idem | idem | idem | `heterogeneity_contrasts.csv` | idem | Sí | Sí, como apoyo | Cuerpo (1 cifra) |
| Auditoría MILP: 6/1 500 sin certificar, límite 5 s | N1.E4 | idem (`milp_*`) | idem | idem | idem | `heterogeneity_summary.csv` | — | Sí | Sí (limitación) | Cuerpo (limitaciones) |
| Escalado LSAP, exponente 2,40 [2,37–2,44] | N1.E2 | `n1_v2/raw/scaling_runs.csv` (630) | idem | idem | — | `scaling_summary.csv` | `n1_central_scaling.pdf` | Sí | No en cuerpo | **Anexo** |
| Recálculo tras retirada | N1.E3 | `n1_v2/raw/failure_runs.csv` (6 000) | idem | idem | — | `failure_summary.csv` | `n1_failure_recovery.pdf` | Sí | No (fuera de la pregunta SP1 final) | **Anexo** |
| LP-slot integral, `x*_LP ∈ {0,1}` (ec. 5b) | — | **NO EXISTE RAW** | — | — | — | — | — | **Teórico (TU)** | Sí | Cuerpo como teorema; ver §3 |

### N2 — atomicidad / composición

| Resultado | ID | RAW | Generador | Config | Post-proceso | Figura | Reproducible | Necesario | Destino |
|---|---|---|---|---|---|---|---|---|---|
| HiGHS vs enumeración: 750 mundos, acuerdo 100 %, error máx. 4,15·10⁻¹² m | N2.E1 | `n2_v1/raw/oracle_validation_runs.csv` (750) | `scripts/sp1_n2_confirmatory.py` | `sp1_n2_confirmatory_v1.yaml` | `oracle_summary.csv` | `n2_oracle_validation.pdf` | Sí | Sí, reducido | **Cuerpo (F4 panel A, inset)** |
| Límite homogéneo LSAP = MILP en 250/250 | N2.E1b | `n2_v1/raw/homogeneous_limit_runs.csv` (250) | idem | idem | — | — | Sí | Sí | Cuerpo (F3 panel A parcial) |
| LP fraccionario en 100 % de 1 500 mundos | N2.E2 | `n2_v1/raw/atomicity_runs.csv` (1 500) | idem | idem | `atomicity_summary.csv` | `n2_atomicity.pdf` | Sí | **Sí (principal N2)** | **Cuerpo (F4)** |
| Brecha de integralidad mediana 18,0 % [17,6–18,5], P95 35,4 % | N2.E2 | idem | idem | idem | idem | idem | Sí | Sí | Cuerpo |
| 45 mundos LP factible / MILP infactible | N2.E2 | idem (`lp_status`,`milp_status`) | idem | idem | idem | idem | Sí | **Sí (resultado clave)** | **Cuerpo (F4 panel C)** |
| Brecha 23,1 % con CV = 0 | N2.E2 | idem, filtro `capacity_cv=0.0` | idem | idem | idem | idem | Sí | **Sí (corrige la narrativa)** | Cuerpo |
| Certificación / censura bajo presupuesto | N2.E3 | `n2_v1/raw/phase_diagram_runs.csv` (1 800) | idem | idem | `phase_summary.csv` | `n2_phase_diagram.pdf` | Sí | Sí, secundario | **Cuerpo (F4 panel D)** |

### N3 — información

| Resultado | ID | RAW | Generador | Config | Post-proceso | Figura | Reproducible | Necesario | Destino |
|---|---|---|---|---|---|---|---|---|---|
| Factibilidad 75,8 / 99,8 / 100 % (CBBA-RB / GRAPE / Pair-GRAPE) | N3.E2 | `n3_v2/raw/e2_runs.csv` (3 600) | `scripts/sp1_n3_confirmatory.py` | `sp1_n3_confirmatory_v2.yaml` | `e2_summary.csv` | `n3_quality.pdf` | Sí | **Sí** | **Cuerpo (F5)** |
| Brechas en soporte común 40,3 / 20,9 / 9,4 % (n = 878) | N3.E2 | idem | idem | idem | idem | idem | Sí | **Sí** | **Cuerpo (F5)** |
| Bytes/AMR 9 089 / 20 909 / 25 791 | N3.E2 | idem (`bytes_per_agent`) | idem | idem | idem | idem | Sí | **Sí** | **Cuerpo (F5)** |
| Friedman Q = 1 166,7; p = 4,5·10⁻²⁵⁴; W = 0,664 | N3.E2 | idem | idem | idem | idem | idem | Sí | Sí, degradado | Cuerpo (sólo W) / **anexo** |
| Topología × conectividad, 5 regímenes | N3.E3 | `n3_v2/raw/e3_runs.csv` (4 500) | idem | idem | `e3_summary.csv` | `n3_locality.pdf` | Sí | **Sí** | **Cuerpo (F6)** |
| Partición permanente como control negativo | N3.E3 | idem, `graph_regime=partitioned` | idem | idem | idem | idem | Sí | **Sí** | **Cuerpo (F6 panel C)** |
| Oráculo: 1 200 mundos, 1 159 certificados, 41 infactibles | N3 | `n3_v2/raw/oracle_runs.csv` | idem | idem | — | — | Sí | Sí (denominadores) | Cuerpo |

### N4 — orden estratégico y ejecución

| Resultado | ID | RAW | Generador | Config | Post-proceso | Figura | Reproducible | Necesario | Destino |
|---|---|---|---|---|---|---|---|---|---|
| Brecha 55,7 → 14,8 → 3,2 % (BR/2BR/C3) | N4.E4 | `n4_v2/raw/e4_family_runs.csv` (12 000) | `scripts/sp1_n4_family.py` | `sp1_n4_family_v2.yaml` | `family_summary.csv` | `n4_family_comparison.pdf` | Sí | **Sí (principal N4)** | **Cuerpo (F7 panel A)** |
| C3 − BR = −49,2 puntos [−53,1; −45,9] | N4.E4 | idem | idem | idem | `paired_contrasts.csv` | idem | Sí | Sí | Cuerpo |
| Ablación CF vs DMIS+TX: +1 282 bytes/AMR [1 258–1 318] | N4.E4 | idem (`geo_qpg_cf` vs `geo_qpg_d`) | idem | idem | `paired_risk_differences.csv` | `n4_architecture_ablation.pdf` | Sí | **Sí** | **Cuerpo (F8)** |
| h_c\* bilateral en 1 156/1 200; trilateral 4; no hallado 40 | N4.E9 | `n4_v4/raw/e9_hstar_runs.csv` (2 400) | `scripts/sp1_n4_hstar.py` | `sp1_n4_hstar_v4.yaml` | `hstar_category_summary.csv` | `n4_hstar_distribution.pdf` | Sí | **Sí (mecanismo)** | **Cuerpo (F7 panels C/D)** |
| Sensibilidad de P(h_c\*>3) a N/K | N4.E9 | idem (`robots_per_load`) | idem | idem | idem | `n4_hstar_ratio_sensitivity.pdf` | Sí | Sí | **Cuerpo (F7 panel D)** |
| Traza representativa F-I | N4.E9 | `n4_v4/raw/e9_fi_representative_trace.csv` | idem | idem | `e9_fi_trace_endpoints.csv` | `n4_fi_representative_trace.pdf` | Sí | No (ilegible a tamaño de cuerpo) | **Anexo** |
| F-II: ranking cambia tras R en 74,8 %; enteras 96,1–96,8 % | N4.E7 | `n4_v3/raw/e7_cross_family_runs.csv` (16 800) | `scripts/sp1_n4_cross_family.py` | `sp1_n4_cross_family_v3.yaml` | `population_ranking_by_world.csv` | `n4_fii_continuous_atomic.pdf` | Sí | **Sí → se traslada a N3.B** | **Cuerpo §5.3** |
| F-III primal–dual vGNE: 91,9 % cruza criterio; 99,57 % / 9,04 % tras R | N4.E7 | idem | idem | idem | `cross_family_summary.csv` | `n4_fiii_residuals.pdf` | Sí | **Sí → se traslada a N3.B** | **Cuerpo §5.3** |
| Pareto transversal | N4.E7 | idem | idem | idem | idem | `n4_cross_family_pareto.pdf` | Sí | Sí | **Cuerpo (F9)** |
| DPOP exacto en pequeño | N4.E5 | `n4_v2/raw/e5_dpop_runs.csv` | `sp1_n4_family.py` | idem | `dpop_summary.csv` | `n4_dpop_exactness.pdf` | Sí | Compacto | **Anexo + 1 frase** |
| Escalado N4 | N4.E6 | `n4_v2/raw/e6_scaling_runs.csv` | idem | idem | `scaling_summary.csv` | `n4_scaling.pdf` | Sí | No en cuerpo | **Anexo** |
| F-IV temporal: 95,6 % vs 97,8 % servicio | N4.E8 | `n4_v3/raw/e8_dynamic_runs.csv`, `e8_dynamic_history.csv` | `sp1_n4_cross_family.py` | idem | — | `n4_fiv_dynamic.pdf` | Sí | **No (oráculo con información futura)** | **Anexo / trabajo futuro** |

---

## 2. Hallazgo mayor: existen métodos ya ejecutados que el capítulo no reporta

El barrido completo de `n4_v2/raw/e4_family_runs.csv` (12 000 filas, 10 métodos
× 1 200) revela dos variantes ejecutadas y **nunca reportadas** en el capítulo:

| Método en RAW | n | ¿Reportado hoy? | Relevancia para el contrato final |
|---|---|---|---|
| `geo_qpg_lll` | 1 200 | No | **Rama LLL de N3.B ya ejecutada a h = 1** |
| `geo_qpg_smith` | 1 200 | No | Variante Smith discreta a h = 1 |
| `geo_qpg_u` (BR) | 1 200 | Sí | Rama BR de N3.B |
| `geo_qpg_p` (2BR) | 1 200 | Sí | Orden estratégico |
| `geo_qpg_c3` | 1 200 | Sí | Orden estratégico |
| `geo_qpg_cf` | 1 200 | Sí | Confirmación central |
| `geo_qpg_d` (DMIS+TX) | 1 200 | Sí | Confirmación distribuida |

Esto **reduce el alcance de la campaña nueva #1** (ver §4).

---

## 3. Mapa figura solicitada → ¿producible desde RAW?

| Figura | Panel | Dato requerido | Fuente RAW | Veredicto |
|---|---|---|---|---|
| **F1** escalera | — | ninguno (diagrama) | — | **Rehacer en TikZ** |
| **F2** escenarios | — | geometrías sintéticas | `fig03_scenarios.tex` | **Reusar/compactar** |
| **F3** N1 | A: LP-slot vs LSAP vs MILP | `lp_objective` del modelo por puestos | **NO EXISTE** | **Falta** — ver §3.1 |
| | B: CV × 5 escenarios × falso positivo | `heterogeneity_runs.csv`: 25 celdas × 60 | ✔ completo | **RE-PLOT** |
| | C: severidad del déficit | `hungarian_relative_deficit`, `..._total_shortfall_kg` | ✔ | **RE-PLOT** |
| **F4** N2 | A: HiGHS vs enumeración | `oracle_validation_runs.csv` | ✔ | **RE-PLOT** |
| | B: heatmap CV × ρ brecha | `atomicity_runs.csv`: CV(5) × ρ(2) × 150 | ✔ (ρ sólo 2 niveles) | **RE-PLOT** |
| | C: heatmap P(LP factible ∧ MILP infactible) | `lp_status`/`milp_status` | ✔ | **RE-PLOT** |
| | D: certificación bajo presupuesto | `phase_diagram_runs.csv` | ✔ | **RE-PLOT** |
| **F5** N3.A Pareto | — | bytes/AMR, brecha, factibilidad, soporte común | `e2_runs.csv` | ✔ | **RE-PLOT** |
| **F6** N3.C topología | A/B/C | `graph_regime` ∈ {complete, dense, medium, threshold, **partitioned**} | `e3_runs.csv` (4 500) | ✔ | **RE-PLOT** |
| **F7** N4 orden | A: brecha por h | `e4_family_runs.csv` **y** `gap_br/gap_2br/gap_c3` en `e9` | ✔ (doble fuente) | **RE-PLOT** |
| | B: riesgo de infactibilidad | `feasible`, `raw_certificate` | ✔ | **RE-PLOT** |
| | C: distribución de h_c\* | `hstar_order`, `hstar_category`, `searched_through` | ✔ | **RE-PLOT** |
| | D: sensibilidad a CV, ρ, N/K | `capacity_cv`, `pressure`, `robots_per_load` | ✔ | **RE-PLOT** |
| **F8** CF vs DMIS+TX | todos | `geo_qpg_cf` vs `geo_qpg_d`, `arbitration_messages`, `transaction_messages`, `transaction_aborts`, `mis_iterations` | `e4_family_runs.csv` | ✔ | **RE-PLOT** |
| **F9** Pareto final | — | 14 métodos + cierre R | `e7_cross_family_runs.csv` (16 800) | ✔ salvo métodos nuevos | **RE-PLOT tras campañas** |

### 3.1 Única laguna real en las figuras existentes

**F3 panel A** pide comparar el óptimo del **LP relajado de la formulación por
puestos** con LSAP y con MILP bajo capacidad homogénea.

`homogeneous_limit_runs.csv` (250 mundos) contiene `lsap_cost` y
`milp_objective` pero **no** el óptimo del LP relajado: nunca se resolvió.

Esto **no requiere una campaña nueva**. Los 250 mundos están definidos por
`world_seed` y son regenerables de forma determinista. Es una **re-análisis**:
regenerar el mundo, montar la matriz por puestos, resolver la relajación
continua y registrar `lp_objective`. Coste estimado: minutos.

Alternativa admisible: no incluir el panel A y presentar la integralidad como lo
que es —un resultado formal por unimodularidad total—, sin validación empírica.
Recomiendo hacer el re-análisis: convierte una afirmación teórica en una
verificación estructural barata.

---

## 4. ¿Se pueden reducir las campañas nuevas propuestas?

### Campaña #1 — N3.B revisión × fitness: **SÍ, se reduce sustancialmente**

Diseño pedido: 3 protocolos (BR, ASR, LLL) × 3 fitness (F0, F1, F2) = 9
configuraciones discretas, más rama continua, más comparador primal–dual.

Estado real de la evidencia:

| Componente pedido | ¿Existe? | Dónde |
|---|---|---|
| BR con fitness marginal (≈F2) | **Sí**, 1 200 mundos | `e4_family_runs.csv`, `geo_qpg_u` |
| LLL con fitness marginal (≈F2) | **Sí**, 1 200 mundos | `e4_family_runs.csv`, `geo_qpg_lll` |
| Smith discreto | **Sí**, 1 200 mundos | `e4_family_runs.csv`, `geo_qpg_smith` |
| ASR (cualquier fitness) | **No** | — |
| Fitness F0 (sólo distancia) | **No** | — |
| Fitness F1 (déficit + distancia) | **No** | — |
| Rama continua Replicator/Smith/BNN/Logit + R | **Sí**, 1 200 c/u | `e7_cross_family_runs.csv` |
| Primal–dual vGNE (central y distribuido) + R | **Sí**, 1 200 c/u | `e7_cross_family_runs.csv` |
| Cambios de ranking inducidos por R | **Sí** | `population_ranking_by_world.csv` |

**De las 9 celdas discretas, 2 ya existen** (BR×F2, LLL×F2) sobre 1 200 mundos,
con 5 escenarios, CV ∈ {0; 0,35; 0,65; 1,0} y ρ ∈ {0,70; 0,85}.
**La rama continua y el comparador dual están completos y no requieren
re-ejecución.**

Lo genuinamente ausente es **el factor *fitness*** (F0 y F1) y **el protocolo
ASR**. Es decir: 3 protocolos × 2 fitness nuevos (6 celdas) + ASR × F2 (1
celda) = **7 celdas**, no 9 + continuo + dual.

Reducción recomendada:

- ejecutar sólo la rama discreta faltante;
- reutilizar la rama continua y el primal–dual ya congelados, declarando
  explícitamente que proceden de la campaña `n4_v3` y bajo qué contrato;
- **advertencia de comparabilidad**: `e4_family_runs` usa 5 escenarios y
  `e7_cross_family` los mismos 5, pero son campañas distintas con `campaign_id`
  distinto. Mezclar celdas viejas y nuevas en un mismo panel exige o bien
  re-ejecutar las 2 celdas existentes bajo el nuevo banco held-out, o bien
  declarar el panel como comparación entre campañas. **Recomiendo re-ejecutar
  las 9 celdas discretas sobre el banco held-out nuevo** para que el factorial
  sea limpio, y usar las celdas existentes sólo como comprobación de coherencia.

Esto último matiza la reducción: el ahorro real y seguro está en **no repetir la
rama continua ni el primal–dual**, que es la parte más cara.

### Campaña #2 — N4 held-out industrial: **NO se puede reducir**

Búsqueda exhaustiva de `warehouse`, `aisle`, `cross_aisle`, `dock`,
`industrial`, `holdout` en todos los CSV de `sp1_levels`: **cero coincidencias**.

Los escenarios existentes son exclusivamente los cinco sintéticos
(`uniform`, `clustered`, `separated`, `ring`, `corridor`).

Además, los regímenes pedidos (R1/R2/R3 con N/K ∈ {4, 3, 2}) sólo están
parcialmente cubiertos: `e9_hstar_runs.csv` tiene N/K ∈ {2; 3; 3,2; 4} pero
únicamente sobre geometría sintética y sólo para el diagnóstico h_c\*.

**La campaña industrial es necesaria en su totalidad**, incluidas las cuatro
familias de layout y el generador determinista. Es la única evidencia que puede
sostener H-N4.E.

---

## 5. Elementos de infraestructura localizados

| Elemento | Ruta | Estado |
|---|---|---|
| Fuente LaTeX SP1 | `Subdocuments/SP1/sp1.tex` (1 244 líneas) | Compila, 25 pág. |
| Macros generadas | `generated/metrics.tex` (317), `n4_v3_*`, `n4_v4_*` | OK |
| Script de compilación | `Subdocuments/SP1/build.ps1` | LuaLaTeX + Biber |
| Bibliografía | `references.bib` (111 entradas); 15 citadas por SP1 | OK |
| Configs | `experiments/configs/sp1_*.yaml` (20) | OK |
| Generadores | `scripts/sp1_n1.py`, `sp1_n2_confirmatory.py`, `sp1_n3_confirmatory.py`, `sp1_n4_family.py`, `sp1_n4_cross_family.py`, `sp1_n4_hstar.py` | OK |
| Común | `scripts/sp1_levels_common.py` | OK |
| Tests | `tests/` — 41 ficheros `test_*.py`, 20 específicos de SP1 | Sin ejecutar aún |
| Manifiestos | `provenance/results/*/manifest.json` | Íntegros |

---

## 6. Contenido que el audit propone degradar

Ninguna evidencia se elimina. Movimientos propuestos a anexo:

1. N1.E1 (LSAP vs voraz) — control de implementación, no resultado de tesis.
2. N1.E2 escalado, N1.E3 recálculo tras retirada.
3. N2.E1 validación del oráculo — se reduce a *inset* + 1 frase.
4. N4.E5 DPOP detallado, N4.E6 escalado.
5. N4.E8 F-IV temporal — el oráculo dispone de información futura; no sostiene
   comparación válida.
6. Traza representativa F-I — ilegible al tamaño de cuerpo.
7. Atlas de algoritmos que duplican ecuaciones.
8. Tablas estadísticas completas y `p`-valores extremos.

---

## 7. Decisiones que requieren tu confirmación antes del Checkpoint B

1. **Snapshot/commit.** No lo he creado por las 25 491 supresiones en
   `results/`. Opciones: (a) commitear sólo `Subdocuments/SP1` y `reports/`;
   (b) restaurar `results/` antes de nada; (c) commitear todo asumiendo las
   supresiones. **Recomiendo (a).**

2. **F3 panel A.** ¿Autorizas el re-análisis de 250 mundos para registrar
   `lp_objective` del modelo por puestos, o prefieres presentar la integralidad
   sólo como resultado formal?

3. **Campaña #1.** ¿Confirmas re-ejecutar las 9 celdas discretas sobre el banco
   held-out (factorial limpio) y **reutilizar** la rama continua y el
   primal–dual de `n4_v3`? Es la única forma de tener un 3×3 comparable sin
   pagar de nuevo la parte cara.

4. **`geo_qpg_smith` discreto.** Existe y nunca se ha reportado. ¿Entra en el
   factorial de N3.B como cuarto protocolo, o se deja en anexo?

---

## 8. Lo que este audit **no** ha hecho

- No ha modificado `sp1.tex` ni ninguna figura.
- No ha ejecutado simulaciones.
- No ha ejecutado la batería de tests (pendiente para Checkpoint B).
- No ha verificado el SHA de los scripts generadores frente al manifiesto.
- No ha comprobado que los valores citados en el capítulo coincidan con los
  `key_metrics.json` (auditoría numérica pendiente, recomendada en Checkpoint B).
