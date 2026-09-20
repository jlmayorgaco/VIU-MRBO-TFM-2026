# Ficha de evidencia — CEE02184AAFCA

- **Estado:** `lectura_cercana_verificada`.
- **Referencia:** Palmer, A. W., Hill, A. J., & Scheding, S. J. (2018).
  *Modelling Resource Contention in Multi-Robot Task Allocation Problems with
  Uncertain Timing*. In *2018 IEEE International Conference on Robotics and
  Automation (ICRA)* (pp. 3693–3700).
  https://doi.org/10.1109/ICRA.2018.8460981
- **Localizadores revisados:** resumen, motivación y formulación, p. 2;
  evaluación descrita en secciones IV–V.
- **Papel en la revisión:** puente SP1–SP3 para incertidumbre y recursos
  mutuamente excluyentes.

El artículo modela tiempos de viaje y ejecución como variables aleatorias y
calcula distribuciones condicionadas por el orden de acceso a recursos. Compara
aproximaciones analíticas con Monte Carlo y con un tratamiento determinista en
dos problemas MRTA. Entre los recursos motivadores figuran intersecciones y
puntos de carga, donde varios robots no pueden operar simultáneamente.

**Uso permitido.** Justifica que congestión y tiempo incierto deben entrar en
el coste de asignación, no añadirse únicamente después de decidir las tareas.

**Límites.** Es un marco de evaluación del coste agnóstico al optimizador; no
forma coaliciones físicas, no evita colisiones por sí solo y depende de
supuestos distribucionales que deben verificarse antes de transferirlo.
