# Guía de lectura — comparación homogénea controlada

Aquí MILP y Hungarian reciben exactamente el mismo problema. Las figuras de calidad y factibilidad sí permiten una comparación algorítmica dentro de esta reducción.

## `comparison_distance_parity.png` / `comparison_distance_parity.pdf`

**Pregunta.** ¿Recuperan ambos métodos el mismo coste de distancia?

**Cómo leerla.** La diagonal representa igualdad exacta. La caja indica el error absoluto máximo.

**Límite.** La equivalencia solo vale para capacidad homogénea y cuotas enteras reducibles a slots.

## `comparison_paired_solver_time.png` / `comparison_paired_solver_time.pdf`

**Pregunta.** ¿Qué método consume más tiempo de solver en el mismo mundo?

**Cómo leerla.** Puntos sobre la diagonal indican mayor tiempo MILP; el ratio P50 resume la diferencia pareada.

**Límite.** Los tiempos dependen de hardware, carga del sistema y versiones.

## `comparison_runtime_scaling.png` / `comparison_runtime_scaling.pdf`

**Pregunta.** ¿Cómo evolucionan los tiempos con el tamaño?

**Cómo leerla.** Líneas sólidas: medianas; bandas: P05–P95. Una tendencia log–log solo se dibuja con pendiente positiva y R²≥0.50.

**Límite.** Las pendientes no son complejidad asintótica demostrada.

## `comparison_feasibility_agreement.png` / `comparison_feasibility_agreement.pdf`

**Pregunta.** ¿Clasifican igual la factibilidad de misión completa?

**Cómo leerla.** Las dos series usan las mismas instancias; Δ cuenta desacuerdos.

**Límite.** No evalúa factibilidad mecánica ni transporte.
