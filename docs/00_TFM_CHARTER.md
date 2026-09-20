# 00 — TFM Charter

## 1. Identidad del trabajo

- **Alumno:** Jorge Luis Mayorga Taborda.
- **Director:** José Ignacio Iñíguez Amigot.
- **Título administrativo vigente:** Coordinación distribuida local de múltiples AMR para el transporte cooperativo de cargas heterogéneas en entornos industriales.
- **Título técnico de trabajo recomendado:** Coordinación distribuida acoplada basada en juegos poblacionales para la formación de coaliciones y el transporte cooperativo de cargas heterogéneas mediante AMR.

El título administrativo procede de la solicitud formal. El título técnico puede emplearse internamente para delimitar la contribución, pero no debe sustituir al oficial sin aprobación.

## 2. Problema central

Una flota de robots móviles con capacidades heterogéneas debe transportar cargas con requisitos heterogéneos de masa, geometría, soporte y pose. Algunas cargas exceden la capacidad individual y requieren una coalición. La solución debe seleccionar y reclutar robots, conducirlos hacia la carga, establecer una configuración cooperativa, transportar la carga y recuperarse de perturbaciones usando información local y sin un coordinador central durante la operación.

## 3. Pregunta principal de investigación

¿Puede una dinámica distribuida basada en juegos poblacionales, acoplada a leyes continuas de movimiento y alimentada por información local, formar coaliciones factibles y ejecutar transporte cooperativo de cargas heterogéneas con garantías parciales de convergencia/estabilidad y un rendimiento competitivo frente a métodos centralizados y distribuidos de referencia?

## 4. Contribución nuclear

La contribución nuclear debe ser una, precisa y demostrable:

> Una formulación de juego poblacional/potencial con restricciones de coalición y capacidad, acoplada a un campo vectorial de movimiento, que permita la formación distribuida de coaliciones y su adaptación ante cambios o fallos.

Las aportaciones complementarias —caging, reparto de wrench, obstáculos, tráfico y red imperfecta— deben demostrar el alcance de la contribución nuclear, no convertirse en contribuciones independientes desconectadas.

## 5. Preguntas de investigación

- **RQ1 — Formación distribuida:** ¿Bajo qué condiciones de demanda, heterogeneidad, roles de contacto, información vecinal y parámetros de la dinámica se forman coaliciones factibles sin déficit ni sobrerreclutamiento persistente?
- **RQ2 — Ejecución cooperativa:** ¿Cómo deben acoplarse reclutamiento, aproximación, contacto, estabilización y control de pose para transportar una carga sin líder físico permanente y dentro de las restricciones mecánicas y de seguridad?
- **RQ3 — Planificación y tráfico:** ¿Cómo pueden coordinarse robots libres, robots en reunión y coaliciones en transporte para resolver prioridades, cruces, bloqueos, congestión y replanteamientos con información local?
- **RQ4 — Degradación y resiliencia:** ¿Cómo se degrada y recupera el sistema ante batería limitada, fallos parciales, cambios de tarea, retardos y pérdidas de paquetes?
- **RQ5 — Coste de la descentralización:** ¿Cuál es el coste computacional, comunicativo y operacional de la descentralización frente a un oráculo central y a referentes distribuidos comparables?

## 6. Hipótesis operacionales

Las hipótesis finales deben fijarse después de ejecutar pilotos; no deben incluir umbrales arbitrarios sin justificación.

