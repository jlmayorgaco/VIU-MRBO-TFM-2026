# Inventario y trazabilidad de fuentes

Este directorio registra el material que alimenta `pre-thesis` sin concatenar documentos ni copiar libros. Los corpus lógicos `books` y `work` residen físicamente en `material/books/` y `material/compendios/`; `paper/` y `thesis/` conservan sus raíces. Cada archivo mantiene una fila, un SHA-256 y, cuando existe un duplicado byte a byte, la ruta del ejemplar canónico. La selección editorial ocurre en `content-crosswalk.csv`; el manifiesto no convierte un borrador en evidencia.

## Artefactos

- `source-snapshot.json`: commit, resumen no destructivo del árbol sucio, conteos del corpus, controles y hashes de la plantilla, configuración y TikZ protegidos.
- `source-manifest.csv`: inventario de archivos, páginas de PDF o primera sección LaTeX, deduplicación, SP, claims, símbolos detectables, uso, generador, procedencia y licencia.
- `content-crosswalk.csv`: destino obligatorio de cada unidad: `thesis-body`, `thesis-appendix`, `monograph`, `background` o `archive-only`.
- `source-claim-review.csv` y `source-claim-review-decisions.json`: adjudicación hash-bound de las 41 fuentes de monografía sin claim activo. `reviewed-unlinked` cierra únicamente la decisión a nivel archivo; sus 91 resultados formales y 266 unidades LaTeX etiquetadas conservan la auditoría por resultado o fragmento. Trece de esas 266 unidades registran el resultado formal que las contiene y las otras 253 poseen decisión explícita por fragmento.
- `labeled-unit-review-decisions.json`: 456 decisiones semánticas hash-bound por fragmento y 47 bindings de fuente. Veinte bindings cubren las 137 etiquetas de `thesis` situadas fuera de resultados formales auditados; dos cubren el ensayo exploratorio `megajuego`; veinticinco cubren el material técnico restante de `paper`. Distinguen definición, límite, contexto, protocolo y resumen de evidencia y fijan si cada pieza sobrevive en memoria, monografía o solo como fuente suprimida, sustituida o excluida.
- `idea-ledger.csv` y `idea-ledger-summary.json`: registro reproducible de 13.019 unidades editoriales identificables (títulos de documento, marcadores PDF, encabezados inferidos, secciones LaTeX, resultados formales y 477 observaciones, figuras, tablas o ecuaciones etiquetadas). Las filas formales heredan el veredicto y los claim-ID exactos del inventario canónico. En 21 unidades etiquetadas, la línea fuente cae dentro de un resultado auditado: el ledger conserva el ID formal, el veredicto y los claims de contexto en campos separados, pero deja vacío el claim propio de la unidad. Las otras 456 tienen decisión explícita y ninguna queda pendiente. Sus funciones son 116 definiciones, 123 límites, 169 contextos, doce protocolos y 36 resúmenes de evidencia; los destinos de las 477 etiquetas son 72 `thesis-body`, 294 `monograph` y 111 `archive-only`. El corpus histórico `thesis` reúne 140 etiquetas cerradas; el lote exploratorio `megajuego`, quince; y veinticinco fuentes técnicas reúnen 304 decisiones, de las cuales 214 sobreviven como candidatas monográficas y 90 se excluyen. Una etiqueta o un marcador registra una unidad candidata y su localizador; no demuestra que sea correcta ni que dos títulos parecidos sean equivalentes.
- `formal-results-audit.csv`: inventario canónico de teoremas, proposiciones, lemas, corolarios y conjeturas, con hash de fuente, claim-ID por resultado, veredicto normalizado y las siete dimensiones de auditoría. La alerta léxica de prueba próxima se conserva, pero no sustituye la revisión semántica.
- `formal-spine-review.md` y `formal-spine-verdicts.csv`: revisión semántica inicial de la columna formal; se conservan como historial y no representan el estado final.
- `formal-spine-rereview.md` y `formal-spine-rereview.csv`: re-revisión delta posterior; sus fallos documentan el estado intermedio que motivó las correcciones.
- `formal-spine-final-review.md` y `formal-spine-final-verdicts.csv`: veredicto independiente definitivo sobre las fuentes activas. Esta pareja tiene precedencia semántica sobre las dos revisiones anteriores y sobre el inventario estructural.
- `integrity/formal-audit/semantic-all.csv`, `semantic-all.md` y `semantic-all-summary.json`: auditoría semántica exhaustiva de 166/166 resultados candidatos, enlazada por hash y sin promociones automáticas.
- `book-consultation-map.csv` y `book-consultation-map.md`: consulta documental de 37/37 libros canónicos, con identidad verificada, fuente autorizada, localizadores, uso y límites de copyright. Diez están además en el ledger; las otras 27 no adquieren autorización de cita por esta verificación de metadatos.
- `work-thematic-crosswalk.csv` y `work-thematic-crosswalk.md`: clasificación temática de 33/33 borradores canónicos; ninguno se acepta como evidencia independiente.
- `plan-completion-audit.md`: cierre requisito por requisito con estados `PASS`, `PARTIAL` y pendientes externos o físicos.
- `../CITATION_AUDIT.md` y `../CITATION_AUDIT.json`: auditoría fresca de las 76 claves activas y sus 243 contextos, con trazas por clave en `../.aris/`.
- `integrity/originality/originality-report.md`: auditoría anti-AI, solapamiento propio y 202 búsquedas web alineadas con los PDF finales.

