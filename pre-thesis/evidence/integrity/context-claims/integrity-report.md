# Auditoría independiente Stage 2.5: contexto, cifras y claims

**Veredicto: PASS WITH P3 — 0 P1, 0 P2.** La memoria VIU activa no contiene, en el estado congelado auditado, una afirmación cuantitativa sin trazabilidad, una cita activa inexistente, una referencia interna colgante ni un claim fuerte que exceda la evidencia examinada. Persisten cuatro clases de observaciones P3 de procedencia, precisión bibliográfica o edición; ninguna sostiene una conclusión más fuerte.

## Alcance y sello reproducible

- Fecha local: `2026-09-08` (`America/Bogota`).
- Commit visible: `e2e67abe7552b60be210805626fac4f495d95138` (`sp1-final-refactor`). `pre-thesis/` figura como no rastreado; por ello el commit no identifica por sí solo el manuscrito y los hashes son vinculantes.
- Entrada única: `pre-thesis/main.tex`. Se siguieron recursivamente `\input`/`\include`, se borraron ramas literales `\iffalse` y `\ifdefined` no definidas por esa entrada, y se excluyeron la monografía y snapshots sin arista activa.
- Grafo: 46 archivos; fingerprint SHA-256 de la secuencia `ruta|sha256`: `4e3caac8f29a13472758a8ddd0068f6a99ad1ef2162d261e9f162d21d43846a9`. El detalle está en `active-graph.csv`.
- PDF pendiente de sello final: `pre-thesis/build/main.pdf` fue regenerado después del freeze anterior; su SHA-256 se fijará tras dos compilaciones byte a byte idénticas. `build/verification.json` informa `passed`: 11 preliminares, 69 páginas de cuerpo, 39 de resultados, 8 de referencias, 10 de anexos, 98 totales y fracción resultados/cuerpo 0.565217.

## Resultados por fase

### Cifras y estadística

Se inventariaron el 100 % de las unidades cuantitativas activas: **67/67 grupos**. El inventario incluye cifras externas, parámetros, conteos, complejidades, cotas finitas, ejemplos numéricos, tablas completas, intervalos, valores `p`, repetición en resumen/conclusiones y presupuesto físico del PDF. Cada fila de `quantitative-claims.csv` enlaza texto y evidencia.

Los hashes activos de tablas E2, E3 y E4 coinciden con sus manifests; E6, E7 y Cargo pasan sus `audit.json`. Los valores extendidos de Cargo se comprobaron contra `tables/hypotheses.csv`, `tables/summary.csv` y las corridas archivadas; la macro regenerada es byte a byte idéntica al snapshot activo y el manifest Cargo sella el SHA-256 completo `1a726b4922437773f744c255a8082424a12bfc257d77570af6095351056782ba`. No se interpretó una simulación como prueba formal: cotas de SP1, E3, E4, E6 y E7 se verificaron en las pruebas activas, mientras los tamaños de efecto permanecen como resultados de campaña.

### Contexto de citas

La población tiene 74 comandos de cita ordinarios, 110 ocurrencias clave y 67 claves ordinarias únicas. Se seleccionaron **25/74 contextos (33.78 %)** mediante SHA-256 de `VIU-2026-stage2.5-context|ruta|ordinal|claves`, estratificando y tomando `ceil(0.30*n)` en anexos, marco, introducción, metodología, SP1, SP2 y SP3. Se consultaron fuentes primarias u oficiales; no se afirmó lectura de un PDF cuando solo se examinó su landing page/resumen.

Resultado: **22 supports, 3 partial, 0 unsupported, 0 unverified**. Los tres parciales son conservadores y no invalidan un claim fuerte:

1. `01-introduction.tex:16`, `an2023cooperativeReview`: la revisión soporta transporte cooperativo y sus retos, pero no demuestra por sí sola la inferencia económica sobre dimensionar la flota máxima.
2. `sp3.tex:184`, `barreiro2017distributed`: soporta dinámica poblacional distribuida, no las cuatro rondas, el cierre heurístico ni redes variables propias de esta implementación; el texto niega esa transferencia.
3. `sp4.tex:91`, `alonsomora2017transport`: soporta optimización restringida/SCP y transporte; la celda de complejidad es una caracterización del manuscrito, no un teorema textual de la fuente.

El detalle, URLs primarias y evidencia precisa están en `citation-context-sample.csv`.

### Claims sustantivos

Se registraron 67 claims sustantivos. La muestra determinista ordena por ruta/línea/ID dentro de seis estratos y toma ordinales `1,4,7,...`: **25/67 (37.31 %)**, por encima del 30 % y del mínimo de 10. Los 25 resultaron `aligned` o `aligned-scoped`; los niveles distinguen prueba formal, contraejemplo, simulación auditada, piloto, fuente primaria, contrato de diseño y limitación explícita. Véanse `claim-registry.csv` y `claim-sample.csv`.

