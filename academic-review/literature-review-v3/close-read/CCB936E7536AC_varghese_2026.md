# Ficha de evidencia — CCB936E7536AC

- **Estado:** `lectura_cercana_verificada`.
- **Referencia:** Varghese T., G., Kochuvila, S., Kumar, N., & Prasad,
  R. R. V. (2026). *Hybrid Coordination Framework for Centralized Task
  Allocation and Execution in Heterogeneous Multi-Robot Systems*. IEEE Access,
  14, 61573–61595.
  https://doi.org/10.1109/ACCESS.2026.3680629
- **Localizadores revisados:** resumen, p. 1; formulación y arquitectura,
  pp. 4–15; conclusión y trabajo futuro, pp. 21–22.
- **Papel en la revisión:** comparador central reciente para SP1/logística.

El marco combina Shapley Value Clustering Algorithm con NSGA-II para capacidad
de carga, energía, plazos, makespan y balance. En escenarios ROS 2/Gazebo con
cinco robots heterogéneos, los autores reportan 100 % de asignación y 0,122 s de
tiempo medio de asignación. La propia conclusión reserva para trabajo futuro el
hardware, flotas mayores, coordinación descentralizada, fallos y retardos reales
(pp. 21–22).

**Uso permitido.** Es un oráculo/comparador central multiobjetivo y una lista
útil de variables operativas.

**Límites.** No es arquitectura distribuida, no demuestra escalabilidad y no
valida condiciones físicas reales. Sus porcentajes no deben denominarse prueba
industrial ni transferirse fuera de las simulaciones descritas.
