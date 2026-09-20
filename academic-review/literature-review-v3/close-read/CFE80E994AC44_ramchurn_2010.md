# Ficha de evidencia — CFE80E994AC44

- **Estado:** `lectura_cercana_verificada`.
- **Referencia:** Ramchurn, S. D., Polukarov, M., Farinelli, A., Truong, N. C.,
  & Jennings, N. R. (2010). *Coalition Formation with Spatial and Temporal
  Constraints*. In *Proceedings of the 9th International Conference on
  Autonomous Agents and Multiagent Systems* (pp. 1181–1188).
  https://dblp.org/rec/conf/atal/RamchurnPFTJ10
- **Nota bibliográfica:** `1838186.1838191` es el identificador del registro
  de ACM/DL; no se presenta como DOI resoluble.
- **Localizadores revisados:** resumen e introducción, p. 1; formulación y
  evaluación, pp. 1–8.
- **Papel en la revisión:** baseline de SP1 con rutas, cargas de trabajo y
  plazos; no evidencia de transporte físico.

El artículo define CFSTP: agentes limitados forman, disuelven y reforman
coaliciones para tareas espacialmente distribuidas, con carga de trabajo,
duración, plazo y eficiencia dependiente de la coalición. Demuestra NP-hardness
por contener Team Orienteering como caso especial, formula un MIP para
instancias pequeñas y propone heurísticas anytime. En su conjunto experimental,
las heurísticas completan en promedio 97 % de las tareas en casos de 20 agentes
y 300 tareas (p. 1).

**Uso permitido.** Justifica que una coalición con restricciones espaciales y
temporales no se reduce a asignación uno-a-uno, y que un MIP puede actuar como
oráculo acotado mientras una heurística atiende instancias mayores.

**Límites.** El resultado pertenece a una abstracción de agentes/tareas de
respuesta a emergencias. No modela contacto carga-robot, wrench, cinemática de
AMR ni tráfico de varias cargas; el 97 % no es transferible al TFM sin replicar
generador, métrica y condiciones.
