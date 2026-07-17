# Campaña confirmatoria Cargo extremo a extremo

## Propósito y resultado observable

Cerrar la principal brecha científica del TFM mediante una ejecución única que conecte selección heterogénea, estimación vecinal, cierre de coalición, aproximación de uniciclos, verificación mecánica, transporte planar seguro, fallo simple, re-reclutamiento y reanudación. El resultado será reproducible desde una configuración versionada, producirá datos crudos, tablas, figuras y manifiesto, y actualizará la memoria sin extrapolar sus garantías locales.

## Contexto y archivos canónicos

Rigen `docs/00_TFM_CHARTER.md`--`docs/05_NOTATION.md`, `docs/07_SP_SECTION_TEMPLATE.md`, las plantas de `src/viu_mrob_tfm/sp5/payload_transport.py`, la recuperación de `src/viu_mrob_tfm/sp6/experiment.py` y el protocolo de red de `src/viu_mrob_tfm/sp8/experiment.py`. La revisión científica de partida está en `docs/11_FULL_MANUSCRIPT_REVIEW.md` y en la conversación del 17 de julio.

## Alcance y no alcance

Incluye una carga Cargo, robots heterogéneos, comunicación vecinal con retardo y pérdida, dinámica de uniciclo para aproximación/reemplazo, carga rígida planar durante transporte, obstáculo circular, fallo de un miembro y continuación. No incluye contacto 3D, flexibilidad, percepción visual, ROS 2, hardware, empuje/caging, múltiples cargas simultáneas ni garantías globales del sistema híbrido.

## Supuestos y preguntas resueltas

Los contactos se fijan tras el docking y cada robot acoplado aporta una fuerza planar limitada. La pose de la carga se mide exactamente; la información estratégica sobre capacidad y estado se intercambia mediante mensajes. El fallo abre el certificado, congela la carga y activa una reparación local. La pregunta confirmatoria es si el método vecinal completo conserva una tasa de misión y un coste medibles frente a información perfecta, sin guardia mecánica, sin reparación y una referencia central.

## Diseño matemático/técnico

El estado híbrido registra `RECRUIT`, `DOCK`, `TRANSPORT`, `RECOVER` y `DONE/FAILED` solo como fases del simulador, no como una FSM de control propuesta. Los robots ejecutan uniciclo dinámico muestreado con saturación de velocidad, aceleración y par equivalente. La carga satisface `M qdd + D qd = W_apl + W_ext`; el wrench se reparte por mínimos cuadrados acotados. La guardia geométrica filtra la velocidad antes del reparto. El protocolo vecinal conserva vistas versionadas y aplica retardo/pérdida con semillas separadas.

Invariantes: finitud; límites de velocidad y par; hashes idénticos entre métodos; decisión basada solo en la vista declarada; contacto fijo después del acoplamiento; ausencia de reparación geométrica posterior; fallos y timeouts en el denominador; contabilidad exacta de mensajes; carga inmóvil mientras el certificado está abierto.

## Plan experimental

Piloto con tres semillas y campaña confirmatoria con 30 semillas por celda. Factores: `N={4,8,12}`, escenarios `open`, `obstacle`, `network_degraded`, `failure`. Métodos: vecinal completo, información perfecta, sin guardia, sin reparación y referencia central. Métricas: éxito extremo a extremo, tiempo de misión/recuperación, error final, colisión, distancia mínima, residual de wrench, saturación, energía, mensajes, bytes y CPU. Comparaciones pareadas con IC bootstrap, McNemar/Wilcoxon, tamaños de efecto y Holm. Las semillas confirmatorias se congelan antes de abrirse.

## Hitos

- [x] Hito 1 — contrato, configuración y modelo integrado definidos.
- [x] Hito 2 — simulador y pruebas de invariantes implementados.
- [x] Hito 3 — piloto aprobado y protocolo confirmatorio congelado.
- [x] Hito 4 — campaña ejecutada y artefactos generados.
- [x] Hito 5 — matriz de evidencia y memoria sincronizadas.
- [x] Hito 6 — entorno reproducible, pruebas, PDF y re-revisión cerrados.

## Validación

Ejecutar `python -m pytest -q`; ejecutar la configuración smoke y la confirmatoria; verificar auditoría `passed`; regenerar tablas y figuras; compilar `thesis/build.ps1`; renderizar páginas modificadas; comprobar ausencia de citas indefinidas, overfull y caracteres de control. Finalmente reconstruir desde un árbol generado con `git archive` cuando el conjunto canónico esté versionado.

## Riesgos y mitigaciones

El principal riesgo es fabricar complejidad física no respaldada. Se reutiliza la planta planar auditada y se declaran sus límites. La campaña puede revelar bajo éxito; se conserva como resultado negativo. Si una referencia central usa información global, se presenta como techo. El presupuesto se protege añadiendo una síntesis transversal, no otro SP.

## Registro de decisiones

- 2026-07-17: cerrar exclusivamente la rama Cargo.
- 2026-07-17: priorizar composición y distribución operativa sobre nuevos teoremas.
- 2026-07-17: mantener separadas las garantías locales; la campaña prueba compatibilidad empírica, no un teorema híbrido global.

## Progreso

La campaña confirmatoria quedó congelada y ejecutada con 30 semillas, cuatro
escenarios, tres tamaños de flota y seis métodos: 360 mundos y 2160 ejecuciones.
La auditoría automática pasó todos sus controles. El método distribuido
completó 359/360 misiones sin colisión; las ablaciones aislaron el efecto de la
guardia física y de la reparación. La hipótesis de ventaja temporal espacial no
recibió soporte y se registró como resultado negativo. La memoria, la matriz de
evidencia, el resumen y las conclusiones ya reflejan estos resultados. Resta
cerrar la suite completa, compilar y revisar visualmente el PDF, y documentar
el estado de versionado necesario para una reconstrucción desde archivo Git.

La suite completa terminó con 66 pruebas aprobadas. Se añadió un lock mínimo de
seis dependencias exactas y la campaña confirmatoria conserva protocolo,
semillas, datos, trazas, auditoría y hashes. El PDF final no contiene referencias
indefinidas, errores ni cajas desbordadas; el cuerpo ocupa 80 páginas y los
anexos 19. Las páginas modificadas se inspeccionaron como imágenes. La
reconstrucción mediante `git archive` queda condicionada a incorporar al control
de versiones los archivos actualmente no rastreados; no se alteró el índice Git
de un árbol compartido con cambios ajenos.
