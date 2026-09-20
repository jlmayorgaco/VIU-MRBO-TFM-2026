# Auditoría de cierre narrativo de SP1

Fecha: 2026-08-15
Artefacto: `output/pdf/sp1_levels/SP1_levels_N1_N2_N3_N4.pdf`

## Decisión

SP1 se congela como una cadena de cuatro preguntas: cardinalidad, atomicidad,
localidad informativa y localidad estratégica. No se incorporan más métodos ni
campañas. Los números y las conclusiones conservan el alcance registrado en
`docs/04_CLAIMS_EVIDENCE.md`.

## Controles de cierre

| # | Control | Evidencia | Estado |
|---:|---|---|---|
| 1 | Una pregunta por N1--N4 | Guía de lectura y aperturas de N2--N4 | CUMPLE |
| 2 | Una transición causal entre niveles | Cierres N1/N2/N3 y última página | CUMPLE |
| 3 | N3 se lee como frontera de información | Apertura, dos estrategias y síntesis de N3 | CUMPLE |
| 4 | Rol científico de F-I--F-IV explícito | Primera página de N4 | CUMPLE |
| 5 | $h^\star$ es el resultado central | E9, distribución y vínculo con gap | CUMPLE |
| 6 | Atlas físico antes de las ecuaciones | Páginas 28--30 antes del desarrollo formal | CUMPLE |
| 7 | Claims sin herencias indebidas | Tabla final y auditorías N4 | CUMPLE |
| 8 | Comparación continua tras cierre entero | E7 y texto de alcance | CUMPLE |
| 9 | Tabla final de estado de claims | Última página | CUMPLE |
| 10 | Cierre conceptual sin detalles de ejecución | Última página | CUMPLE |

## Frontera conservada

SP1 termina en una coalición lógica y atómica. Contacto, reparto de wrench,
estabilidad, seguridad continua y transporte quedan en SP2. La categoría
`h^\star>3` conserva el significado de búsqueda truncada y no certifica
optimalidad.

## Validación cerrada

- PDF independiente: 48 páginas exactas y render completo.
- Revisión visual: páginas 2, 12, 18, 26--30, 41--42 y 48 sin solapes ni cortes.
- Pruebas específicas: 17 superadas.
- Batería completa: 296 superadas.
- Memoria VIU: 120 páginas; compilación terminada.
- Figuras TikZ protegidas: 5 de 5 verificadas por `thesis/build.ps1`.

Los avisos tipográficos de la memoria completa son preexistentes y no afectan al
artefacto SP1: su log no contiene cajas desbordadas ni referencias indefinidas.
