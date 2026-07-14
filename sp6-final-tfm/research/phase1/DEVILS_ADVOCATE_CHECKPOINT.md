# Devil's Advocate Report — Checkpoint 1

## Veredicto: REVISE

No se identifican fallos críticos inevitables, pero la propuesta no debe pasar a búsqueda y diseño definitivo sin mantener abiertas las condiciones siguientes.

## Problemas mayores

### 1. SOTA todavía no está definido

- **Tipo:** alcance y sesgo.
- **Problema:** la expresión «ganar al SOTA» puede conducir a seleccionar comparadores favorables o incompatibles.
- **Impacto:** una victoria frente a un baseline débil no sustentaría la afirmación principal.
- **Corrección:** definir en Phase 2 un protocolo de elegibilidad, buscar contraevidencia y congelar comparadores antes del ensayo.

### 2. Brecha entre equilibrio continuo y coalición discreta

- **Tipo:** lógica y método.
- **Problema:** la convergencia de una dinámica poblacional sobre un símplex no implica una coalición entera físicamente válida.
- **Impacto:** el teorema podría no respaldar el sistema ejecutado.
- **Corrección:** formalizar la regla de cierre y probar o medir la pérdida entre equilibrio, cierre y factibilidad.

### 3. Composición decisión–control no demostrada

- **Tipo:** teoría.
- **Problema:** estabilidad del juego y estabilidad del controlador por separado no garantizan estabilidad al cambiar coaliciones.
- **Impacto:** el núcleo escalonado quedaría sin garantía.
- **Corrección:** formular condiciones de separación temporal, conmutación o estabilidad práctica y declarar qué queda solo observado.

### 4. Riesgo de pseudodistribución

- **Tipo:** validez de constructo.
- **Problema:** estimaciones, cierre, selección de candidatos o métricas pueden consultar información global.
- **Impacto:** la comparación distribuida sería semánticamente inválida.
- **Corrección:** inventario de información por operación y medición explícita de mensajes, vecindarios y sincronización.

### 5. Atribución causal del rendimiento

- **Tipo:** explicación alternativa.
- **Problema:** la mejora puede proceder del filtro físico o del controlador y no del juego.
- **Impacto:** se sobreafirmaría el aporte de teoría de juegos.
- **Corrección:** ablaciones con el mismo cierre y controlador, cambiando solo el motor de decisión.

### 6. Alcance excesivo para un TFM

- **Tipo:** factibilidad.
- **Problema:** equilibrio nuevo, grafos variables, control de carga, fallos y SOTA completo pueden superar el tiempo disponible.
- **Impacto:** profundidad insuficiente o resultados incompletos.
- **Corrección:** una clase de juego, un equilibrio principal, una clase de grafos y una planta planar; extensiones como exploratorias.

## Problemas menores

- Los márgenes prácticos aún no están justificados.
- «Sin violaciones físicas» debe convertirse en restricciones observables.
- El coste computacional debe medirse externamente, no estimarse de forma analítica solamente.
- Un único simulador limita la validez externa.

## Contraargumento más fuerte

Una subasta distribuida o un método de optimización vecinal con el mismo filtro de factibilidad y el mismo controlador podría igualar o superar la propuesta. En ese caso, el juego poblacional añadiría complejidad teórica y comunicación sin mejorar la misión.

## Evidencia ausente

- Identificación verificable del SOTA realmente comparable.
- Prueba de novedad del juego o equilibrio.
- Teorema de relación entre equilibrio, cierre discreto y factibilidad.
- Propiedad de estabilidad bajo reconfiguración.
- Justificación ingenieril de márgenes.

## Stress tests

| Prueba | Resultado |
|---|---|
| Eliminar la afirmación de SOTA | La contribución teórica todavía podría ser válida |
| Invertir la hipótesis | Es creíble que subasta u optimización distribuida ganen |
| Aplicar a otra planta o 3D | No generaliza sin nueva evidencia |
| Eliminar el juego en una ablación | Prueba decisiva para atribución |
| Pregunta «¿y qué?» | La relevancia existe solo si mejora misión física, no solo convergencia |

## Condiciones para pasar

1. Mantener la superioridad como hipótesis y publicar también un resultado nulo o negativo.
2. Seleccionar un único concepto principal de equilibrio después de la investigación.
3. Congelar un protocolo de elegibilidad de baselines.
4. Diseñar ablaciones para juego, cierre y control.
5. Declarar toda dependencia global.
6. Reducir el dominio teórico a supuestos demostrables en un TFM.
