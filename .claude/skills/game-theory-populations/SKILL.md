---
name: game-theory-populations
description: Teoría de juegos potenciales, dinámicas poblacionales (Replicator, Smith, BNN, Logit) y conceptos de equilibrio tal como se usan en este TFM - jerarquía de desviaciones h, terminales BR, brecha respecto al óptimo, y las condiciones que hay que declarar para afirmar convergencia o eficiencia. Úsala al escribir o revisar la formulación estratégica de SP1, SP3 o cualquier mecanismo de reclutamiento de coaliciones.
---

# Juegos potenciales y dinámicas poblacionales

## 1. Qué hay que declarar antes de llamarlo juego

Un juego no está definido hasta que están los cinco:

1. **Jugadores.** ¿Los AMR individuales, o masas poblacionales? No es lo mismo y
   el repositorio usa ambas: $x_{ik}$ es asignación individual, $x_k$ es masa
   poblacional agregada. Nunca las intercambies (`docs/05_NOTATION.md`).
2. **Estrategias.** Conjunto y si es discreto, símplex, o mezcla.
3. **Utilidad o coste**, con su normalización y su escala.
4. **Información.** Qué observa cada jugador y cuándo. Esta es la que más se
   omite y la que define la contribución de N3.
5. **Protocolo de revisión.** Quién revisa, cuándo, y si simultáneamente.

## 2. Juego potencial

Afirmar «es un juego potencial» exige exhibir $\Phi$ y verificar la igualdad de
diferencias para toda desviación admisible del tipo declarado:

| Tipo | Qué garantiza |
|---|---|
| Potencial exacto | $u_i(s_i', s_{-i}) - u_i(s_i, s_{-i}) = \Phi(s_i', s_{-i}) - \Phi(s_i, s_{-i})$ |
| Potencial ordinal | Sólo coincide el signo. Basta para terminación, no para cotas de eficiencia |
| Potencial ponderado | Con pesos $w_i$; declararlos |

Consecuencia legítima: **la dinámica de mejor respuesta termina** si el espacio
de perfiles es finito, $\Phi$ es monótona y la mejora está acotada inferiormente.
Los tres, dichos. Ver `math-rigor` §3.

Consecuencia **no** legítima: que el punto final sea bueno. Un juego potencial
garantiza terminación en un equilibrio, no eficiencia. Si quieres hablar de
eficiencia, mide la brecha o acota el precio de la anarquía; no lo insinúes.

## 3. La jerarquía de desviaciones

Es la contribución de N4 y el sitio donde más fácil se resbala.

- $h = 1$ (BR): desviaciones unilaterales. Su punto fijo es un equilibrio de
  Nash en estrategias puras.
- $h = 2$ (2BR): desviaciones bilaterales; intercambios entre dos AMR.
- $h = 3$ (C3) y superiores: coalicionales de orden $h$.

Reglas de escritura:

- $h_c^\star$ es **el primer orden conectado en el que existe una mejora**. No
  mide la magnitud de esa mejora. Si el texto sugiere lo contrario, corrígelo.
- Usa $h_c^\star$ en leyendas de figura, nunca $h^\star$.
- Tercera categoría: «**no detectado hasta $h=3$**», nunca «$h_c^\star > 3$».
  La búsqueda estaba truncada; no hallado no equivale a inexistente. Esta
  limitación se enuncia **una vez**, en Limitaciones.
- Un terminal BR no es un óptimo. Es un perfil del que nadie mejora **solo**.
  Decirlo así cada vez cuesta cinco palabras y evita la pregunta del tribunal.
- «Propuestas de reasignación», no «propuestas físicas»: N4 no actúa sobre la
  planta.

## 4. Dinámicas poblacionales

Las cuatro familias del trabajo, con lo que cada una exige declarar:

| Dinámica | Clase | Hay que declarar |
|---|---|---|
| Replicator | Imitativa | Que las estrategias con masa nula nunca entran: el borde del símplex es invariante. Es una limitación, no un detalle |
| Smith | Basada en excesos de pago | La función de tasa y su recorte; es Nash-estacionaria y positivamente correlacionada |
| BNN | Basada en excesos | Excesos respecto al pago medio; positivamente correlacionada |
| Logit | Perturbada | El ruido $\eta$ o temperatura. Su reposo es un **equilibrio logit**, no un Nash. Nunca lo llames Nash |

Para todas: **positive correlation** y **Nash stationarity** son las dos
propiedades que justifican usarlas con un potencial. Si el argumento de
convergencia se apoya en ellas, cítalas explícitamente.

Y para todas: son dinámicas en **tiempo continuo** sobre masas poblacionales. La
implementación es discreta, con población finita. Ese salto se declara
(`control-systems` §1).

## 5. Equilibrios: no confundir

- **Nash puro** ≠ **equilibrio logit** ≠ **reposo de la dinámica** ≠ **óptimo
  social**. Cuatro objetos distintos. Nombra el que corresponde.
- **vGNE** (equilibrio generalizado de Nash variacional) es un refinamiento con
  restricciones acopladas: al citarlo, di que es *variacional* y qué
  restricciones acopla. El método del repositorio es
  «PD-vGNE-seeking + $\mathcal{R}$», nunca «PD-vGNE distribuido + R».
- Si el mecanismo cierra con una operación central $\mathcal{R}$, entonces el
  resultado **no** es puramente distribuido. Decláralo, y declara que su coste
  no está en el eje horizontal de la figura de Pareto.

## 6. Comparación con baselines

CBBA y GRAPE son los baselines. Al compararlos:

- Sólo sobre el **soporte común** de mundos con solución certificada. La macro
  lo dice en el nombre (`GapCommon` frente a `GapOwn`).
- Reporta siempre las tres caras: factibilidad, brecha y coste de comunicación
  en bytes/AMR. Ganar en una y callar las otras dos es el error clásico.
- Una ventaja frente a una heurística está condicionada a esa heurística y al
  orden en que recorre las cargas. No es superioridad general del enfoque.
- La atomicidad importa: el LP admite participación fraccionaria; la coalición
  ejecutable exige $x_{ik} \in \{0,1\}$. La diferencia entre ambos objetivos es
  estructural, no ruido numérico.

## 7. Al escribir

Pasa después `tfm-voice` (registro) y `claims-evidence-guard` (respaldo). Las
palabras `converge`, `equilibrio`, `óptimo`, `eficiente`, `garantiza` disparan
la comprobación completa.
