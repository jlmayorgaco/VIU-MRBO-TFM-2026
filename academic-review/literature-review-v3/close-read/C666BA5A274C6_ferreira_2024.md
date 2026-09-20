# Ficha de evidencia — C666BA5A274C6

- **Estado:** `lectura_cercana_verificada`.
- **Versión:** se inspeccionó el manuscrito arXiv:2109.03089v1; se identificó
  la versión de registro posterior en IEEE Access.
- **Referencia de registro:** Ferreira, B. A., Petrović, T., Orsag, M.,
  Martínez-de Dios, J. R., & Bogdan, S. (2024). *Distributed allocation and
  scheduling of tasks with cross-schedule dependencies for heterogeneous
  multi-robot teams*. IEEE Access, 12, 74327–74342.
  https://doi.org/10.1109/ACCESS.2024.3404823
- **Localizadores revisados:** resumen, alcance y comparadores, pp. 1–2;
  evaluación y conclusión del manuscrito, pp. 15–16.
- **Papel en la revisión:** puente SP1–SP3 para asignación, rutas y precedencias.

El estudio representa la planificación como una variante del vehicle routing
problem para tareas `XD[ST-SR-TA]`: dependencias entre calendarios, un robot por
tarea y planificación extendida en el tiempo. La solución CBM-pop distribuye
una metaheurística evolutiva con intercambio de conocimiento. El manuscrito la
compara con Gurobi como oráculo acotado y con una subasta distribuida; incluye
benchmarks y un caso simulado de invernadero. En ese caso se reportan 10
ejecuciones por método y mejoras medias modestas en makespan/coste junto con
menor tiempo de CPU (p. 15).

**Uso permitido.** Fundamenta que precedencias, tiempos de transición y rutas
deben entrar en la asignación, y que el oráculo exacto solo es viable en
instancias acotadas.

**Límites.** La clase evaluada usa tareas de un solo robot; no resuelve reparto
de carga ni contacto cooperativo. El caso es simulado, presupone intervalos
entre misiones y deja para trabajo futuro llegadas asíncronas, perturbaciones y
fallos. Los resultados cuantitativos se atribuyen al manuscrito inspeccionado;
antes de citarlos como datos de la versión final se debe comprobar que no
cambiaron durante la revisión editorial.
