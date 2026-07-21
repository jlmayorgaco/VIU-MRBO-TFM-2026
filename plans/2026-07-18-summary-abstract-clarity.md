# Revisión de claridad del Resumen y el Abstract

## Propósito y resultado observable

Reescribir los preliminares bilingües para que un lector externo comprenda el
problema, el método, los resultados principales y los límites sin depender de
etiquetas internas ni de una sucesión de cifras. El resultado observable es
thesis/build/main.pdf recompilado, con ambas versiones entre 200 y 300 palabras
y con afirmaciones equivalentes.

## Contexto y archivos canónicos

Se aplican docs/00_TFM_CHARTER.md--docs/05_NOTATION.md, la exigencia VIU de
docs/01_VIU_REQUIREMENTS.md, la evidencia de
docs/04_CLAIMS_EVIDENCE.md y las fuentes
thesis/sections/frontmatter/01-summary.tex y
thesis/sections/frontmatter/02-abstract.tex.

## Alcance y no alcance

Incluye claridad, selección de resultados, equivalencia español--inglés,
compilación e inspección visual. No modifica datos, métodos, hipótesis,
bibliografía, título ni alcance científico.

## Supuestos y preguntas resueltas

La petición se interpreta como una corrección editorial y científica de ambos
preliminares. Se reduce la densidad numérica, se retiran dos cifras de ablaciones
cuya atribución causal es conjunta o trivial y se conservan los principales
resultados positivos y negativos registrados en la matriz de evidencia.

## Diseño matemático/técnico

No cambia la formulación. Cargo se define como transporte de una carga apoyada
sobre una coalición rígida. La arquitectura se clasifica positivamente como
híbrida y se declaran sus dependencias globales. La verificación mecánica se
describe como planar, y la integración como demostrador de compatibilidad
funcional que sustituye varios mecanismos de SP2--SP6.

## Plan experimental

No se generan experimentos. Las afirmaciones se verifican contra la matriz de
evidencia y la memoria se recompila desde sus fuentes.

## Hitos

- [x] Reescribir Resumen y Abstract con contenido equivalente y 200--300 palabras.
- [x] Compilar, revisar avisos y comprobar visualmente las páginas modificadas.

## Validación

- Conteo desde fuente: 297 palabras en el Resumen y 269 en el Abstract.
- thesis/build.ps1: compilación completa superada.
- PDF: A4, 122 páginas, sin referencias/citas indefinidas ni cajas desbordadas.
- Extracción y renderizado: páginas 2 y 3 completas, legibles y sin cortes.
- Persisten avisos preexistentes de fuentes, cajas subllenas y U+0016 fuera de
  los dos preliminares revisados.

## Riesgos y mitigaciones

La simplificación podía ocultar evidencia negativa o exagerar la integración.
Se conservaron el resultado temporal no sustentado, la tasa libre de conflictos
nula a 128 robots, los bloqueos del piloto y la limitación híbrida/distribuida.
La omisión de cifras secundarias no altera los resultados completos del capítulo
6 ni su trazabilidad.

## Registro de decisiones

- 2026-07-18: priorizar legibilidad para lectores externos y reducir las cifras.
- 2026-07-18: explicar Cargo y la verificación mecánica en lenguaje natural.
- 2026-07-18: retirar del resumen las dos cifras de ablación Cargo porque una
  retira un bloque conjunto y la otra compara continuar frente a detenerse.
- 2026-07-18: editar el inglés como prosa autónoma, con equivalencia factual y
  sin calco sintáctico frase por frase.

## Progreso

Tarea completada. Las fuentes, los conteos, la compilación, el texto extraído,
el renderizado y el diff de los dos preliminares quedaron revisados. No se
modificaron la matriz de evidencia ni la notación porque no cambió ninguna
afirmación científica ni símbolo canónico.
