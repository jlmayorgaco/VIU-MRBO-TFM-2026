# Auditoría SP0--SP8 con la plantilla maestra

## 1. Regla de autoría y evidencia

El entorno naranja `contribucion` identifica una formulación, caracterización, cota, mecanismo o resultado producido dentro de este TFM. No acredita prioridad universal ni sustituye la demostración, la revisión bibliográfica o la campaña experimental. Cada caja debe declarar uno de estos estados:

- **Demostrado:** existe enunciado delimitado y prueba completa en anexos.
- **Validado empíricamente:** existe protocolo reproducible y evidencia soportada, sin elevarla a teorema.
- **Propuesto:** la formulación es propia, pero su claim permanece pendiente.
- **Conjetural:** existe una hipótesis formal aún no demostrada ni respaldada suficientemente.

Los términos “nuevo”, “original” o “propio” significan aquí que la síntesis o formulación fue desarrollada para este TFM. Solo puede afirmarse prioridad frente a la literatura como “no se identificó en el corpus verificado”, nunca como inexistencia universal.

## 2. Cadena de información

Se usa la cadena común `OBSERVED -> ESTIMATED -> RAW -> CLOSED -> GUARDED -> EXECUTED`. El último estado acreditado se determina por código y evidencia, no por el objetivo futuro del SP. `CLOSED` significa decisión lógica entera; `GUARDED` exige el certificado declarado; `EXECUTED` exige que la acción atraviese una planta simulada o física con control y restricciones.

## 3. Auditoría por subproblema

| SP | Incremento y contraejemplo mínimo | Último estado acreditado | Resultado formal y prueba | Evidencia empírica | Aporte propio defendible | Claim que no puede hacerse todavía |
|---|---|---|---|---|---|---|
| SP0 | Dos matchings factibles pueden ser Nash y tener costes distintos. | `CLOSED`, con ocupación agregada exacta. | Proposición de potencial/Nash, PoS/PoA, cotas e imposibilidades; pruebas en Anexo SP0. | Soportada en el dominio estático pareado. | Caracterización de la penalización, frontera de eficiencia y certificados delimitados; no un algoritmo nuevo de matching. | Arquitectura vecinal ejecutada, optimalidad de cualquier Nash o estabilidad física. |
| SP1 | Concentración `(2,0)` y dispersión `(1,1)` tienen igual déficit, pero solo la primera completa una carga. | `CLOSED` mediante QR con lectura global; Smith termina en `RAW`. | Cuotas realizables, degeneración bajo escasez y caso mínimo del incentivo; pruebas en Anexo SP1. | Desarrollo soportado; superioridad frente a greedy fue refutada. | Interfaz `RAW--CLOSED`, caracterización de escasez, incentivo de cuórum y operador QR auditado. | Cierre plenamente distribuido, optimalidad de QR o superioridad general. |
| SP2 | Igual cardinalidad puede aportar distinto servicio operacional. | `GUARDED` solo respecto de un umbral adimensional; no capacidad mecánica. | Alineación marginal para `E` fija y no integrabilidad genérica del score plano; prueba en Anexo SP2. | Soportada para scorers secuenciales; primal--dual no superó a greedy. | Score marginal de servicio y separación entre cobertura y completitud. | Consenso vecinal implementado, compatibilidad general, factibilidad energética, wrench, estabilidad o capacidad física. |
| SP3 | Igual capacidad escalar puede producir distinto torque realizable. | `GUARDED` por certificado planar cuasiestático; no `EXECUTED`. | Potencial de wrench y equivalencia KKT de la relajación; prueba en Anexo SP3. | Soportada para guardia y cierres ensayados; el consenso corto muestra limitación. | Juego potencial de wrench, precios de slot y guardia mecánica dentro del modelo planar. | Rigidez 3D, transporte, caging, estabilidad del sistema completo o distribución estricta. |
| SP4 | Un wrench factible en reposo no impide perder contacto o bloquearse durante el desplazamiento. | `EXECUTED` en dos capas simuladas separadas: docking dinámico y carga planar con contactos fijos. | Potencial fuerte/VE del juego congelado y estabilidad local de pose bajo wrench exacto; pruebas en Anexo SP4. | Soportada para docking y para el estrato abierto de transporte; no para la cadena extremo a extremo. | Juego de vivacidad, cierre/guardia y servorregulación de pose con residual de wrench explícito. | Reducción de tiempo por acoplamiento extremo a extremo, contacto/fricción real, estimación distribuida de pose, caging o robustez general. |
| SP5 | Una trayectoria rápida puede ser insegura o romper la interfaz de contacto. | Objetivo `EXECUTED` con guardia de seguridad; no acreditado. | La garantía CBF pertenece al modelo citado; no a la adaptación pendiente. | Pendiente. | Diseño candidato de filtro compatible con la modalidad física. | Seguridad general, invariancia digital o factibilidad permanente del QP. |
| SP6 | Una reparación lógica puede no restaurar soporte, wrench o contacto. | Objetivo `EXECUTED` tras recuperación; no acreditado. | No existe cota de recuperación soportada. | Pendiente. | Diseño candidato de re-reclutamiento sujeto a certificado remanente. | Recuperación garantizada, cota temporal o tolerancia universal a fallos. |
| SP7 | Ausencia de colisión instantánea no excluye bloqueo persistente. | Exploratorio; no acreditado. | No existe resultado formal propio soportado. | Pendiente y condicionado. | Juego candidato de congestión/prioridad como extensión exploratoria. | Solución general de tráfico, completitud u optimalidad tipo CBS/ECBS. |
| SP8 | Un resultado con agregados globales puede volverse inconsistente en una red fragmentada. | No existe estado terminal acreditado para la arquitectura local completa. | Solo cotas auxiliares de SP0; no una garantía transversal bajo red imperfecta. | Pendiente. | Diseño de auditoría calidad--cómputo--comunicación y método local candidato. | Escalabilidad general, robustez o menor crecimiento sin curvas reproducibles. |

## 4. Decisión sobre los recuadros naranjas

- SP0--SP3 pueden contener cajas de aporte demostrado o validado, siempre con alcance y enlace al anexo o a la evidencia.
- SP4 puede contener cajas demostradas o validadas únicamente para los alcances C4A--C4D; SP5--SP8 conservan el estado vigente en la matriz de claims.
- Un baseline, una ecuación tomada de literatura o una garantía heredada no se encierra como aporte propio.
- Una adaptación se atribuye como “inspirada en” la fuente y no hereda sus teoremas.

## 5. Cobertura de la plantilla maestra

La estructura canónica conserva título, introducción, figura, oráculo, tabla crítica, juego/mecanismo, control, protocolo, resultados y transición. Dentro de esos bloques se añaden:

1. contraejemplo incremental;
2. cadena de información y estado terminal;
3. estado explícito del aporte;
4. verificación, resultado primario, gap, ablación y resultado negativo;
5. estado de reproducibilidad;
6. separación de límite teórico y límite práctico.

Por la restricción VIU de 50--80 páginas, los doce campos de la tabla maestra son un contrato de contenido. En el cuerpo pueden agruparse en seis columnas legibles siempre que no se pierdan rol, arquitectura, paradigma, información, complejidad, garantía, límites y estado; el detalle completo permanece en la auditoría metodológica y en los artefactos reproducibles.
