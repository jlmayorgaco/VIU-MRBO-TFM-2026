# Auditoría semántica — corpus `thesis`

Fecha de corte: 2026-09-08. Esta revisión pertenece a Stage 2.5 de integridad. No constituye revisión académica Stage 3, autorización editorial ni promoción automática de resultados.

## Cobertura y validación

- Rango auditado: `THESIS-FR-0001`–`THESIS-FR-0021`, en el orden del inventario.
- Cobertura: 21/21 identificadores; no hay huecos ni `result_id` duplicados.
- Esquema: las 18 columnas de `BASE_COLUMNS`, en el mismo orden que `semantic-b.csv`.
- Campos obligatorios: completos en las 21 filas.
- Fuentes: se leyeron completos los ocho ficheros de sección, sus ocho anexos de demostraciones y los documentos canónicos exigidos por `AGENTS.md`.
- Relación con el spine: se contrastaron los 18 `FSF-01`–`FSF-18`, sus veredictos finales y la rerevisión. `DUPLICATE` significa que debe conservarse solo la formulación activa canónica; una superposición corregida no sanea retroactivamente un enunciado fuente defectuoso.
- Inventario: no se regeneró ni se modificó `formal-results-audit.csv`; tampoco se editaron LaTeX, claims, manifiestos o fuentes.

Los SHA-256 actuales coinciden con `source_sha256` en las 21 filas del inventario:

| Fuente | SHA-256 |
|---|---|
| `sp0.tex` | `423a856a3ac3f836babe0b6ceddeea28f66db2d70f7386dda770cd9f8dc9b0a2` |
| `sp1.tex` | `102684bee5548244c9fb3cf2dacf0364c207e4b9b94c84b95f899affa31c8d96` |
| `sp2.tex` | `04cc09945f4e90aa7987abe6d078bc81311021fbe96baa9c880d10989ce6d688` |
| `sp3.tex` | `e9ff4962f5312300a58afb8436f92a26fa1a30c68ed2e0e20ab3840bdb680ede` |
| `sp4.tex` | `887e2e13952cd41d6b7c3133e23a3328a85b8bd62501f2380eb85d5678b692eb` |
| `sp6.tex` | `3433cfeecbb86023a6d4bd2f8bdf4545704de644b302de0a914fb8e33fe856af` |
| `sp7.tex` | `37af59fc438876889129fff887838ad78fd44aa94573984b623c4181d3833b83` |
| `sp8.tex` | `9eed4b36420fadbc60148f4a7f9db393435e822e1d98d3987bbae6c9d819c399` |

## Veredictos

| Veredicto | Cantidad | Lectura |
|---|---:|---|
| PASS | 3 | Resultado correcto en su dominio; aún requiere decisión editorial. |
| LIMITED | 8 | Núcleo recuperable, pero el enunciado original omite una condición, escala o alcance material. |
| FAIL | 2 | Bicondicional o cuantificador falso con contraejemplo explícito. |
| DUPLICATE | 8 | Resultado ya cubierto por una formulación canónica activa o una copia inequívoca. |
| CONJECTURE | 0 | Ningún elemento de este bloque es solo una conjetura. |

## Resultado por identificador

