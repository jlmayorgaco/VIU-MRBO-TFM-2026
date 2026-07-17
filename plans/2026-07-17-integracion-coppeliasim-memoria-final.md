# Integración de CoppeliaSim y simulaciones AWS en la memoria final

## Propósito

Incorporar en la memoria VIU la secuencia completa de pilotos AWS C15--C19 y la escena CoppeliaSim `Industrial 2`, manteniendo separadas la evidencia algorítmica, el replay cinemático, la auditoría geométrica y la validación física todavía pendiente.

## Fuentes de verdad

- `docs/00_TFM_CHARTER.md`--`docs/07_SP_SECTION_TEMPLATE.md`.
- `docs/04_CLAIMS_EVIDENCE.md`, filas C15--C19.
- `results/coppeliasim_validation/aws_dynamic_assignment_sp0/`.
- `results/coppeliasim_validation/aws_heterogeneous_coalitions*/`.
- `results/coppeliasim_validation/aws_industrial2_method_comparison_pilot/`.
- `results/coppeliasim_validation/aws_industrial_adversarial_industrial2/`.

## Alcance editorial

La integración se realizará mediante una subsección transversal después de la campaña Cargo, dos figuras generadas y una tabla compacta de evolución experimental. Metodología, conclusiones y reproducibilidad se actualizarán con la misma frontera de evidencia. No se describirá `Industrial 2` como validación dinámica de Pioneer, agarre cooperativo, contacto rueda--suelo o operación industrial.

## Reglas numéricas

Los valores C15--C19 se importarán desde los CSV y manifiestos mediante un exportador reproducible. La memoria consumirá macros y filas de tabla generadas; no se escribirán a mano resultados que ya existen en datos procesados.

## Hitos

- [x] H1 — exportador LaTeX desde CSV/JSON y prueba de consistencia.
- [x] H2 — subsección AWS/CoppeliaSim integrada en el capítulo 6.
- [x] H3 — resumen, abstract, metodología y conclusiones reconciliados con C19.
- [x] H4 — comandos de reproducción documentados.
- [x] H5 — PDF compilado y revisado visualmente.

## Cierre

El 17 de julio de 2026 se generaron 50 macros desde las fuentes de resultados,
pasaron 28 pruebas AWS/CoppeliaSim y se inspeccionaron las páginas del resumen,
abstract, sección 6.13 y conclusiones. La salida estable conserva C19 como piloto
negativo y mantiene abierto el gate de validación dinámica tridimensional.

Artefacto revisado: `output/pdf/TFM_VIU_CoppeliaSim_integrado.pdf`, 136 páginas,
SHA-256 `60127B1590289E7343CC739620DA02758CE46231C3BE2955C5698AF88C7799D7`.

## Riesgos

- Exceso de páginas: limitar la subsección a dos figuras, una tabla y discusión crítica.
- Sobreafirmación: usar `piloto`, `proxy`, `cinemático`, `muestreado` y `parcial` donde corresponda.
- Inconsistencia con la memoria actual: reemplazar la frase que reduce CoppeliaSim a geometría por una descripción de geometría más replay cinemático.
- Duplicación de C16--C18: presentar una evolución, no repetir todas las tablas originales.

## Registro

- 2026-07-17: se elige una subsección transversal en lugar de repartir cifras entre cuatro SP; así se conserva la frontera entre capas y se evita atribuir a SP1--SP2 evidencia física que no poseen.
