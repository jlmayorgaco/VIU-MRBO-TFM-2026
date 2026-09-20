# Ficha de evidencia — C60F209AB33AE

- **Estado:** `lectura_cercana_verificada`.
- **Referencia:** Liu, L., & Shell, D. A. (2013). *Optimal Market-based
  Multi-Robot Task Allocation via Strategic Pricing*. Robotics: Science and
  Systems IX. https://doi.org/10.15607/RSS.2013.IX.033
- **Localizadores revisados:** resumen y definición del problema, p. 1;
  experimentos, p. 6; limitaciones y conclusiones, p. 8.
- **Papel en la revisión:** baseline distribuible de asignación uno-a-uno.

El mecanismo adopta la perspectiva de un vendedor que ajusta precios para
resolver conflictos entre clientes. Para el problema de asignación estudiado,
alcanza el óptimo global y presenta complejidad fuertemente polinómica
`O(n^3 log n)`. Los experimentos usan 50 ensayos y comparan con Hungarian,
AUCTION y un método previo de intercambios (p. 6). Los autores advierten que
resolver empates exige comunicación exitosa y que obtener el óptimo con
información estrictamente local sigue siendo problemático (p. 8).

**Uso permitido.** Sirve como ejemplo de que “market-based” no significa
necesariamente heurístico ni subóptimo, siempre que el problema conserve la
estructura de asignación de su demostración.

**Límites.** No es un solver de coaliciones multirrobot, capacidades acumuladas
o tareas que requieren varios robots. Por ello no reemplaza el ILP/MILP de SP1
ni valida transporte, colisiones o tolerancia a pérdida de mensajes.
