---
document: field_analysis_and_panel
stage: 3
round: 1
date: 2026-07-14
frozen_commit: 1218a06451f8e6b1f2c4624e49a601e492be5feb
frozen_commit_short: 1218a064
frozen_hash_scheme: FH-v2
frozen_hash_prefix: 2fe960
sealed_pdf_available: false
phase0_phase1_reconstructed_after_context_compaction: true
mutation_policy: read-only review; no manuscript edits
---

# Phase 0 — Field Analysis and Reviewer Panel

> Nota de persistencia: esta Phase 0 fue reconstruida fielmente después de una compactación de contexto. Conserva el alcance, los campos, las identidades, las dimensiones D1–D8 y los disclosures del informe emitido; no se presenta como transcripción literal.

## Frozen review object

- **Objeto evaluado:** cierre TeX congelado de la TFM *VIU-MRBO-TFM-2026*.
- **Commit:** `1218a06451f8e6b1f2c4624e49a601e492be5feb` (`1218a064`).
- **Fingerprint:** FH-v2, prefijo `2fe960`.
- **PDF sellado:** no disponible; la unidad primaria de revisión es `main.tex` y sus 27 entradas alcanzables en la copia congelada.
- **Extensión registrada:** 80 páginas según el manifiesto de cierre, 18 812 palabras, 107 entradas bibliográficas y 55 claves citadas distintas.
- **Exclusiones de independencia:** no consultar reseñas anteriores, `03_consolidated_editorial_decision.md`, el árbol principal, el PDF actual ni `docs/07-tfm`.
- **Política de mutación:** revisión estrictamente READ-ONLY.

## Field classification

La TFM se sitúa en la intersección de:

1. teoría de juegos y juegos poblacionales;
2. asignación de tareas y formación de coaliciones multi-robot;
3. factibilidad física de contacto, cierre y wrench;
4. control seguro mediante QP/HOCBF;
5. estabilidad ISS y control de movimiento;
6. degradación de comunicaciones, reemplazo y localidad;
7. simulación reproducible y trazabilidad de afirmaciones.

El argumento nuclear es que asignación, cardinalidad o equilibrio estratégico no bastan para certificar una coalición físicamente ejecutable. El manuscrito propone una línea progresiva de certificados: utilidad y umbral global, quórum entero, capacidad efectiva, geometría/contacto/wrench, reserva dinámica y seguridad, degradación de red y reemplazo.

## Central claims to audit

- La dinámica de Smith asciende un potencial exacto bajo las condiciones declaradas.
- Las formulaciones convexas con restricciones compartidas permiten caracterizar v-GNE mediante KKT, bajo Slater y para la dinámica primal-dual exacta.
- La cardinalidad y la capacidad escalar no garantizan cierre, equilibrio de wrench ni ejecutabilidad.
- La cadena A0–FULL produce evidencia no monótona: agregar factibilidad geométrica puede retirar reserva de tracción y perjudicar un régimen, aunque ayude en otros.
- La capa ejecutada RAW/SAFE/EXEC debe distinguirse del control nominal y del cierre global.
- Las afirmaciones de localidad deben separar componentes distribuibles de cuantiles, cierres, guardias y reemplazos globales.
- Coppelia debe tratarse como reproducción cualitativa o cinemática, no como validación física independiente.
- La originalidad defendible debe ubicarse en las interfaces, la semántica de coalición física y la arquitectura auditable, no en atribuir novedad a Nash, Smith, KKT, HOCBF o ISS.

## Evidence hierarchy

La revisión aplicará la siguiente jerarquía:

1. identidad algebraica o demostración formal;
2. auditoría numérica de la identidad o del residuo KKT/QP;
3. simulación modular controlada;
4. campaña integrada con ablaciones pareadas;
5. reproducción visual/cinemática en Coppelia;
6. hardware, que no forma parte de la evidencia disponible.

Una capa inferior no podrá presentarse como evidencia de una capa superior. En particular, una comprobación algebraica no valida el modelo físico, y un playback en Coppelia no constituye validación experimental independiente.

## Dimension framework

