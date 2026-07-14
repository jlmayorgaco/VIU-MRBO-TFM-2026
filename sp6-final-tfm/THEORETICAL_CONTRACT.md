# Contrato teórico provisional

## Regla central

El TFM no presentará teoría de juegos, grafos, dinámicas poblacionales y control distribuido como cuatro temas yuxtapuestos. La contribución será el acoplamiento entre decisión y ejecución:

1. el grafo determina la información disponible;
2. un juego poblacional actualiza preferencias o roles;
3. una regla de cierre forma una coalición discreta;
4. el controlador distribuido ejecuta el transporte;
5. el resultado físico realimenta utilidades y reconfiguración.

## Función de cada pilar

| Pilar | Pregunta que responde | Resultado exigible |
|---|---|---|
| Grafos | ¿Quién puede conocer el estado de quién? | Condiciones de conectividad y coste de comunicación |
| Teoría de juegos | ¿Qué objetivo local induce una coalición útil? | Equilibrio, potencial o estabilidad estratégica |
| Dinámicas poblacionales | ¿Cómo evolucionan las preferencias sin coordinador central? | Invariancia, convergencia o cota explícita |
| Control distribuido | ¿Puede la coalición mover la carga? | Seguimiento, estabilidad y reparto del esfuerzo |

## Modelo mínimo

- Grafo de comunicación posiblemente variable G(t)=(V,E(t)).
- Estado local por AMR: posición, capacidad, carga estimada y preferencia de tarea.
- Distribución poblacional sobre tareas o roles.
- Utilidad que combine demanda, coste de desplazamiento, capacidad y congestión.
- Dinámica de revisión poblacional ejecutable con información vecinal.
- Regla explícita para convertir preferencias continuas en una coalición física.
- Modelo planar de carga rígida con masa, inercia y geometría variables.
- Controlador cooperativo distribuido con información local y mensajes vecinales.
- Realimentación que penalice coaliciones incapaces de ejecutar la misión.

## Hipótesis provisionales

### Hipótesis central

Una arquitectura que acopla formación de coaliciones mediante un juego poblacional sobre grafos y control cooperativo distribuido aumenta el éxito físico de transporte frente a una asignación que no realimenta la ejecutabilidad de la carga.

### H1 — Decisión sobre grafos

Bajo las condiciones de conectividad declaradas, la dinámica poblacional distribuida converge o permanece dentro de una cota medible respecto de su referencia con información completa.

### H2 — Factibilidad de la coalición

La realimentación procedente de la capa de control reduce las coaliciones asignadas que no pueden ejecutar el transporte.

### H3 — Ejecución distribuida

Para cargas y perturbaciones dentro del dominio declarado, el error de seguimiento y el desacuerdo de esfuerzos permanecen acotados.

### H4 — Robustez

La reconfiguración poblacional conserva una fracción mayor de misiones ante cambios del grafo o pérdida de un AMR que una arquitectura sin reasignación.

## Obligaciones de demostración

1. Definir qué información es local, vecinal y global.
2. Probar o acotar invariancia y convergencia de la dinámica poblacional.
3. Declarar la relación entre equilibrio del juego y factibilidad física.
4. Establecer una propiedad de estabilidad para el controlador distribuido.
5. Analizar qué ocurre cuando la coalición cambia durante la ejecución.
6. Separar propiedades demostradas, observadas numéricamente y no verificadas.

## Campaña experimental propuesta

### E1 — Dinámica poblacional y topología

Variar topología, conectividad y tamaño de red. Medir distancia a la referencia, potencial, convergencia, mensajes y factibilidad de la asignación.

### E2 — Control distribuido de cargas heterogéneas

Variar masa, inercia, geometría y trayectoria. Medir éxito de transporte, error de seguimiento, reparto del esfuerzo, saturación y energía.

### E3 — Acoplamiento extremo a extremo

Comparar la arquitectura completa con ablaciones sin realimentación física, sin dinámica poblacional y con información global. La métrica principal será la misión física completada.

### E4 — Reconfiguración

Introducir pérdida de enlaces, retardo y fallo de un AMR. Medir recuperación, carga perdida, tiempo adicional y mensajes.

## Exclusiones iniciales

- No afirmar control distribuido si una operación decisiva consulta el estado global sin declararlo.
- No identificar convergencia de preferencias con éxito físico.
- No convertir simulación planar en evidencia de seguridad funcional.
- No añadir aprendizaje automático salvo que responda una pregunta no cubierta por los cuatro pilares.
- No crear una campaña independiente por concepto; habrá un experimento integrado y ablaciones.