Los estados se interpretan de forma conservadora. En `evidence_status`, `candidate` significa material aún no validado y `supported`, únicamente que `docs/04_CLAIMS_EVIDENCE.md` vincula explícitamente el archivo con al menos una afirmación `SOPORTADA`; ese enlace no promueve todos sus párrafos ni resultados formales. En `audit_status`, los 166 veredictos proceden de `integrity/formal-audit/semantic-all.csv`: las siete banderas `*_audited=yes` significan que la dimensión fue revisada, no que la respuesta fuera favorable. Ningún veredicto promueve una afirmación sin cruce exacto con evidencia.

Para resolver discrepancias en los 18 resultados activos se usa la precedencia `formal-spine-final-verdicts.csv` > `formal-spine-rereview.csv` > `formal-spine-verdicts.csv`. Para el corpus completo, `formal-results-audit.csv` es la vista canónica reproducible de `integrity/formal-audit/semantic-all.csv`. Los informes anteriores no se reescriben: conservan la secuencia de hallazgo, corrección y cierre. Ningún estado léxico como `inline_proof_detected` sustituye una revisión matemática.

## Generación reproducible

Desde la raíz del repositorio:

```powershell
python .\pre-thesis\evidence\tools\build_inventory.py
python .\pre-thesis\evidence\tools\build_inventory.py --check
python .\pre-thesis\evidence\tools\build_source_claim_review.py --check
python .\pre-thesis\evidence\tools\verify_book_identities.py --check
python .\pre-thesis\evidence\tools\build_idea_ledger.py
python .\pre-thesis\evidence\tools\build_idea_ledger.py --check
python .\pre-thesis\scripts\verify_release_manifest.py --write
python .\pre-thesis\scripts\verify_release_manifest.py --check
```

El generador usa la biblioteca estándar de Python y `pdfinfo` para contar páginas. En Windows recurre a `pypdf` cuando Poppler no puede abrir un nombre que supera `MAX_PATH`. Escribe únicamente dentro de `pre-thesis/evidence/`; no modifica ni copia los cuatro corpus. Los CSV se emiten como UTF-8 con BOM y neutralizan celdas que empiecen por `=`, `+`, `-` o `@` para evitar ejecución accidental al abrirlas en una hoja de cálculo. El sello de release se renueva solo después de ejecutar esas auditorías sobre el repositorio completo; el build portátil lo verifica sin volver a leer los corpus originales.

La deduplicación de archivos es exacta y global por SHA-256. La ruta canónica se elige primero por precedencia documental (`thesis`, `paper`, `work`, `books`) y después por orden lexicográfico; estos nombres son corpus lógicos, no raíces obligatorias. Las copias reciben `archive-only`, pero permanecen inventariadas. El generador incorpora los mapas humanos de libros y compendios: estos afinan destino, ámbito y claim contextual sin elevar el estado de evidencia. El ledger de ideas señala coincidencias de títulos normalizados como candidatos a revisión, nunca como duplicados semánticos resueltos.

