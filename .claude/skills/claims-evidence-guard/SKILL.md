---
name: claims-evidence-guard
description: Verifica que toda afirmación de optimalidad, convergencia, estabilidad, robustez, escalabilidad o superioridad esté respaldada por una definición formal y por evidencia trazable antes de escribirla. Úsala siempre que redactes o revises una frase que afirme rendimiento, garantía o ventaja en cualquier .tex del TFM, y antes de cerrar un capítulo.
---

# Guardia de afirmaciones

`AGENTS.md` §3.2 lo fija: **no afirmar optimalidad, convergencia, estabilidad,
robustez o escalabilidad sin una definición formal y evidencia correspondiente.**
Esta habilidad convierte esa regla en un procedimiento. Es la que protege la
defensa: una afirmación sin respaldo es la pregunta que hará el tribunal.

## 1. Palabras que disparan la comprobación

`óptimo` · `optimalidad` · `converge` · `convergencia` · `estable` ·
`estabilidad` · `robusto` · `robustez` · `escalable` · `escalabilidad` ·
`garantiza` · `asegura` · `siempre` · `nunca` · `mejor que` · `supera a` ·
`equivalente a` · `sin pérdida de` · `en tiempo real` · `distribuido` (cuando
implica ausencia de coordinador).

## 2. Procedimiento, por afirmación

**Paso 1 — Clasifica.** ¿Es *demostrada*, *medida* o *no afirmada*?

| Clase | Qué exige | Cómo se escribe |
|---|---|---|
| Demostrada | Enunciado formal y demostración, con hipótesis explícitas | «Bajo H1–H3, … (Proposición N)» |
| Medida | Macro generada desde una campaña reproducible, con soporte declarado (n, semilla, configuración) | «Sobre los 878 mundos del soporte común, la brecha mediana fue 9,4 %.» |
| No afirmada | Nada de lo anterior | No se escribe. O pasa a Limitaciones como pregunta abierta. |

**Paso 2 — Localiza la evidencia.** Busca la fila en `docs/04_CLAIMS_EVIDENCE.md`.
Si la afirmación no está ahí: si tienes la evidencia, **añade la fila** en el
mismo cambio; si no la tienes, **no escribas la frase**.

**Paso 3 — Comprueba el soporte de la cifra.** Las macros declaran su soporte en
el nombre (`...GapCommon` frente a `...GapOwn`). Una comparación entre métodos
sólo es válida sobre el **soporte común**. Citar `GapOwn` como si fuera
comparable es el error más caro de este repositorio.

**Paso 4 — Acota el alcance.** Toda medida vale en su dominio de generación:
rango de $n$, distribución de capacidades, topología, semillas. Si el texto
generaliza más allá, o se acota o se retira.

**Paso 5 — Una limitación, una vez.** La limitación fuerte va una sola vez, en su
sitio, no repetida como cautela preventiva en cada oración (`tfm-voice` §1.2).

## 3. Reformulaciones canónicas

| No escribas | Escribe |
|---|---|
| «El método converge.» | «La dinámica de potencial es no decreciente y el espacio de perfiles es finito, luego la secuencia termina (Prop. N).» |
| «El método es robusto.» | «La factibilidad se mantuvo por encima del 99 % en los tres regímenes de CV ensayados.» |
| «Escala bien.» | «El coste de comunicación creció con pendiente medida $b$ (IC 95 % $[\cdot]$) en el rango $n \in [\cdot]$.» |
| «Supera a CBBA.» | «Sobre los 878 mundos del soporte común, la brecha mediana fue 9,4 % frente a 40,3 %; a cambio transmitió 25 791 bytes/AMR frente a 9 089.» |
| «Sin reloj» / «asíncrono» | «Sin rondas globales síncronas ni planificación por lotes.» El sistema implementado es digital y muestreado. |
| «Óptimo.» | «Óptimo del programa (4); la relajación es integral por unimodularidad total.» Nunca «óptimo» a secas. |
| «Es la contribución principal.» | Enuncia el resultado. El lector juzga su importancia. |

## 4. Trampas específicas de este TFM

- **No hallado no equivale a inexistente.** Escribe «no detectado hasta $h=3$»,
  nunca «$h_c^\star > 3$».
- **Factibilidad no es calidad.** Que exista coalición ejecutable no implica
  brecha pequeña.
- **Ventaja condicionada.** Una ventaja frente a una heurística está condicionada
  a esa heurística y al orden en que recorre las cargas; no es superioridad
  general.
- **Coste no contabilizado.** Si el eje de una figura no incluye el coste de
  $\mathcal{R}$ o de cualquier cierre central, decláralo en el pie.
- **Ninguna cifra a mano.** Si el número no procede de `generated/*.tex` o de
  `canonical_metrics.tex`, es un fallo de procedimiento aunque sea correcto.

## 5. Antes de cerrar un capítulo

Recorre las palabras del §1 con `grep -n` sobre el `.tex` y contrasta cada
aparición con `docs/04_CLAIMS_EVIDENCE.md`. Si una fila de ese documento ha
quedado sin frase que la use, o una frase sin fila, la trazabilidad está rota:
arréglala antes de compilar la versión definitiva.
