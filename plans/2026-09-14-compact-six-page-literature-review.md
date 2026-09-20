# Revisión sistematizada V3 — restauración visual y ampliación a seis páginas

## Objetivo

Ampliar la síntesis compacta de cuatro a seis páginas, recuperar la familia de
figuras del documento de referencia y recalcularlas con los derivados V3. El
corte legado de 59 registros se conserva únicamente como comparación
documental, sin mezclarlo con el corpus V3 de 244 documentos cuando las
categorías no son equivalentes.

## Decisiones de trazabilidad

- Las series V3 se generan desde los CSV congelados de
  `academic-review/literature-review-v3/data/`.
- Los únicos valores legados reutilizados son los explícitos en el `.tex`
  entregado por el autor: corpus 59, ventana fechada 54, cuatro conteos de
  familias, ocho discriminantes de cobertura y cinco posiciones ordinales de
  autoridad.
- No se reconstruye ni superpone una serie anual histórica inexistente. El
  dashboard legado se reproduce en estructura, pero sus seis paneles se
  alimentan con V3 y declaran la ausencia del archivo crudo anterior.
- Posiciones del mapa metodológico y presupuesto de centralización son
  proyecciones descriptivas de señales de título/resumen, no medidas de
  rendimiento ni pruebas de arquitectura.
- La matriz de capacidades se limita a fuentes con ficha de lectura cercana.

## Paginación prevista

1. Método, resumen bilingüe, mapa metodológico y comparación de cortes.
2. Matriz de capacidades y modalidades físicas.
3. Intersecciones, autoridad por etapa, red-team y brecha defendible.
4. Dashboard temporal V3 con la misma lógica de seis paneles.
5. Evolución metodológica, madurez de evidencia y cadena de certificados.
6. Agenda experimental, fronteras cuantitativas, limitaciones, referencias y
   declaraciones.

## Definición de terminado

- [x] Script reproducible, manifiesto y valores legados congelados.
- [x] Fuente LaTeX y PDF de exactamente seis páginas.
- [x] Sin cajas desbordadas, referencias indefinidas ni caracteres ausentes.
- [x] Suite de pruebas de revisión académica aprobada.
- [x] Las seis páginas renderizadas e inspeccionadas visualmente.
- [x] Entregable final copiado a `output/pdf/`.

## Cierre

**Estado:** completado el 2026-09-14.

El PDF final conserva la familia visual del informe entregado, actualiza sus
paneles con el corpus V3, mantiene el corte legado con advertencias explícitas
de comparabilidad y añade la síntesis metodológica y experimental acordada.