| ID | Veredicto | Hallazgo decisivo | Relación activa/destino |
|---|---|---|---|
| 0001 | LIMITED | El potencial, Nash factibles, óptimos y Nash subóptimos son correctos; “toda secuencia termina en Nash” requiere maximalidad. | Monografía; FSF-01 es solo una generalización relacionada. |
| 0002 | PASS | `PoS=1` y `PoA=+∞` siguen de una familia 2×2 con razón `1/(2 epsilon)`. | Monografía. |
| 0003 | DUPLICATE | La regulación finita bajo activación sin inanición repite C1-SP0 y la caracterización anterior. | Conservar claim canónico. |
| 0004 | DUPLICATE | Teorema de cuotas realizables correcto. | FSF-01 añade maximalidad y bound explícito. |
| 0005 | PASS | Bajo escasez sin exceso, `D_n=sum n_k-N` no depende de la distribución. | Monografía; no está en los 18 FSF. |
| 0006 | DUPLICATE | Copia dentro de `iffalse`, etiqueta duplicada y condición terminal incompleta. | No contar ni migrar; usar FSF-01. |
| 0007 | LIMITED | La prueba cuenta revisiones; “tiempo finito” no es una cota física bajo justicia sola. | Usar FSF-01. |
| 0008 | DUPLICATE | Gradiente marginal e incompatibilidad de derivadas cruzadas correctos. | FSF-02. |
| 0009 | DUPLICATE | Convexidad estricta da fórmula interior y unicidad del QP. | FSF-09; falta claim-ID exacto. |
| 0010 | FAIL | El minimizador regularizado no minimiza necesariamente el residual puro. | Archivar original; usar FSF-10. |
| 0011 | LIMITED | El gradiente/KKT funciona para acciones físicas, pero `a=0` deja símbolos y restricción sin definir. | Usar FSF-11. |
| 0012 | PASS | Potencial exacto, convexidad fuerte y VE único están demostrados para la instantánea congelada. | Monografía; claim C4A-SP4. |
| 0013 | LIMITED | La rama nominal es válida; la cota perturbada mezcla traslación/rotación y fuerza/par sin métrica. | Usar FSF-08; FSF-07 cubre Cargo nominal. |
| 0014 | LIMITED | Identidad y bound de cambios correctos; terminar en Nash exige camino maximal. | Usar FSF-12. |
| 0015 | LIMITED | La equivalencia Nash–mínima usa costes positivos y déficit no trivial, ausentes del enunciado. | Usar FSF-13. |
| 0016 | DUPLICATE | La construcción de costes `M` y `2` prueba PoA sin cota uniforme. | FSF-14. |
| 0017 | LIMITED | La cota omite espera inicial y certificación terminal; justicia no acota segundos. | Usar FSF-15 y sus `2^n_R` ventanas. |
| 0018 | LIMITED | El potencial de rutas es exacto, pero un prefijo truncado no termina necesariamente en Nash. | Usar FSF-16. |
| 0019 | DUPLICATE | `theta_7<∞` y `lambda_7>theta_7` excluyen Nash conflictivos bajo accesibilidad. | Parte de FSF-17. |
| 0020 | DUPLICATE | Finitud, liberación y no reingreso dan concesión finita para una zona. | Parte de FSF-17; falta claim-ID exacto. |
| 0021 | FAIL | Una interacción remota por sí sola no crea la pareja indistinguible necesaria para una imposibilidad universal. | Archivar original; usar FSF-18. |

## Bloqueos y correspondencia de evidencia

Los dos resultados `FAIL` no pueden sostener conclusiones. `0010` queda refutado por el caso escalar `G=Q=1`, demanda uno y regularización 100; `0021` queda refutado por una familia singleton con óptimo conocido. Sus reemplazos activos, FSF-10 y FSF-18, cambian materialmente los enunciados y no son simples pruebas adicionales.

Los ocho `LIMITED` tampoco deben migrarse literalmente. Las correcciones ya existentes cubren maximalidad (`0007`, `0014`, `0018`), acción inactiva (`0011`), escala de wrench (`0013`), costes positivos (`0015`) y ventanas temporales (`0017`). `0001` conserva valor histórico, pero necesita el mismo contrato de camino maximal.

Los tres `PASS` poseen pruebas completas. Solo `0002` y `0012` tienen correspondencia directa con `C7B-SP0` y `C4A-SP4`; `0005` corresponde a `C1B-SP1`. Este veredicto no decide su inclusión frente al presupuesto editorial. Los duplicados remiten al resultado activo indicado y no suman contribuciones nuevas.
