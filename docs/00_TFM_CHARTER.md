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

- **RQ1 — Coaliciones y heterogeneidad:** ¿Bajo qué condiciones de demanda, heterogeneidad, recursos y parámetros de la dinámica emergen coaliciones factibles sin déficit ni sobrerreclutamiento persistente?
- **RQ2 — Acoplamiento y comunicación:** ¿Cómo modifican el acoplamiento decisión–movimiento y la comunicación local el equilibrio, el tiempo de formación y el rendimiento del transporte?
- **RQ3 — Factibilidad física:** ¿Cómo deben incorporarse fuerza, torque y geometría de contacto para distinguir una coalición nominalmente válida de otra físicamente ejecutable?
- **RQ4 — Degradación y resiliencia:** ¿Cómo se degrada el sistema ante congestión, batería limitada, retardos, pérdidas de paquetes y fallos parciales de robots?
- **RQ5 — Coste de la descentralización:** ¿Cuál es el coste computacional, comunicativo y operacional de la descentralización frente a un oráculo central y a referentes distribuidos comparables?

## 6. Hipótesis operacionales

Las hipótesis finales deben fijarse después de ejecutar pilotos; no deben incluir umbrales arbitrarios sin justificación.

- **HP:** Una ley distribuida que combine dinámicas poblacionales, información espacial local y certificados físicos de factibilidad puede producir coaliciones de cardinalidad y capacidad adecuadas para transportar cargas heterogéneas, con estabilidad operacional y un desempeño competitivo frente a métodos centralizados y distribuidos de referencia.
- **H1:** El payoff con umbrales de déficit y exceso recluta recursos suficientes sin sobreasignación persistente cuando la instancia es factible.
- **H2:** Incorporar un certificado físico específico de la modalidad —soporte, rigidez y wrench para Cargo; contacto unilateral y confinamiento para empuje/caging— reduce coaliciones nominalmente válidas pero físicamente inviables.
- **H3:** El acoplamiento espacial conserva su ventaja bajo comunicación local por encima de una región crítica de conectividad.
- **H4:** La recoalición local recupera la tarea tras un fallo parcial cuando la capacidad remanente admite una coalición física.
- **H5:** El método distribuido presenta menor crecimiento de coste que el oráculo combinatorio y mantiene una calidad cuantificable al aumentar la escala.

No fijar “80 % del óptimo” o “95 % de éxito” hasta contar con un piloto, una razón industrial o una referencia que justifique esos umbrales.

## 7. Alcance priorizado

### Núcleo obligatorio

1. SP0: formulación y prueba mínima.
2. SP1: cardinalidad variable.
3. SP2: capacidades y requisitos heterogéneos.
4. SP4: transporte origen–destino con pose.
5. SP6: fallo y re-reclutamiento.
6. SP8: escalabilidad, coste de comunicación y gap frente a oráculo para instancias pequeñas.

### Extensión seleccionada

- **Modo primario Cargo:** la caja se soporta sobre varios robots y se transporta como un cuerpo compuesto; SP3--SP6 deben modelar formación rígida, reparto de soporte y wrench.
- **Rama secundaria empuje/caging:** los robots desplazan la caja mediante contactos unilaterales y trayectorias de empuje realimentadas por la pose estimada de la carga. Solo se denomina caging cuando existe un certificado de confinamiento geométrico.
- SP5 como capa de seguridad/evitación evaluada experimentalmente.

### Alcance condicionado

- SP7, tráfico multi-coalición completo, se trata como estudio exploratorio o trabajo futuro salvo evidencia suficiente.
- La rama empuje/caging queda como extensión de evidencia objetivo C y no comparte automáticamente las garantías formales del modo Cargo.
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