- **HP:** Una ley distribuida que combine dinámicas poblacionales, información espacial local y certificados físicos de factibilidad puede producir coaliciones de cardinalidad y capacidad adecuadas para transportar cargas heterogéneas, con estabilidad operacional y un desempeño competitivo frente a métodos centralizados y distribuidos de referencia.
- **H1:** En SP1, un payoff con déficit, exceso, utilidad de tarea, costes de espera/cambio y un certificado de rol/contacto recluta recursos suficientes sin sobreasignación persistente cuando la instancia es factible.
- **H2:** En SP2, incorporar un certificado físico específico de la modalidad —soporte, rigidez y wrench para Cargo; contacto unilateral y confinamiento para empuje/caging— reduce coaliciones nominalmente válidas pero físicamente inviables y permite ejecutar el transporte bajo los supuestos declarados.
- **H3:** En SP3, la coordinación local de rutas, reservas y prioridades reduce conflictos observables, aunque la no observabilidad remota limita las garantías globales bajo red imperfecta.
- **H4:** La recoalición local recupera la tarea tras un fallo parcial cuando la capacidad remanente admite una coalición física y existe una ruta de sustitución segura.
- **H5:** El método distribuido presenta menor crecimiento de coste que el oráculo combinatorio y mantiene una calidad cuantificable al aumentar la escala.

No fijar “80 % del óptimo” o “95 % de éxito” hasta contar con un piloto, una razón industrial o una referencia que justifique esos umbrales.

## 7. Alcance priorizado

El TFM se organiza en tres subproblemas canónicos. Las campañas históricas conservan sus códigos `sp0`--`sp8` únicamente como identificadores técnicos de artefactos; no constituyen nueve subproblemas vigentes.

### SP1 — Formación distribuida de coaliciones

Decide qué robots atienden cada carga, cuántos se necesitan, qué rol o contacto asume cada uno, cuándo conviene esperar o iniciar, y cuándo abandonar o cambiar de coalición. El método debe aproximar la referencia global mediante estado propio, percepción local y mensajes vecinales. Este SP contiene el problema de reclutamiento y el certificado previo de factibilidad de la coalición.

### SP2 — Ejecución y transporte cooperativo

Con la coalición formada, los robots se aproximan, se acoplan, estabilizan la carga, generan una velocidad común, preservan contactos y restricciones físicas, navegan sin líder físico permanente, reconfiguran la geometría, sustituyen miembros degradados o fallidos y completan el desacoplamiento. El modo primario es **Cargo**, con carga soportada como cuerpo compuesto, formación rígida y reparto de wrench. Empuje/caging permanece como extensión secundaria y requiere su propio modelo de contacto y confinamiento.

### SP3 — Planificación y tráfico de múltiples coaliciones

Coordina simultáneamente robots libres, robots reuniéndose y coaliciones que transportan cargas de tamaños distintos. Incluye pasillos, cruces, prioridades, bloqueos, congestión, nuevas tareas y replanteamientos. La escala, el coste computacional/comunicativo y la degradación de red se evalúan aquí y transversalmente en SP1--SP3; no forman un cuarto SP.

### Alcance condicionado

- La validación dinámica completa se concentra en Cargo; empuje/caging queda en evidencia objetivo C salvo resultados adicionales.
- La planificación multi-coalición continua y completa se limita a la evidencia disponible; las garantías de exclusión discreta no se transfieren automáticamente a cuerpos continuos.
- No se promete optimalidad global del sistema acoplado completo.

## 8. Criterios de éxito del TFM

El TFM es exitoso si entrega:

1. formulación matemática consistente y notación estable;
2. algoritmo distribuido implementado y reproducible;
3. al menos un resultado formal no trivial para un caso bien delimitado;
4. comparación justa con baselines adecuados;
5. experimentos con datos, incertidumbre y casos adversos;
6. análisis honesto de limitaciones y regiones de fallo;
7. memoria compatible con VIU, con al menos la mitad del cuerpo dedicada a resultados, análisis y validación.

## 9. No objetivos

- Resolver todos los subcampos de MRTA, manipulación cooperativa, MAPF y redes imperfectas con una única prueba.
- Reemplazar control de bajo nivel, planificación, percepción y comunicaciones por una única palabra “juego”.
- Demostrar SOTA mediante una sola simulación.
- Usar CoppeliaSim como sustituto de análisis formal o estadístico.
- Presentar resultados generados o modificados manualmente sin trazabilidad.
