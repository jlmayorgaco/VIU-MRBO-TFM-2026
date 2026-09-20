# Plan V4 - Auditoría y fortalecimiento de la revisión de literatura

**Fecha:** 2026-09-16  
**Estado:** completado  
**Alcance:** versión independiente y auditable de la revisión. No modifica la memoria ni los artefactos V3 existentes mientras el árbol de trabajo contiene cambios ajenos en curso.

## Objetivo

Conservar íntegramente como referencia visual las nueve páginas de
`MROB_literature_review_reworked (2).pdf` y entregar una revisión V4 que
separe de forma comprobable el mapeo descriptivo, la evidencia técnica y la
auditoría de la brecha. Las cifras deben derivarse del corpus disponible y
toda limitación no cerrada debe permanecer visible.

## Hipótesis de trabajo y límites

- El corte disponible contiene 3.014 identidades de descubrimiento, 244
  documentos analíticos, 59 trabajos canónicos y 20 fichas de lectura cercana;
  el generador V4 debe comprobar esas cifras contra los datos de entrada.
- La cobertura WoS F01/F02 y la consulta arXiv siguen parciales. No se
  declarará exhaustividad, saturación ni ausencia universal.
- No se inventará una segunda codificación humana, evidencia por celda ni un
  análisis de sensibilidad como resultado si no se ejecuta realmente. El
  documento especificará esos controles como pendientes y generará los
  registros necesarios para completarlos.
- Los gráficos del PDF de referencia no se redibujan ni rasterizan: se
  conservan como páginas vectoriales embebidas.

## Entregables

1. `academic-review/literature-review-v4/`: protocolo congelable, codebook,
   registro adversarial, tabla de denominadores, script de derivación y
   comprobaciones.
2. `output/pdf/literature-review/MROB_literature_review_v4_audited.pdf`:
   PDF que incluye sin alteración las páginas de referencia y un addendum V4
   con el protocolo operativo que prevalece sobre la narrativa metodológica
   anterior.
3. Informe de control que distinga hechos derivados, evidencia técnica
   disponible, controles aún pendientes y riesgo residual.

## Fases

- [x] Revisar contrato científico del TFM, protocolo, matriz de afirmaciones,
  notación, plantilla de SP, corpus V3 y PDF visual.
- [x] Derivar y comprobar los denominadores del corte actual.
- [x] Crear codebook de cuatro estados y registro adversarial sin convertir
  ausencia documental en ausencia de capacidad.
- [x] Redactar protocolo V4 de mapeo sistemático, revisión técnica anidada y
  auditoría adversarial de la brecha.
- [x] Construir el addendum PDF y verificar visualmente todas sus páginas.
- [x] Ejecutar pruebas pertinentes, comprobar hashes y revisar el diff propio.

## Criterios de aceptación

- Cada número del addendum procede de una tabla generada o se marca como
  regla prospectiva.
- El PDF mantiene las nueve páginas originales y no elimina ninguna figura.
- La distinción `yes/partial/no/unclear` queda definida con evidencia admisible.
- La conclusión de la brecha se limita al corpus y el corte declarados.
- El build falla ante un desajuste de los denominadores críticos.
