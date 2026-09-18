# Aplicabilidad de la trazabilidad documental

Fecha de corte: 2026-09-09. Este registro explica los campos de aplicabilidad generados en `source-manifest.csv` y replicados en `content-crosswalk.csv`. Su función es separar un vacío legítimo de una auditoría pendiente; no eleva el nivel de evidencia de ninguna fuente.

## Claims

`claim_link_status` usa cuatro estados:

- `linked`: `claim_ids` contiene identificadores existentes en `docs/04_CLAIMS_EVIDENCE.md` y `evidence_locator` apunta a ese ledger.
- `not-applicable`: la unidad es estructural, auxiliar, duplicada sin enlace canónico, contextual no activa o excluida.
- `reviewed-unlinked`: la fuente candidata fue adjudicada explícitamente, pero no existe base para enlazar el archivo completo a un claim; `evidence_locator` apunta a la fila hash-bound de `source-claim-review.csv`.
- `pending-semantic-review`: existe contenido candidato, pero falta auditar el fragmento, sus supuestos y la relación exacta con un claim.

`claim_relation` evita confundir mención con prueba. El generador emplea `mentions` para fuentes de manuscrito, `context` para libros, `canonical-reference` para duplicados enlazados, `candidate-only` para fuentes ya revisadas que permanecen fuera de los claims y `none` donde no aplica. `supports` y `refutes` están reservados para una adjudicación humana con locator de fragmento; no se infieren por ruta.

El corte actual contiene 57 unidades `linked`, 104 `not-applicable`, 41 `reviewed-unlinked` y ninguna `pending-semantic-review` a nivel de archivo. Las 45 unidades destinadas a `monograph` se dividen en cuatro fuentes de `paper/` con claim exacto ya adjudicado por la auditoría formal y 41 fuentes `candidate-only`: 26 fuentes LaTeX de `paper/` y 15 PDF del corpus lógico `work`. La revisión de esas 41 fuentes cubre identidad, clasificación y decisión de no enlace; no valida sus 91 resultados formales ni sus 266 unidades LaTeX etiquetadas como un bloque. Trece de esas unidades etiquetadas conservan contexto formal exacto y las 253 situadas fuera de un resultado formal tienen ya una decisión hash-bound de fragmento. Cualquier incorporación posterior debe respetar ese destino, relación y limitación, y aportar soporte independiente cuando la pieza pretenda sostener un claim. Los borradores del autor no son evidencia independiente y no reciben claims antes de contrastarlos con prueba, código o datos.

Las ocho fuentes activas de `thesis/` que estaban pendientes ya tienen decisión explícita. `thesis/generated/aws-industrial2-results.tex` presenta magnitudes de los claims `C15-SP0`, `C16-SP1SP2`, `C17-SP1SP2`, `C18-SP1SP5` y `C19-SP1SP5SP7`, por lo que queda enlazada con relación conservadora `mentions`, no `supports`. El resumen, el abstract, la introducción, la metodología, el índice de Resultados, las conclusiones y la tabla de cobertura bibliográfica son destinos derivados, agregadores o piezas estructurales; no constituyen evidencia independiente y quedan como `not-applicable` con motivo registrado en cada fila.

Los cuatro libros sin claim explícito también quedaron adjudicados como contexto sin claim activo. El volumen de automatización de almacenes aporta criterios y KPI, los dos volúmenes colectivos sirven como índice de capítulos y el tratado de teoría de grafos queda como referencia auxiliar de definiciones; ninguno respalda por sí mismo un resultado del TFM. Esta decisión no impide un uso futuro: cualquier promoción exigirá registrar el claim, el pasaje y, cuando corresponda, el capítulo primario.

La auditoría semántica formal aporta enlaces exactos para `paper/megajuego.tex`, `paper/sec_cfrd.tex`, `paper/sec_clusters.tex` y `paper/sec_modelo_fisico.tex`. Solo se importan claim-ID existentes en el ledger; `NONE` y `NONE_IN_DOCS_04` son marcadores internos excluidos. La relación de archivo permanece en `mentions`: un veredicto formal y una mención de claim no convierten todo el manuscrito en evidencia.

## Símbolos

`symbols` es un índice heurístico conservador, no un inventario matemático completo. `symbol_status` distingue:

- `indexed`: existe al menos una coincidencia del vocabulario programado;
- `pending-semantic-review`: hay señales de modo matemático fuera de ese vocabulario;
- `reviewed-local-only`: la revisión manual confirmó notación local, contextual o sobrecargada que no debe promoverse al vocabulario canónico;
- `none-detected`: una fuente LaTeX no presenta coincidencias ni señales matemáticas;
- `not-applicable`: el formato o la función estructural no se somete al índice.

El corte actual contiene 53 unidades `indexed`, 5 `reviewed-local-only`, 11 `none-detected`, 133 `not-applicable` y ninguna `pending-semantic-review`. Las cinco revisadas manualmente son `paper/sec_auditoria.tex`, `paper/sec_ensayo_cierre_figs.tex`, `paper/sec_ensayo_cierre_interp.tex`, `paper/sec_ensayo_cierre_plan.tex` y `paper/sec_ensayo_cierre_resultados.tex`; cada fila conserva el diagnóstico en `symbol_note`. En particular, `N` significa número de nodos de una continuación en `sec_ensayo_cierre_plan.tex`, no número de robots, y por eso no se promovió mediante una expresión regular amplia. Toda promoción de un símbolo debe comprobar significado, dominio y unidades en `docs/05_NOTATION.md`; una coincidencia textual no autoriza a reutilizar notación sobrecargada.

## Estados de evidencia

`evidence_status` conserva su semántica de triage por archivo. `supported` significa que al menos un claim enlazado está `SOPORTADA`; no valida todas las afirmaciones de una unidad mixta. El estado vinculante de cada claim sigue en `docs/04_CLAIMS_EVIDENCE.md` y puede ser `PENDIENTE`, `PARCIAL`, `SOPORTADA`, `REFUTADA` o `RETIRADA`.

El verificador falla ante SP desconocidos, claims inexistentes, estados vacíos, locators incoherentes, deriva entre ambos CSV o cambios del ledger no regenerados. Las rutas `aws-industrial2.tex` y `aws-industrial2-results.tex` se resuelven como SP3; `index.tex` permanece como agregador `SP1;SP2;SP3;transversal`, conforme a la matriz de investigación.
