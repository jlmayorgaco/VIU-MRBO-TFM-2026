# Auditoría bibliográfica fresca

- Veredicto: **PASS** (`all_entries_keep`)
- Fecha de actualización: 2026-09-09T05:56:43+00:00
- Alcance: citas activas de `thesis` y `monograph` bajo `pre-thesis`.
- Regla aplicada: no se modificó LaTeX ni BibLaTeX.

## Resumen cuantitativo

- Entradas en `.bib`: 116
- Claves activas auditadas: 76
- Contextos activos revisados: 243
- Entradas `.bib` no activas: 40
- Claves activas sin entrada `.bib`: 0
- Acciones: KEEP=76, FIX=0, REPLACE=0, REMOVE=0
- Fuentes: arxiv=3, crossref_doi=67, manual_primary=2, official_url=4

## Refresco posterior al cambio en sp3.tex y al ID PDF determinista

- Claves activas sin cambios: True
- Contextos de cita sin cambios: True
- Contextos esperados/actuales: 243/243
- Hash `sections/source-snapshot/mainmatter/06-results-and-analysis/sp3.tex`: d97dc785296261bcd46b97b8ba2cf44a25bc41bafff318e4c6f98e8265d604a2
- PDF thesis: 07b32806a6f7a0ede9f93fb80ba7e68bb106dae0389e6d10b591ab0ea7c385c8
- PDF monograph: d22f011514079e7573dded2f8e19dd4710a1a01239d5450b76eb160738e2730f
- Cambio binario posterior: limitado al `/ID` del trailer; al normalizar ese campo, los PDF anteriores y actuales son byte a byte iguales y el texto extraído coincide en 207/207 páginas.
- Trazas por clave: 76/76
- Errores de rutas externas en fuentes auditadas: 0

## Dictamen

Todas las claves efectivamente citadas o nocitadas siguen localizadas en fuentes primarias o autoritativas. Los cambios posteriores declarados no alteraron claves ni contextos de cita, por lo que las trazas y fuentes web previas siguen aplicando. El ID determinista se inyecta desde un wrapper efímero y no modifica las fuentes LaTeX auditadas.

El veredicto se mantiene en PASS porque todas las claves activas quedan en KEEP y las verificaciones de comparación, PDF final, trazas y rutas externas pasaron.

## Matices conservados

- `barer2014ecbs`: Crossref expone fechas de migración/indexado de OJS, pero la página primaria AAAI/SoCS verifica 2014-08-15, volumen 5(1), páginas 19-27 y DOI.
- `barreiro2017distributed`: Crossref expone metadatos tempranos de 2016; fuentes institucionales y la citación final corroboran IEEE TSMC Systems 47(2):304-314, 2017.
- `bullo2009distributed`: Crossref omite el subtítulo; el subtítulo local corresponde a la edición del libro y no se marca como error.
- `wurman2008coordinating`: Crossref no resolvió por API en la pasada automática, pero la página primaria AAAI/OJS verifica la identidad bibliográfica y el contexto Kiva/almacenes.
- `sandholm2010population`: se verificó por página editorial MIT Press; no requiere DOI para ser válida como libro.
- Las fuentes comerciales (`geekplusWarehouseSolutions`, `mirInternalTransport`) solo deben respaldar ejemplos industriales generales, no métricas comparativas ni resultados científicos.
- `awsRobomakerWarehouse2021` sigue siendo válido como procedencia del mundo de simulación, aunque el repositorio oficial figure archivado/read-only en 2026.

## Artefactos

- Inventario de contextos: `.aris/citation-audit/contexts.txt` y `.aris/citation-audit/contexts.json`.
- Metadatos web: `.aris/citation-audit/web_metadata.json`.
- Trazas por clave: `.aris/traces/citation-audit/2026-09-09_run01/`.
- Contrato JSON: `CITATION_AUDIT.json`.

## Limitaciones

- El revisor mcp__codex__codex solicitado no está disponible; esta actualización conserva el revisor local fresco y las comprobaciones web/API autoritativas ya materializadas en .aris/citation-audit/web_metadata.json y trazas por clave.
- Esta actualización no reabre búsquedas web porque el inventario de claves y los 243 contextos de cita permanecen idénticos tras el cambio fuente declarado.
- No se modificó LaTeX ni BibLaTeX; REPLACE/REMOVE/FIX siguen en cero y cualquier acción correctiva futura requiere aprobación humana.

## Tabla por clave

