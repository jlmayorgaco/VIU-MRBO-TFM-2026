# Revisión de voz humana de SP1.N1

## Propósito y resultado observable

Eliminar giros impersonales y frases de plantilla del extracto de diez páginas
de SP1.N1. El PDF final debe conservar cifras, hipótesis, referencias y alcance,
pero la explicación debe sonar escrita por el autor y no por una plantilla.

## Contexto y archivos canónicos

- `thesis/sp1_levels_23p/main.tex` contiene el texto evaluado.
- `scripts/results/sp1_levels/n1_v2/` contiene los resultados que no deben cambiar.
- `docs/04_CLAIMS_EVIDENCE.md` limita las conclusiones permitidas.
- `reports/2026-08-06-sp1-n1-viu-nonspecialist-review.md` registra la puerta VIU
  ya superada.

## Alcance y no alcance

Se revisa la prosa narrativa y los rótulos que producen tono automático. No se
cambian datos, métodos, contrastes, ecuaciones ni configuración experimental.
Tampoco se revisan N2--N4.

## Supuestos y preguntas resueltas

- El perfil de revisión es manuscrito técnico en español.
- Se admiten términos técnicos cuando son necesarios y están explicados.
- La repetición del sustantivo correcto es preferible a rotar sinónimos.
- El texto académico puede usar voz impersonal, pero no debe ocultar el sujeto,
  el número de casos ni la acción observada.

## Diseño matemático/técnico

No hay cambios matemáticos. Cada oración revisada conservará sujeto concreto,
acción medible, dato y límite. Se evitarán verbos ceremoniales como «sustentar»,
«actuar como auditor» o «certificar una alternativa» cuando una formulación
directa pueda expresar el mismo hecho.

## Plan experimental

No se repiten experimentos. La validación compara las macros y cifras antes y
después, recompila el PDF y ejecuta las pruebas dirigidas de SP1.N1.

## Hitos

- [x] Hito 1: inventario de patrones de escritura artificial.
- [x] Hito 2: reescritura directa de los pasajes señalados.
- [x] Hito 3: PDF de diez páginas recompilado e inspeccionado.
- [x] Hito 4: pruebas, diff y segunda lectura aprobados.

## Validación

- Buscar vocabulario de plantilla y construcciones impersonales en el LaTeX.
- Confirmar que cifras, macros y referencias no cambian.
- Compilar exactamente diez páginas y revisar visualmente las páginas afectadas.
- Ejecutar `test_sp1_levels.py` y las pruebas dirigidas de N1.

## Riesgos y mitigaciones

- **Tono demasiado coloquial:** mantener vocabulario académico y precisión.
- **Pérdida de alcance:** conservar las frases que delimitan qué no prueba N1.
- **Desbordamiento:** reemplazar frases, no añadir explicaciones redundantes.
- **Edición cosmética:** exigir que cada cambio mejore sujeto, acción o lectura.

## Registro de decisiones

- 2026-08-07: se abre una revisión independiente de voz después de la puerta
  técnica y la puerta generalista VIU.

## Progreso

Revisión completada. El PDF conserva diez páginas y la segunda auditoría no
encuentra las frases señaladas ni vocabulario de plantilla. Pasaron 32 pruebas,
el comprobador de cinco figuras TikZ protegidas y el control del registro LaTeX.
El detalle queda en `reports/2026-08-07-sp1-n1-human-voice-audit.md`.