### Grafo bibliográfico e interno

- 116 entradas BibTeX; 74 claves usadas contando `\nocite`; 0 claves activas ausentes de la bibliografía.
- 2 contextos `\nocite`, 8 claves; 7 son exclusivamente puntos del mapa bibliográfico: `huang2022mlLns`, `paul2023collective`, `shibata2023event`, `tang2025railgun`, `yu2023graphTransformer`, `zhang2024coalition`, `zhou2026cttapf`.
- 157 labels, todos únicos; 113 referencias internas, 86 destinos únicos; 0 destinos colgantes.
- 42 entradas BibTeX no alcanzadas por el grafo congelado. Son deuda editorial, no citas fantasma: `activmedia2003pioneer`, `balch1998behavior`, `bogomolnaiaJackson2002Hedonic`, `chenSun2011LeaderFollower`, `chenSun2012Coalition`, `crouse2016Rectangular`, `cuturi2013sinkhorn`, `demsar2006Statistical`, `fiorini1998velocity`, `grayLamport2006Commit`, `grisetti2007gridMapping`, `halpernMoses1990Knowledge`, `highs2026Official`, `holm1979Sequential`, `huangfuHall2018Highs`, `jangShinTsourdos2018GRAPE`, `jonkerVolgenant1987Shortest`, `kalman1960optimal`, `karp1972reducibility`, `kerby2014SimpleDifference`, `kube2000cooperative`, `lakens2013EffectSizes`, `leanh2006agv`, `luby1986MIS`, `mardenShamma2012LogLinear`, `martinezPiazuelo2022Population`, `mayne2000mpc`, `nash1950equilibrium`, `nav2StateEstimation2026`, `nedic2009distributedSubgradient`, `olson2011apriltag`, `petcuFaltings2005DPOP`, `ponda2010dynamicCommunication`, `quijano2017population`, `ren2004virtual`, `robotLocalization2026`, `silver2005cooperativePathfinding`, `song2002potential`, `uribe2021dualDistributed`, `weed2018entropic`, `zavlanos2008distributedAuction`, `zhangParker2013Resources`.

### Siete modos de fallo del academic-pipeline

Se auditaron explícitamente: bug de implementación que supera autorrevisión, cita alucinada, resultado experimental alucinado, dependencia de atajos, bug reformulado como hallazgo, metodología fabricada y frame-lock. Los siete quedan `CLEAR` en el freeze. `failure-modes.csv` conserva evidencia y justificación por modo. Los resultados negativos E2-PD, E4-timeout, E6-deadline y AWS-congestión se mantienen como negativos, no como garantías recuperadas retrospectivamente.

## Hallazgos P3 priorizados y corregibles

1. **P3 — recreación histórica incompleta.** `sp2.tex:216`, la auditoría E3 y la auditoría E4 declaran ausentes sus generadores históricos. El postproceso es trazable, pero no puede recrearse cada mundo desde cero. Corrección posterior: recuperar/versionar generadores o conservar esta limitación visible.
2. **P3 — tres atribuciones parciales.** Afinar, si se desea, las tres líneas enumeradas en la fase de citas o añadir fuente primaria más específica; su redacción actual ya limita la transferencia.
3. **P3 — bibliografía sobrante.** Las 42 entradas no alcanzadas aumentan ruido del ledger aunque no aparecen en el PDF. Podrían moverse a una bibliografía de trabajo después del depósito.
4. **P3 — maquetación menor.** `main.log` no contiene referencias/citas indefinidas ni labels duplicados; sí registra cajas `Underfull` en tablas/leyendas. El verificador no las considera fallo y no hay `Overfull` detectado en esta pasada.

## Comandos de cierre

```powershell
git rev-parse HEAD
git branch --show-current
git status --short -- pre-thesis
# Importación de active_graph()/active_literal_branches() desde:
# pre-thesis/evidence/integrity/originality/audit_originality.py
python -m pytest -q -p no:cacheprovider tests/test_sp2_effective_capacity.py tests/test_sp3_evidence.py tests/test_sp4_theory_and_evidence.py tests/test_sp6_recovery.py tests/test_cargo_e2e.py tests/test_sp7_traffic.py
Get-FileHash -Algorithm SHA256 pre-thesis/build/main.pdf
Get-Content pre-thesis/build/verification.json -Raw
```

El cierre focal produjo **38 passed in 34.53 s**. No se reescribieron manuscrito, código, configuraciones, datos, `paper/`, `work/`, `books/` ni `docs/`; esta auditoría solo creó este informe y siete CSV en su directorio.