| Clave | Veredicto | Fuente | Usos | Nocite | Nota |
|---|---:|---:|---:|---:|---|
| `alonsomora2017transport` | KEEP | crossref_doi | 8 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `ames2017cbf` | KEEP | crossref_doi | 4 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `an2023cooperativeReview` | KEEP | crossref_doi | 5 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `awsRobomakerWarehouse2021` | KEEP | official_url | 6 | 0 | Official repository source; suitable for simulation-asset provenance, not for scientific claims beyond the asset itself. |
| `barer2014ecbs` | KEEP | crossref_doi | 4 | 0 | Crossref reports OJS migration/indexing dates in 2021/2022, but AAAI/SoCS primary publication metadata matches the 20... |
| `barreiro2017distributed` | KEEP | crossref_doi | 1 | 0 | Crossref exposes 2016 early/publication metadata and page span 1-11; local BibLaTeX uses final issue metadata 47(2):3... |
| `bertsekas1988Auction` | KEEP | crossref_doi | 3 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `bezerra2025dynamicCoalition` | KEEP | crossref_doi | 2 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `bicchi1995closure` | KEEP | crossref_doi | 4 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `boyd2006randomizedGossip` | KEEP | crossref_doi | 2 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `buckman2019cbbaPr` | KEEP | crossref_doi | 2 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `bullo2009distributed` | KEEP | crossref_doi | 4 | 0 | Crossref short title omits the subtitle; the local BibLaTeX title is not treated as an error. |
| `cherukuri2016primalDual` | KEEP | crossref_doi | 3 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `choiBrunetHow2009CBBA` | KEEP | crossref_doi | 10 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `dai2024dynamicCoalition` | KEEP | crossref_doi | 2 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `desai2001formation` | KEEP | crossref_doi | 2 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `dutta2021hedonic` | KEEP | crossref_doi | 2 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `ebel2024cooperative` | KEEP | crossref_doi | 2 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `fink2008caging` | KEEP | crossref_doi | 2 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `fiorini1998velocity` | KEEP | crossref_doi | 2 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `franci2022stochasticGNE` | KEEP | crossref_doi | 2 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `geekplusWarehouseSolutions` | KEEP | official_url | 1 | 0 | Commercial page; suitable for industrial-context examples, not for validated performance claims. |
| `gerkeyMataric2002MURDOCH` | KEEP | crossref_doi | 4 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `gerkeyMataric2004MRTA` | KEEP | crossref_doi | 3 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `huang2022mlLns` | KEEP | crossref_doi | 2 | 2 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `internationalFederationRobotics2025` | KEEP | official_url | 1 | 0 | Official organization page; not a peer-reviewed literature source, but appropriate for market statistics. |
| `johnson2011acbba` | KEEP | crossref_doi | 4 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `kar2009imperfectConsensus` | KEEP | crossref_doi | 2 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `karp1972reducibility` | KEEP | crossref_doi | 3 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `khatib1986obstacle` | KEEP | crossref_doi | 4 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `kia2019dynamicConsensus` | KEEP | crossref_doi | 2 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `korsahStentzDias2013iTax` | KEEP | crossref_doi | 3 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `koshal2016aggregative` | KEEP | crossref_doi | 2 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `kuhn1955Hungarian` | KEEP | crossref_doi | 11 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `li2019largeAgentMapf` | KEEP | crossref_doi | 4 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `li2022mapfLns2` | KEEP | crossref_doi | 2 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `mirInternalTransport` | KEEP | official_url | 1 | 0 | Commercial page; suitable for industrial-context examples, not for validated performance claims. |
| `monderer1996potential` | KEEP | crossref_doi | 7 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `naito2025tihdp` | KEEP | crossref_doi | 2 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `nakamura1989dynamics` | KEEP | crossref_doi | 3 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `nanjanath2006dynamicAuctions` | KEEP | crossref_doi | 4 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `nedic2010constrainedConsensus` | KEEP | crossref_doi | 2 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `olfatiSaber2004switchingConsensus` | KEEP | crossref_doi | 3 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `ortega2002passivity` | KEEP | crossref_doi | 4 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `parker1998alliance` | KEEP | crossref_doi | 4 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `parkerTang2006ASyMTRe` | KEEP | crossref_doi | 4 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `paul2023collective` | KEEP | crossref_doi | 2 | 2 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `pereira2004caging` | KEEP | crossref_doi | 3 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `phan2024cactus` | KEEP | arxiv | 2 | 0 | Preprint/accepted-conference metadata checked against arXiv page. |
| `qiu2024payloadConsumption` | KEEP | arxiv | 2 | 0 | Preprint metadata checked against arXiv page. |
| `rantanen2018lossyAcbba` | KEEP | crossref_doi | 3 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `rosenfelder2024force` | KEEP | crossref_doi | 2 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `sandholm2010population` | KEEP | manual_primary | 10 | 0 | Book entry has no DOI in the local BibLaTeX entry; publisher metadata is sufficient for existence and core metadata. |
| `sartoretti2019primal` | KEEP | crossref_doi | 2 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `shan2024collectiveTransport` | KEEP | crossref_doi | 2 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `sharon2015cbs` | KEEP | crossref_doi | 4 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `shehoryKraus1998Coalition` | KEEP | crossref_doi | 4 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `shibata2023event` | KEEP | crossref_doi | 2 | 2 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `shibata2023localGlobal` | KEEP | crossref_doi | 2 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `shida2025infeasibleTasks` | KEEP | crossref_doi | 2 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `tang2025railgun` | KEEP | crossref_doi | 2 | 2 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `tsitsiklis1986asynchronousOptimization` | KEEP | crossref_doi | 3 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `vandenberg2008rvo` | KEEP | crossref_doi | 4 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `vandenberg2011orca` | KEEP | crossref_doi | 6 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `vanderschaf2017passivity` | KEEP | crossref_doi | 4 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `vigAdams2006Coalition` | KEEP | crossref_doi | 4 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `wang2017barrier` | KEEP | crossref_doi | 3 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `wurman2008coordinating` | KEEP | manual_primary | 1 | 0 | Crossref API did not return this DOI in the automated lookup, but the AAAI/OJS primary page verifies the bibliographi... |
| `yi2019operatorGNE` | KEEP | crossref_doi | 2 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `yoshikawa1993coordinated` | KEEP | crossref_doi | 3 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `yu2023graphTransformer` | KEEP | crossref_doi | 2 | 2 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `zhang2024coalition` | KEEP | crossref_doi | 2 | 2 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `zhangParker2013IQASyMTRe` | KEEP | crossref_doi | 4 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `zhangParker2013Resources` | KEEP | crossref_doi | 1 | 0 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
| `zhou2026cttapf` | KEEP | arxiv | 2 | 2 | Preprint/conference metadata checked against arXiv page. |
| `zlotStentz2006ComplexTasks` | KEEP | crossref_doi | 4 | 2 | Metadatos DOI verificados mediante Crossref/resolutor DOI. |
