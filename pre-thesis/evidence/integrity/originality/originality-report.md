# Auditoría definitiva de originalidad y patrones de escritura — Stage 2.5

## Veredicto

**PASS integral con P3.** No se detectó copia problemática, autoplagio de una publicación previa ni patrón de escritura que requiera una corrección P1/P2. Las búsquedas web quedaron realineadas uno a uno con las muestras finales de memoria y monografía; ambos `--check` devuelven `PASS`.

El P3 restante es procedimental: este cribado no sustituye Turnitin/iThenticate ni permite atribuir autoría humana o automática.

## Sello y cobertura

- Fecha: 9 de septiembre de 2026; commit `e2e67abe7552b60be210805626fac4f495d95138`, rama `sp1-final-refactor`, árbol deliberadamente sucio.
- Memoria: grafo activo desde `pre-thesis/main.tex`; 279 párrafos, 90 muestreados (32,258 %), todos los 10 estratos cubiertos; 328 unidades/15 146 palabras en el barrido exhaustivo de estilo.
- Monografía: grafo activo desde `pre-thesis/monograph/main.tex`; 351 párrafos, 112 muestreados (31,909 %), todos los 10 estratos cubiertos; 448 unidades/17 768 palabras. `\VIUFullSPsixProofs` queda activa solo aquí.
- Se resolvieron `\iffalse`, `\iftrue` y `\ifdefined`; los offsets son líneas físicas reales. Se auditó prosa fuera de entornos display; captions, ecuaciones, tablas, TikZ y código quedan excluidos.
- Tres giros genéricos que producían coincidencias abiertas de cinco o seis palabras se reformularon durante el cierre; después se regeneraron inventarios, muestras, hashes y búsquedas alineadas. La consulta sustituta de SP3 también quedó registrada aunque el párrafo no resultó seleccionado en la muestra final.

| Artefacto | Páginas | SHA-256 |
|---|---:|---|
| `pre-thesis/main.tex` | — | `82228a53e9d8777a509418416208812628c047012c7e2c063161b57cbcf44cce` |
| `pre-thesis/build/main.pdf` | 97 | `07b32806a6f7a0ede9f93fb80ba7e68bb106dae0389e6d10b591ab0ea7c385c8` |
| `pre-thesis/monograph/main.tex` | — | `209232c9d7963bee78f3a218513a6d5117310b094d3558c46f53db782833fe46` |
| `pre-thesis/monograph/build/monograph.pdf` | 110 | `d22f011514079e7573dded2f8e19dd4710a1a01239d5450b76eb160738e2730f` |
| `corpus-inventory.csv` (205 fuentes) | — | `5c6279c51773c3465343b6fb63f4e64c89594550d3e52d3e87db0656544cc28b` |
| `audit_originality.py` | — | `bb19bd5a17934dbe63a29b7ff9e60268e6a4bf91460b9b1974268a8017615849` |

Los inventarios registran cada hash activo. El corpus contiene 43 fuentes de `paper/`, 43 de `work/`, 41 de `thesis/`, 32 del snapshot canónico y 46 del histórico. La igualdad exacta de membresía y hashes pasó en el sello final.

## Originalidad externa

Para cada párrafo muestreado se ejecutaron dos consultas: una frase exacta discriminante de 8–12 palabras y la misma consulta sin comillas. La memoria conserva 90 filas/180 consultas y la monografía 112 filas/224 consultas. Las 202 filas quedaron `ORIGINAL`: ningún fragmento devuelto contenía la frase exacta y el máximo solapamiento abierto fue de cuatro palabras consecutivas.

Los dos documentos comparten 10 pares de consultas, por lo que las muestras contienen 192 pares únicos. Esos 10 pares se reutilizaron únicamente porque coincidían literalmente las consultas exacta y abierta. `external-search-audit.csv` y `monograph-external-search-audit.csv` conservan consulta, URLs, fecha y veredicto; siete ledgers de partición preservan el rastro de ejecución, incluidos los tres casos reformulados. No se transfirió ningún resultado por mero ID ni se reprodujo texto extenso de terceros.

## Solapamiento con material propio

La comparación usa shingles normalizados de cinco palabras. Snapshot, `thesis/` y borradores del mismo proyecto son procedencia, no evidencia independiente.

