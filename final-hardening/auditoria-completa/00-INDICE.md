# Auditoría completa de `pre-thesis/` — índice

Auditoría del TFM contra sus propias directrices (`pre-thesis/guidelines/`,
siete ficheros temáticos) más los frentes que no estaban cubiertos y que
convenía revisar igualmente.

**Artefactos auditados**

| Documento | Páginas | Compilado |
|---|---:|---|
| `pre-thesis/build-v2/main-v2.pdf` | 146 | limpio |
| `pre-thesis/supplementary/build/supplementary.pdf` | 113 | limpio |

---

## Parte mecánica — medido, no opinado

| # | Informe | Qué mide | Resultado |
|---|---|---|---|
| 1 | [`mecanica/01-gates.md`](mecanica/01-gates.md) | compilación, conformidad VIU, márgenes, trazabilidad de macros, censo formal | 0 errores, 0 refs indefinidas, 0 etiquetas duplicadas; **2 fallos VIU** |
| 2 | [`mecanica/02-prosa.md`](mecanica/02-prosa.md) | patrones de escritura asistida, ritmo, calcos, léxico | `lmscan` 1,8 % — «Human-written», confianza alta; el defecto es de **ritmo** |
| 3 | [`mecanica/03-lenguaje-pipeline.md`](mecanica/03-lenguaje-pipeline.md) | vocabulario de taller: `claim`, `gate`, `artefacto` | 19 ocurrencias en 2 ficheros |
| 4 | [`mecanica/04-trazabilidad-numerica.md`](mecanica/04-trazabilidad-numerica.md) | cifras escritas a mano frente a macros generadas | **7 pies de figura con la N a mano** teniendo macro |
| 5 | [`mecanica/05-referencias-cruzadas.md`](mecanica/05-referencias-cruzadas.md) | flotantes y ecuaciones citados en el texto | **19 flotantes nunca citados** — incumple VIU |

## Parte de lectura — una auditoría por directriz

| # | Informe | Directriz aplicada |
|---|---|---|
| 1 | [`lectura/01-figuras.md`](lectura/01-figuras.md) | `03-figuras-y-calidad-grafica.md`, reglas 1–110 |
| 2 | [`lectura/02-coherencia-y-flujo.md`](lectura/02-coherencia-y-flujo.md) | `02-coherencia-y-flujo.md`, secciones A–CB |
| 3 | [`lectura/03-fases-y-deposito.md`](lectura/03-fases-y-deposito.md) | `05-checklist-por-fases.md` (FASE 0–40) + `06-guia-estrategica-viu.md` |
| 4 | [`lectura/04-matematica.md`](lectura/04-matematica.md) | FASE 8 y 9, teorema a teorema |
| 5 | [`lectura/05-suplementario.md`](lectura/05-suplementario.md) | FASE 26–27 y sección CO |
| 6 | [`lectura/06-bibliografia.md`](lectura/06-bibliografia.md) | `04-literatura-citas-y-referencias.md`, secciones A–DZ |

---

## Herramientas que produjeron esto

Todas reutilizables, en el repositorio:

| Guion | Qué hace |
|---|---|
| `.claude/skills/viu-compliance/scripts/viu_check.py` | gate normativo sobre el PDF |
| `pre-thesis/scripts/check_margins_v2.py` | caja de contenido real por página, excluyendo encabezado y pie |
| `pre-thesis/scripts/check_macro_provenance.py` | cada macro activa frente al bundle de su campaña |
| `pre-thesis/scripts/census_formal_results.py` | cierre real de `\input`, resultados formales, ecuaciones sin citar |
| `final-hardening/audit_numeric_traceability.py` | literales numéricos frente a macros disponibles |
| `final-hardening/audit_crossrefs.py` | flotantes y ecuaciones sin citar |
| `.claude/skills/ai-burstiness/scripts/prose_audit.py` | ritmo, léxico, calcos, `lmscan` por párrafo |
| `final-hardening/scan_pipeline_language.py` | vocabulario de taller |
| `final-hardening/verify_audit_claims.py` | recuenta las afirmaciones de una auditoría externa |

---

## Advertencia sobre auditorías externas

`verify_audit_claims.py` existe por una razón. Una auditoría externa reciente
aportó diez recuentos de frecuencia: **los diez estaban inflados y seis eran
cero**. También afirmaba un fallo de numeración en el índice que no existe,
caracteres corruptos en seis páginas donde no hay ninguno, y figuras sin fuente
cuando no falta ninguna. Sus «palabras partidas» eran partición de guion al
justificar, que es tipografía correcta.

Antes de aplicar cualquier informe externo, recuéntelo.
