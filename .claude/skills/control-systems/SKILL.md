---
name: control-systems
description: Convenciones de teoría de control para el TFM - estabilidad de Lyapunov e ISS, CBF, MPC, LQR, consenso y conectividad algebraica, modelo continuo frente a ejecución muestreada, y wrench/grasp/caging en transporte cooperativo. Úsala al escribir, revisar o implementar cualquier ley de control, argumento de estabilidad o acoplamiento estrategia-planta (SP2 y SP3).
---

# Sistemas de control

## 1. La distinción que atraviesa todo el TFM

**Modelo matemático continuo ≠ ejecución digital muestreada.** `AGENTS.md` §3.2
lo exige y es donde más se falla.

- Un resultado de estabilidad en tiempo continuo no se transfiere sin más a la
  implementación. Si lo afirmas, declara el periodo de muestreo, el retardo y
  por qué la propiedad sobrevive (discretización exacta, paso suficientemente
  pequeño con cota, o análisis muestreado propio).
- **Nunca escribas «sin reloj» ni «asíncrono» a secas.** El sistema
  implementado es digital. Formúlalo como *ausencia de rondas globales
  síncronas* o *ausencia de planificación por lotes*.
- Distingue el tiempo de la dinámica de la planta del tiempo de la dinámica de
  decisión. Si se acoplan, di a qué escala y con qué separación temporal
  (singular perturbation, o directamente reconoce que no la hay).

## 2. Estabilidad: qué hay que decir para poder decirlo

Antes de escribir «estable», responde: **¿estable qué, respecto a qué, y en qué
región?**

| Afirmación | Lo que exige |
|---|---|
| Estabilidad de Lyapunov | $V$ candidata explícita, definida positiva, $\dot V \le 0$ en un dominio declarado, y el dominio |
| Asintótica | Además $\dot V < 0$, o LaSalle con el conjunto invariante identificado |
| Exponencial | Cotas $c_1\|x\|^2 \le V \le c_2\|x\|^2$, $\dot V \le -c_3\|x\|^2$, y las constantes |
| ISS | Función de clase $\mathcal{KL}$ y ganancia $\gamma$ respecto a la entrada declarada |
| Pasividad | Puerto (entrada, salida) explícito y función de almacenamiento |

Si no tienes una de estas, la propiedad es *observada en simulación*, y así se
escribe: «no se observó divergencia en las N corridas», no «el sistema es
estable». Ver `claims-evidence-guard`.

**Convergencia de una dinámica de decisión** es otra cosa que la estabilidad de
la planta. No las mezcles en la misma frase ni en la misma proposición.

## 3. Consenso y topología

- $\lambda_2(L)$ es la conectividad algebraica del Laplaciano del grafo de
  comunicación **estático**. Si el grafo cambia (movimiento, radio $R^{com}$,
  fallos), $\lambda_2$ de un instante no gobierna el comportamiento: hace falta
  conectividad conjunta en intervalos acotados, o decláralo como limitación.
- La tasa de consenso depende de $\lambda_2$; enunciarlo exige grafo no
  dirigido y conexo, o el equivalente dirigido (fuertemente conexo y balanceado).
- **Partición permanente:** bajo un grafo partido, una política que sólo usa la
  información de su componente no puede garantizar optimalidad global en todas
  las instancias. Es un límite del contrato de información, no del algoritmo, y
  se enuncia así.
- Declara siempre $R^{sens}$ y $R^{com}$ y la relación entre ellos
  ($R^{com} > R^{sens}$ en el piloto AWS: 3,2 m y 1,8 m).

## 4. CBF, MPC, LQR y QP

- **CBF.** La garantía de seguridad exige: $h$ con grado relativo declarado,
  condición $\dot h \ge -\alpha(h)$ con $\alpha$ de clase $\mathcal{K}$,
  conjunto seguro invariante, y **factibilidad del QP**. Un QP infactible no da
  seguridad: di qué se hace en ese caso (relajación con holgura penalizada,
  parada segura) y con qué frecuencia ocurrió.
- **MPC.** Declara horizonte, coste terminal, restricción terminal y si hay o no
  garantía de factibilidad recursiva. Sin coste/restricción terminal, no
  afirmes estabilidad nominal; di que es MPC sin garantía formal, que es una
  opción legítima y honesta.
- **LQR.** Es óptimo **para el modelo lineal y la ponderación $Q,R$ elegidos**.
  Declara $Q$ y $R$ y que la optimalidad es respecto a ese criterio, no del
  sistema real ni del no lineal.
- **Conmutación MILP–QP.** Si el esquema conmuta entre modos, la estabilidad del
  conmutado no se sigue de la de cada modo. Dwell time, o decláralo como
  limitación.

## 5. Transporte cooperativo: contacto

El TFM debe declarar **un modo primario** y validarlo completo (`AGENTS.md` §3.3):

- **Prehensil / rígido:** matriz de agarre (*grasp matrix*), reparto de wrench,
  formación. Fija una convención de marcos para poses y wrench y **mantenla en
  todo el documento**.
- **No prehensil:** caging y empuje. Cierre de forma (*form/force closure*),
  condiciones de caging, fricción declarada con su modelo y su coeficiente.

**No mezcles ambos bajo una única prueba de estabilidad** sin modelar
explícitamente sus diferencias de contacto y restricciones. Son problemas con
espacios de restricción distintos.

Toda magnitud física con unidad SI: wrench en N y N·m, masa en kg, carga útil en
kg, velocidades en m/s y rad/s.

## 6. Arquitectura: lo que este TFM no hace

- **Sin FSM global de alto nivel.** Prefiere campos vectoriales, dinámicas
  continuas, activaciones suaves o mecanismos asíncronos locales.
- **White-box.** Estados, payoffs, restricciones, parámetros y leyes de control
  interpretables. Si una ganancia se ajustó a mano, dilo y di sobre qué criterio.
- **Distribuido de verdad:** estado propio, percepción local, mensajes vecinales.
  Un optimizador central sólo como baseline u oráculo experimental, y etiquetado
  como tal en cada figura donde aparezca.
- Sin RL multiagente como método principal.

## 7. Antes de afirmar nada

Contrasta con `claims-evidence-guard`. Las palabras `estable`, `robusto`,
`converge`, `garantiza`, `en tiempo real` disparan la comprobación completa.
`robusto` sin una definición métrica detrás es la más cara de todas.