| Documento | Corpus | Filas | Exactas | Altas | Moderadas | Lectura |
|---|---|---:|---:|---:|---:|---|
| Memoria | snapshot | 244 | 238 | 0 | 0 | Reutilización canónica declarada |
| Memoria | snapshot histórico | 75 | 15 | 3 | 8 | Historia del mismo proyecto |
| Memoria | `thesis/` | 237 | 161 | 21 | 26 | Revisión no publicada |
| Memoria | `paper/` | 0 | 0 | 0 | 0 | Borrador; confirmar estado |
| Memoria | `work/` | 52 | 0 | 0 | 6 | Borradores propios |
| Monografía | snapshot | 334 | 333 | 0 | 0 | Fuente canónica declarada |
| Monografía | snapshot histórico | 148 | 45 | 5 | 23 | Historia del proyecto |
| Monografía | `thesis/` | 329 | 256 | 25 | 28 | Revisión no publicada |
| Monografía | `paper/` | 2 | 0 | 0 | 0 | Borrador; confirmar estado |
| Monografía | `work/` | 84 | 1 | 1 | 10 | Extensión propia; declarar si fue publicada |

La reutilización exacta/alta desde `work/` es legítima solo bajo el supuesto de material inédito. Si cualquier archivo de `paper/` o `work/` fue enviado, defendido o publicado, exige autocita, declaración y posible reformulación.

Se verificaron dos obras previas. El TFG Uniandes de 2014 se comparó en texto completo (56 páginas, 188 ventanas) sin coincidencia cercana. El paper IECON 2015, DOI `10.1109/IECON.2015.7392735`, solo pudo compararse por título porque Crossref no expuso abstract ni texto. Los ledgers de obras previas contienen cero matches cercanos en ambos documentos.

## `avoid-ai-writing`, detection-only

| Documento | P0 bruto | P1 bruto | P2 bruto | P1 contextual | P2 contextual |
|---|---:|---:|---:|---:|---:|
| Memoria | 0 | 3 | 8 | 0 | 0 |
| Monografía | 0 | 2 | 8 | 0 | 0 |

Los P1 brutos son usos técnicos de `exhaustivo/exhaustiva/integral`; no quedan guiones largos en la prosa auditada. Los P2 proceden de conectores técnicos y agregados de ritmo derivados del contrato de 3–5 oraciones; no constituyen por sí solos señales de autoría. `ai-writing-adjudication.csv` conserva la adjudicación contextual.

No se detectaron residuos conversacionales, atribución vaga, apertura genérica, inflación de novedad, lenguaje promocional, conclusión vacía, pregunta retórica ni rastro de razonamiento interno.

## Prioridades y reproducción

1. Ejecutar el control institucional Turnitin/iThenticate antes del depósito, como comprobación independiente P3.
2. Confirmar por escrito que `paper/` y `work/` son inéditos; de lo contrario, reclasificar y autocitar.
3. Decidir si el trabajo Uniandes de 2014 es antecedente conceptual directo y citarlo por continuidad intelectual.
4. Tratar conectores y la cláusula con guiones como P3 opcional; no reemplazar terminología matemática ni romper mecánicamente el contrato de párrafos.

```powershell
python pre-thesis/evidence/integrity/originality/audit_originality.py --document both --all
python pre-thesis/evidence/integrity/originality/audit_originality.py --document thesis --author-works
python pre-thesis/evidence/integrity/originality/audit_originality.py --document monograph --author-works
python pre-thesis/evidence/integrity/originality/audit_originality.py --merge-external
python pre-thesis/evidence/integrity/originality/audit_originality.py --document thesis --check
python pre-thesis/evidence/integrity/originality/audit_originality.py --document monograph --check
```

Ambos checks pasan muestra ≥30 %, todos los estratos, fragmentos de 8–12 palabras, alineación web exacta, reglas de coincidencia, 205 hashes de corpus, hashes del grafo y PDF, y comparación con obras previas. La membresía y los hashes de fuentes activas no cambiaron durante el cierre; los hashes binarios reflejan dos builds `-Verify` reproducibles bit a bit incluso desde rutas distintas.

## Limitaciones

El buscador no cubre paywalls, repositorios privados ni plagio traducido. La extracción excluye captions y matemáticas. La similitud léxica no decide independencia intelectual, y los patrones de estilo no identifican autoría humana o automática. Los hashes prueban identidad de fuentes y PDF, no por sí solos la cadena de compilación; esta depende de los builds `-Verify` de la campaña principal.
