# Plan: diagramas SP0--SP8 a ancho completo

## Objetivo

Recomponer los nueve diagramas cenitales de resultados para que ocupen todo el ancho útil de la memoria VIU, conserven aproximadamente su altura y aprovechen el espacio adicional para separar mejor robots, cargas, flechas, fórmulas y leyendas.

## Alcance

- Definir una geometría TikZ compartida de ancho `\linewidth` para SP0--SP8.
- Aumentar ligeramente la altura y el tamaño de los robots sin alterar la gramática visual común.
- Mantener las escenas como esquemas conceptuales; no añadir resultados cuantitativos ni afirmaciones nuevas.
- Compilar con LuaLaTeX y revisar visualmente las nueve figuras en el PDF final.

## Riesgos y controles

- **Desbordamiento horizontal:** descontar el grosor del marco al calcular la unidad horizontal.
- **Paginación:** limitar el crecimiento vertical a aproximadamente un 5 %.
- **Colisiones de etiquetas:** revisar cada página renderizada y ajustar solo los elementos conflictivos.
- **Trazabilidad científica:** conservar fórmulas, variables, pies y etiquetas existentes.

## Criterios de aceptación

- Los nueve lienzos alcanzan visualmente el ancho completo del cuerpo de texto.
- Ninguna figura introduce desbordamientos nuevos ni texto recortado.
- Flechas, nodos y leyendas tienen mayor legibilidad y respiración.
- La memoria compila y el PDF final se actualiza en las rutas de entrega.

## Validación realizada

- Compilación estable con `thesis/build.ps1 -SkipBiber`: 66 páginas A4.
- Renderizado a 150 dpi de las nueve páginas que contienen SP0--SP8.
- Revisión visual individual de marcos, nodos, flechas, fórmulas, leyendas y pies.
- Eliminación de los desbordamientos introducidos inicialmente en SP5 y SP8.
- Sin cambios en afirmaciones, notación científica ni matriz de evidencia: el cambio es exclusivamente gráfico.

## Segunda pasada solicitada

El 15 de julio de 2026 se reabre el plan para:

- aumentar de nuevo la altura de los nueve diagramas;
- alcanzar el ancho exacto de `\linewidth` sin el descuento preventivo anterior;
- recomponer por completo las Figuras 8, 9 y 10 para eliminar cruces, solapamientos y densidad visual innecesaria.

La nueva composición separará estados, decisiones y perturbaciones en zonas funcionales con una única dirección de lectura.

## Validación de la segunda pasada

- Escala horizontal: `\linewidth/13.5`; el borde exterior del marco coincide con los 15 cm útiles.
- Escala vertical: incremento de `0.84 cm` a `1.00 cm` por unidad lógica.
- Figuras 8--10 recompuestas y renderizadas individualmente a 180 dpi.
- SP0--SP8 renderizados y revisados individualmente a 150 dpi.
- Las advertencias locales de las leyendas de las Figuras 9 y 10 fueron eliminadas.
- Compilación estable: 67 páginas A4 y ninguna advertencia nueva en SP0--SP8.
- No se modificaron afirmaciones, resultados, notación ni niveles de evidencia.

## Estado

Segunda pasada completada el 15 de julio de 2026.