## Criterios editoriales automatizados

- `material/books/` (`books`): consulta de fondo sin copia ni reproducción; las 37 identidades están verificadas, pero las 27 unidades fuera del ledger todavía requieren revisión contextual y alta antes de citar.
- `material/compendios/` (`work`): borradores del autor destinados inicialmente a la monografía; no son evidencia independiente.
- `paper/`: cantera de resultados técnicos; sus fuentes LaTeX van a la monografía como candidatas y sus salidas de build quedan archivadas.
- `thesis/`: base VIU. Las fuentes de anexos apuntan a `thesis-appendix`; las fuentes de formato, contenido y figuras apuntan a `thesis-body`; salidas y auxiliares se regeneran.

La asignación SP usa la correspondencia histórica de `docs/02_RESEARCH_MATRIX.md`: `sp0`--`sp3` → SP1, `sp4`--`sp6` y Cargo → SP2, `sp7`--`sp8` y tráfico industrial → SP3. Cuando el nombre o la ruta no permiten una asignación segura se registra `unassigned` o `transversal`; no se infiere contenido de un PDF para rellenar el campo.

## Deriva observada del plan

El recuento fijado se verifica sobre las raíces físicas actuales: 42 PDF de `material/books/` forman 37 hashes únicos y 43 PDF de `material/compendios/` forman 33. Los `unit_id` conservan la identidad asignada antes del traslado, de modo que las decisiones humanas y los hashes no pierden continuidad. El baseline de planificación indicaba 104 resultados formales en `paper/`, pero el generador inventaría todos los entornos nucleares presentes. La diferencia queda en `source-snapshot.json` como `PAPER_FORMAL_COUNT_SOURCE_DRIFT`; no se omiten resultados para forzar el número histórico.

## Límites

La relación claim–archivo se obtiene inicialmente de las rutas entre acentos graves en `docs/04_CLAIMS_EVIDENCE.md`; los mapas documentales añaden contexto, pero no convierten ese enlace en una relación claim–enunciado. A nivel fuente existen 57 enlaces, 104 casos no aplicables y 41 candidatos revisados sin enlace; no queda ninguna fuente en espera de adjudicación. `reviewed-unlinked` no significa que el contenido esté validado: mantiene el archivo fuera de los claims activos y desplaza cualquier extracción futura al localizador de fragmento correspondiente. El ledger incluye 8.940 entradas de consulta en libros, 3.094 de borradores, 698 de `paper/` y 287 de `thesis/`; 11.578 coincidencias de título requieren desambiguación y no se fusionaron. Las 477 unidades LaTeX se detectan únicamente cuando el entorno posee una etiqueta convencional `obs:`, `fig:`, `tab:` o `eq:`. Veintiuna tienen contexto formal exacto por contención de línea —2 `PASS`, 15 `LIMITED`, 2 `FAIL` y 2 `DUPLICATE`—; las otras 456 poseen revisión semántica explícita y ninguna conserva `pending-semantic-review`. Solo esas decisiones explícitas pueblan `claim_ids`: 116 definiciones, 123 límites, 169 contextos, doce protocolos y 36 resúmenes de evidencia. Las 140 etiquetas históricas de `thesis` tienen destinos 72 `thesis-body`, 48 `monograph` y 20 `archive-only`. El lote exploratorio `megajuego` aporta quince decisiones adicionales, sin estatus confirmatorio. Veinticinco fuentes técnicas añaden 304 decisiones: 214 candidatas monográficas y 90 exclusiones por falta de artefactos reproducibles, resultados formales fallidos, duplicación, conflicto arquitectónico, ley física inconsistente o sobregiro. Una tabla resumen nunca sustituye los datos primarios. La detección de símbolos se limita a una lista canónica corta. La auditoría de libros valida DOI/identidad, no el contexto de una cita. El inventario tampoco valida por sí solo unidades, demostraciones ni resultados estadísticos: esas comprobaciones pertenecen a la auditoría formal, la revisión semántica y el ledger bibliográfico.
