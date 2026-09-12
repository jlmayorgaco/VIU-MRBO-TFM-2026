# Plan de integración de la revisión en el TFM

## Principio

Integrar la revisión como evidencia trazable dentro del capítulo de marco
teórico/estado del arte y como base de los baselines del capítulo de
resultados. No copiar afirmaciones del coding estructural sin lectura cercana,
registro en `references/LITERATURE_LEDGER.md` y mapeo a `docs/04_CLAIMS_EVIDENCE.md`.

## SP1 — coaliciones

- Núcleo de lectura: `final/core_papers.csv`.
- Comparar formalizaciones de capacidades, requisitos de tarea, formación y
  reasignación; separar métodos centralizados de distribuidos.
- Baselines candidatos: MILP/set partitioning, generalized assignment,
  subastas/consenso y formación de coaliciones, elegidos por modelo.
- Evidencia que falta: close reading de payoff, información local, factibilidad,
  dinámica de actualización y garantías reales.

## SP2 — transporte físico

- Núcleo de lectura: `final/core_papers.csv` y `final/enabling_papers.csv` con
  términos de `physical_layer`/`execution`.
- Declarar el modo primario del TFM como transporte rígido/prehensil si se
  mantiene el charter; no mezclarlo con caging/empuje sin restricciones de
  contacto propias.
- Extraer pose, wrench, fuerzas internas, límites de actuador, estabilidad,
  seguridad y reconfiguración. Un equilibrio estratégico no sustituye estas
  pruebas.

## SP3 — tráfico y planificación

- Usar candidatos con señales de planificación, seguridad, warehouse/logistics
  y comunicación local.
- Elegir A*/Dijkstra, CBS/ECBS, planificación priorizada, ORCA/RVO o CBF-QP
  solo cuando el escenario y la información disponible sean comparables.
- Medir bloqueos, colisiones/distancia mínima, makespan, throughput y tiempo de
  recuperación con semillas pareadas.

## Redacción y claims

- Toda cifra debe venir de tablas/figuras derivadas, no de esta prosa escrita a
  mano.
- Etiquetar observaciones del dataset, evidencia bibliográfica y resultados
  propios con niveles distintos.
- Sustituir `first/novel/SOTA` por una formulación prudente hasta cerrar la
  auditoría de prior art y WoS.
