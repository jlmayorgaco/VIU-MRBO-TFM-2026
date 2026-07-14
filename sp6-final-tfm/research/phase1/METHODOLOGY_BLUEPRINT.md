# Methodology Blueprint

## Paradigma y diseño

- **Paradigma:** positivista.
- **Tipo:** cuantitativo, formal y experimental.
- **Diseño:** benchmarking pareado con ablaciones, análisis de estabilidad y simulación reproducible.
- **Datos:** primarios sintéticos generados por el nuevo simulador; la literatura solo fundamenta modelos y comparadores.

## Unidad de análisis

Una unidad experimental será un mundo congelado: conjunto de AMR, cargas, estados iniciales, grafo o secuencia de grafos, trayectoria, perturbaciones y semilla. Todos los métodos recibirán el mismo mundo.

## Modelo provisional

- N AMR en un plano y K tareas de transporte.
- Grafo de comunicación fijo o variable, conectado o conjuntamente conectado según el teorema elegido.
- Estado local con posición, capacidad, estimación de carga, tarea o rol y mensajes vecinales.
- Juego poblacional o potencial sobre tareas o roles.
- Dinámica de revisión distribuida con información vecinal.
- Regla auditable de preferencias continuas a coalición discreta.
- Carga rígida planar con masa, inercia y geometría variables.
- Control cooperativo distribuido y restricciones explícitas de esfuerzo.
- Realimentación del desempeño físico hacia los pagos o la reconfiguración.

El concepto de equilibrio y la clase exacta de planta se congelarán después de la revisión bibliográfica y antes de programar la campaña confirmatoria.

## Experimentos

### E1 — Juego, equilibrio y grafo

Variar topología, conectividad, tamaño y condiciones iniciales. Medir potencial o brecha de equilibrio, convergencia, estabilidad, mensajes y factibilidad de la coalición.

### E2 — Control distribuido y cargas

Variar masa, inercia, geometría, trayectoria y perturbaciones. Medir misión completada, RMSE de seguimiento, desacuerdo de esfuerzos, saturación, energía y estabilidad numérica.

### E3 — Integración extremo a extremo

Comparar la arquitectura completa con ablaciones sin realimentación física, sin dinámica poblacional, sin restricción gráfica y con una referencia centralizada. Incluir baselines distribuidos seleccionados y verificados en Phase 2.

### E4 — Fallos y reconfiguración

Variar pérdida de enlaces, retardo, cambios de topología y fallo de un AMR. Medir recuperación, carga perdida, tiempo adicional, mensajes y éxito final.

## Comparadores

Las categorías provisionales son:

1. heurística distribuida simple;
2. subasta o consenso distribuido;
3. optimización distribuida;
4. método basado en juegos distinto del propuesto, si existe implementación comparable;
5. referencia centralizada como cota;
6. ablaciones del método propuesto.

La lista final se congelará tras verificar publicaciones, código, semántica del problema y presupuestos de información.

## Métricas

### Primaria

Probabilidad de completar físicamente la misión dentro del tiempo límite y sin violaciones declaradas.

### Secundarias

- brecha de equilibrio o potencial;
- iteraciones y tiempo de convergencia;
- error de seguimiento;
- energía o esfuerzo normalizado;
- tiempo de misión;
- mensajes y bytes transmitidos;
- reconfiguraciones;
- tasa de coaliciones asignadas pero no ejecutables;
- coste computacional observado.

## Muestreo y separación de datos

- Generador de mundos versionado.
- Semillas comunes entre métodos.
- Conjunto piloto para depuración y elección de márgenes.
- Conjunto confirmatorio sellado y abierto solo después del freeze.
- Tamaño fijado por precisión del intervalo o análisis de potencia basado en el piloto.
- Regla de parada independiente del signo o significación del efecto.

## Análisis

- Contrastes pareados por mundo.
- Efectos con intervalos de confianza, no solo valores p.
- Modelo jerárquico o errores agrupados cuando varios tratamientos compartan mundo.
- Corrección de multiplicidad para hipótesis secundarias.
- Análisis por intención de tratar: fallos y timeouts permanecen en el denominador.
- Análisis confirmatorios separados de los exploratorios.

## Criterio de superioridad

La arquitectura solo superará al SOTA distribuido si vence al mejor comparador elegible en la métrica primaria por encima de un margen práctico y satisface simultáneamente los márgenes de no inferioridad secundarios. Los recursos de cómputo, frecuencia, información y comunicación deberán ser comparables.

## Validez

| Riesgo | Mitigación |
|---|---|
| Ajuste a un simulador | escenarios variados, parámetros declarados y validación independiente posterior |
| Baseline débil o mal ajustado | código verificable, presupuesto común y búsqueda de hiperparámetros simétrica |
| Confusión entre capas | ablaciones y métricas intermedias |
| HARKing o p-hacking | preregistro, conjunto confirmatorio sellado y multiplicidad |
| Pseudodistribución | inventario de toda lectura global y medición de mensajes |
| Error de implementación | pruebas unitarias, oráculos pequeños e invariantes |

## Ética y registro

- No intervienen personas ni datos personales; no se prevé evaluación IRB.
- El protocolo confirmatorio se preregistrará localmente y, si el autor lo autoriza, en OSF antes de abrir el conjunto final.
- Se conservarán manifiestos, versiones, hashes, configuración, semillas, datos crudos y scripts de análisis.

## Limitaciones de diseño

- Simulación planar.
- Contacto y sensores simplificados.
- Generalización limitada a las clases de grafos, cargas y plantas declaradas.
- La novedad teórica y el SOTA elegible permanecen provisionales hasta Phase 2.
- Ningún resultado simulado acreditará seguridad funcional ni validación industrial.
