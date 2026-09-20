---
name: math-rigor
description: Disciplina de enunciado y demostración para el TFM - cuándo algo es proposición, lema u observación; qué hipótesis deben aparecer; qué huecos invalidan una demostración; cómo se escribe una demostración de síntesis. Úsala al redactar o revisar cualquier proposición, lema, definición, demostración o paso algebraico en los .tex del TFM.
---

# Rigor matemático

Un enunciado formal es un contrato: si las hipótesis se cumplen, la conclusión
se sigue. Todo lo que no está en las hipótesis no puede usarse en la
demostración, y todo lo que la demostración usa debe estar en las hipótesis.
La mayoría de los fallos de este repositorio son de ese tipo, no algebraicos.

## 1. Entornos disponibles

De `Subdocuments/SP1/viu-mrob-thesis.sty`: `definicion`, `proposicion`,
`teorema`, `lema`, `corolario`, `observacion` (numerados por sección).

| Entorno | Cuándo |
|---|---|
| `definicion` | Introduce un objeto o una propiedad. No afirma nada. |
| `lema` | Resultado auxiliar cuyo único fin es sostener otro. Si no se usa después, sobra. |
| `proposicion` | Resultado propio, autocontenido, con demostración. Es el caso normal aquí. |
| `teorema` | Resérvalo. En un TFM de 6 ECTS, casi nada lo merece; llamar teorema a una proposición invita a que el tribunal lo trate como tal. |
| `corolario` | Se sigue en dos líneas de lo anterior. Si necesita más, es una proposición. |
| `observacion` | Comentario verdadero pero no demostrado formalmente. **No es un resultado.** No se cita como si lo fuera. |

En el cuerpo, la demostración va como *Demostración (síntesis)*: el argumento
completo, sin los pasos rutinarios. La versión larga va al anexo. Una síntesis
no es un esquema: debe convencer, no anunciar.

## 2. Anatomía de un enunciado correcto

1. **Cuantificadores explícitos.** «Para todo mundo $w$ con $N$ AMR y $K$
   cargas tales que…». Nunca un «en general» que oculta el cuantificador.
2. **Hipótesis numeradas y usadas.** Si H3 no aparece en la demostración,
   o sobra o la demostración está incompleta.
3. **Objetos definidos antes de usarse**, con el símbolo de
   `docs/05_NOTATION.md`.
4. **Conclusión falsable.** Si no puedes describir qué instancia la refutaría,
   no es un enunciado matemático.

## 3. Huecos que invalidan (los que aparecen aquí)

- **Existencia no comprobada.** Se toma un mínimo, un óptimo o un punto fijo sin
  argumentar que existe (compacidad, finitud, Weierstrass, Brouwer/Kakutani).
- **Finitud invocada sin decirlo.** «La secuencia termina» exige: la cantidad es
  monótona **y** el conjunto de perfiles es finito **y** la mejora está acotada
  inferiormente. Los tres.
- **Salto de la relajación al entero.** Que el LP sea integral en un caso no lo
  hace integral en otro. La integralidad de N1 procede de la matriz de
  incidencia bipartita totalmente unimodular; con capacidades individuales esa
  formulación deja de existir, y la propiedad no se hereda.
- **Genericidad callada.** Un argumento que falla en empates necesita o una
  regla de desempate declarada o una hipótesis de posición general.
- **Local a global.** Un óptimo local, un equilibrio unilateral o una condición
  de primer orden no dan optimalidad global. En este trabajo ese salto es
  precisamente lo que N4 estudia; no lo des por hecho en ningún otro sitio.
- **Continuo a muestreado.** Un resultado sobre la dinámica continua no vale sin
  más para su ejecución digital muestreada. Ver la habilidad `control-systems`.
- **Suficiente confundido con necesario.** Una condición que garantiza que una
  ventana no es vacía no caracteriza todas las instancias factibles. Dilo así.

## 4. Cómo se revisa una demostración ajena (o propia de hace un mes)

1. Lee el enunciado. Escribe con tus palabras qué instancia lo refutaría.
2. Tacha cada hipótesis y busca dónde se usa. Si alguna no se usa, márcalo.
3. Busca los verbos que ocultan trabajo: *claramente*, *es inmediato*,
   *análogamente*, *sin pérdida de generalidad*. En cada uno, comprueba que de
   verdad es inmediato. «Análogamente» es el escondite más común.
4. Comprueba los casos borde: $N=1$, $K=1$, conjunto vacío, empate,
   componente desconectada, capacidad nula.
5. Comprueba que la conclusión sea exactamente lo que el texto afirma después.
   El desajuste entre proposición y prosa es más frecuente que el error interno.

## 5. Números, unidades y notación

- Todo símbolo, en `docs/05_NOTATION.md`. Si es nuevo, se añade allí en el mismo
  cambio. Nunca el mismo símbolo para dos objetos (masa, número de robots,
  mensaje).
- Declara qué es $x_{ik}$ cada vez que aparece un modelo nuevo: binaria,
  fracción poblacional, probabilidad o estimación. La convención del repositorio
  es $\rho_{ik}$ para preferencia continua y $x_{ik}$ para la decisión binaria;
  $x_k$ es masa poblacional agregada.
- Toda magnitud física con unidad SI o conversión explícita.
- $\widehat{L}_F(I)$ es un **estimador numérico** de escala del operador, no una
  constante de Lipschitz demostrada. No lo uses como si lo fuera en ningún
  argumento de convergencia.

## 6. Lo que no se demuestra, no se afirma

Si un resultado es cierto pero no lo has demostrado, es *medido* o *no
afirmado*, y se escribe como tal. Ver `claims-evidence-guard`. Una `observacion`
elegante no sustituye una demostración, y el tribunal lo notará antes que nadie.
