# Auditoría de citas de SP2

**Fecha:** 2026-08-20  
**Bibliografía:** `references.bib`  
**Entradas citadas:** 21  
**Dictamen formal de la habilidad:** `ERROR`

## Resumen

Las 21 entradas realmente citadas por SP2 fueron comprobadas localmente en sus
tres usos: existencia, metadatos y adecuación contextual. Los 18 DOI resolvieron
y sus títulos/autores/años se contrastaron con Crossref; el preprint de Lee se
contrastó con arXiv, el artículo clásico de Kalman con el PDF de la revista y el
manual Pioneer con copias del manual original. No se detectó una cita inventada
ni un uso contextual que exija reemplazar o retirar una fuente.

El dictamen no se eleva a `PASS` porque el revisor fresco e independiente
exigido por la habilidad se bloqueó y no produjo trazas. Este `ERROR` describe
un fallo del procedimiento de independencia, no un hallazgo bibliográfico
adverso. Antes del depósito institucional conviene repetir esa revisión
zero-context o usar Zotero/DOI para una última exportación APA 7.

## Correcciones ya incorporadas

- Lee respalda la conmutación MILP--QP; no se le atribuye DMPC vecinal.
- Rosenfelder respalda medida y control de fuerza no prehensil.
- RBPF, grafo relativo, matriz de agarre, LQR, MPC, CBF y caging tienen
  atribución inmediata en su primera aparición técnica.
- El manual Pioneer solo respalda equipamiento de serie; LiDAR, IMU, cámara y
  transductor se declaran instrumentación añadida.

## Cobertura por entrada

Las 21 entradas quedan `KEEP` en la comprobación del agente principal:

`activmedia2003pioneer`, `alonsomora2017transport`, `ames2017cbf`,
`bicchi1995closure`, `bullo2009distributed`, `carlone2011linearGraphSlam`,
`desai2001formation`, `fink2008caging`, `grisetti2007gridMapping`,
`howard2005multirobotSlam`, `kalman1960optimal`, `kia2019dynamicConsensus`,
`lee2025switching`, `mayne2000mpc`, `nakamura1989dynamics`,
`olson2011apriltag`, `ortega2002passivity`, `pereira2004caging`,
`ren2004virtual`, `rosenfelder2024force` y `yoshikawa1993coordinated`.

Los contextos auditados están en `.aris/citation-audit/contexts.txt` y la traza
del fallo independiente en `.aris/traces/citation-audit/2026-08-20_run01/`.

