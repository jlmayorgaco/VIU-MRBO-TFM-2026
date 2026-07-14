# Auditoria integral del TFM: campo y panel

Fecha: 2026-07-13<br>
Modo: revision completa, pre-entrega<br>
Manuscrito oficial: `docs/doc-05-final-report/main.tex` (`Arquitectura escalonada para la coordinacion distribuida de multiples AMR en el transporte cooperativo de cargas heterogeneas`)<br>
PDF oficial de trabajo: `docs/doc-05-final-report/main.pdf`<br>
Extension actual del PDF oficial: 78 paginas; aproximadamente 23 260 palabras extraidas.
Informe tecnico ampliado secundario: `output/pdf/TFM_SP4_v4_integrated.pdf`, 208 paginas y aproximadamente 66 188 palabras.

## Estandar y alcance

La auditoria evalua el entregable `doc-05-final-report` como TFM de ingenieria con aspiracion a maxima calificacion. El informe ampliado se usa como fuente tecnica y se revisa para detectar material que deba integrarse, corregirse o mantenerse fuera del cuerpo principal. El objetivo no es prometer una nota, sino comprobar si cada afirmacion relevante es teoricamente correcta, esta respaldada por evidencia reproducible y declara sus limites. Ninguno de los dos manuscritos se modifica durante la primera ronda.

El campo principal combina robotica movil multiagente, teoria de juegos evolutivos, control distribuido, optimizacion, seguridad basada en barreras, formacion de coaliciones y transporte cooperativo. La unidad narrativa esperada es la reduccion distribuida de un deficit fisico-economico comun.

## Riesgos editoriales pre-registrados

1. Acumulacion de SP, capas y campanas sin una tesis unica visible.
2. Confusion entre mecanismo distribuido y dependencias globales de clearing, estimacion o simulacion.
3. Extrapolacion de resultados continuos, algebraicos o cinematicos a seguridad discreta, dinamica o hardware.
4. Novedad insuficientemente separada de Quijano, Martinez y antecedentes de Smith/replicator/primal-dual.
5. Comparaciones no isopresupuestarias o evidencia estadistica insuficiente para superioridad general.
6. Inconsistencias entre resumen, contribuciones, resultados, limitaciones y conclusion.

## Panel confirmado

| Rol | Identidad configurada | Foco exclusivo |
|---|---|---|
| EIC | Tribunal de TFM con experiencia en robotica y control distribuido | Coherencia global, aporte defendible, arquitectura y suficiencia para defensa |
| R1 Metodologia | Especialista en teoria de juegos, optimizacion distribuida, CBF/HOCBF y validacion estadistica | Supuestos, pruebas, complejidad, diseno experimental, incertidumbre y reproducibilidad |
| R2 Dominio | Especialista en sistemas multi-robot, coalition formation, docking y transporte cooperativo | Novedad y correccion respecto al estado del arte de robotica multiagente |
| R3 Perspectiva | Ingenieria de sistemas y transferencia experimental | Factibilidad, integracion, escalado, observabilidad, fallos de implementacion y alcance practico |
| DA | Revisor adversarial de logica y evidencia | Contraargumento mas fuerte, overclaiming, dependencias centralizadas, seguridad discreta y suficiencia |

## Contrato

El contrato congelado se encuentra en `reviewer_full_tfm_contract.json`. Como el paquete local del skill no incluye el `reviewer/full.json` ni el esquema que documenta, este contrato replica el vocabulario reconocido y registra explicitamente la adaptacion al TFM. Los cinco revisores deben precomprometer su criterio sin ver el manuscrito y luego aplicar exactamente ese criterio con evidencia visible.