| ID | Dimensión | Pregunta de evaluación | Condición crítica |
|---|---|---|---|
| D1 | Trazabilidad | ¿Cada afirmación importante puede seguirse hasta fórmula, tabla, figura, código o artefacto? | Contradicción entre fuente, cifra y conclusión. |
| D2 | Correspondencia afirmación–evidencia | ¿La fuerza de cada conclusión coincide con el nivel real de evidencia? | Simulación presentada como hardware, causalidad sin ablación o superioridad universal. |
| D3 | Corrección teórica | ¿Nash, potencial, Smith, KKT/v-GNE, QP e ISS son correctos bajo hipótesis explícitas? | Error matemático central, equivalencia falsa o convergencia general no demostrada. |
| D4 | Originalidad y posicionamiento | ¿La contribución nueva se distingue de resultados heredados y del trabajo previo? | Novedad game-theoretic sobreatribuida o contribución central difusa. |
| D5 | Rigor experimental | ¿Existen controles, ablaciones, repetición, métricas, tolerancias y evidencia negativa? | Comparación no controlada, ausencia de baseline relevante o resultados irreproducibles. |
| D6 | Alcance físico y de sistema | ¿Se modelan y delimitan contacto, wrench, saturación, dinámica, red y hardware? | Afirmaciones físicas que exceden el modelo o ignoran supuestos determinantes. |
| D7 | Narrativa académica | ¿Problema, teoría, método, resultados y conclusiones forman una línea argumental legible? | Fragmentación que impide identificar tesis, aportes o relación teoría–evidencia. |
| D8 | Reproducibilidad y bibliografía | ¿El cierre, artefactos, versiones y referencias permiten auditoría independiente? | Fuentes inexistentes, versión canónica indeterminada o artefactos centrales ausentes. |

## Reviewer panel

| Identidad | Función | Foco principal | Disclosure/independencia |
|---|---|---|---|
| **EIC / Chair** | Integración editorial | Consistencia contractual, severidad, decisión y resolución de discrepancias | No sustituye el juicio técnico independiente. |
| **R1 — Métodos y evidencia** | Revisor metodológico | Diseño experimental, estadística, ablaciones, controles y correspondencia afirmación–evidencia | Debe puntuar D1, D2, D5 y D8 sin usar informes ajenos. |
| **R2 — Dominio: teoría de juegos y robótica multiagente** | Revisor de dominio | Nash, Smith, potencial, KKT/v-GNE, QP, ISS, localidad, wrench, integración y originalidad | Exposición previa al manuscrito declarada; evaluación independiente y sin leer otros dictámenes. |
| **R3 — Reproducibilidad e integridad técnica** | Revisor técnico | Manifiestos, artefactos, código, tolerancias, trazabilidad y versión canónica | No debe inferir validez científica solo por ejecutabilidad. |
| **Devil's Advocate** | Revisor adversarial | Buscar la interpretación más fuerte no soportada, fallos de cierre y contraejemplos | No convierte objeciones hipotéticas en defectos sin evidencia. |

## Panel scoring contract

Cada revisor asignará `pass`, `warn` o `block` a D1–D8 con evidencia localizada. D1–D3 son dimensiones obligatorias; D4–D8 son de alta importancia. La decisión contractual se resuelve por severidad:

- **F1:** cualquier `block` en una dimensión obligatoria implica `reject`.
- **F2:** dos o más `warn`/`block` en dimensiones obligatorias por la mayoría implican `major_revision`.
- **F3:** cualquier `block` en dimensión de alta importancia por la mayoría implica `major_revision`.
- **F4:** cualquier `warn` en dimensión obligatoria implica al menos `minor_revision`.
- **F5:** cualquier `warn` en dimensión de alta importancia implica al menos `minor_revision`.
- **F0:** solo si todas las dimensiones obligatorias son `pass` para todo el panel y no se activa una condición de mayor severidad procede `accept`.

Los promedios numéricos son orientativos y no anulan una condición ordinal de mayor severidad.

## Field-specific review risks

1. Confundir un potencial estático con una garantía de convergencia de cualquier dinámica implementada.
2. Extender KKT/v-GNE del problema continuo al redondeo entero, la guardia o el cierre heurístico.
3. Transferir pasividad del modelo nominal al filtro ejecutado, saturado o sometido a resets.
4. Presentar como distribuida una arquitectura que usa cuantiles, cierres o reemplazos globales.
5. Atribuir al juego mejoras producidas por un reparador global o por un baseline no estratégico.
6. Equiparar capacidad escalar con factibilidad de wrench.
7. Tratar Coppelia como evidencia física independiente.
8. Inflar la novedad de mecanismos estándar en lugar de defender la contribución integradora.

## Required Phase 2 output

Cada dictamen debe incluir:

- D1–D8 con score y evidencia;
- comprobación F1–F5 y F0;
- recomendación y confianza;
- resumen del manuscrito;
- entre tres y cinco fortalezas;
- entre tres y cinco debilidades formuladas como problema–impacto–sugerencia–severidad–ubicación;
- evaluación de literatura, teoría, argumento y contribución;
- preguntas y observaciones menores;
- tabla cuantitativa 0–100 y promedio;
- decisión terminal `reject`, `major_revision`, `minor_revision` o `accept`.

## Phase 0 disclosure

R2 declara exposición previa al manuscrito. En Phase 0 no utiliza informes de otros revisores ni decisiones consolidadas. La exposición previa se mantiene visible y se compensa mediante precommitment explícito, evidencia localizada y aplicación literal del contrato de severidad.
