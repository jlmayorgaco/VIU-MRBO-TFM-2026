# SP8: escala y coordinación bajo red imperfecta

## Propósito y resultado observable

Cerrar el bloque obligatorio SP8 con evidencia de nivel C, manteniendo SP7 como caso nominal de tráfico. El resultado observable será una extensión de red del juego de rutas, una campaña pareada que varíe tamaño, radio, retardo y pérdida, un oráculo exhaustivo restringido para instancias certificables, tablas y figuras generadas, pruebas formales en anexo y una sección SP8 que reemplace el protocolo pendiente.

## Contexto y archivos canónicos

Rigen `docs/00_TFM_CHARTER.md`--`docs/05_NOTATION.md`, `docs/07_SP_SECTION_TEMPLATE.md` y la evidencia SP7-C. Los resultados históricos `results/sp8/SP8_MC_*` se conservan, pero no se usarán como evidencia canónica porque agregan escalabilidad de almacén sin aislar conjuntamente radio, retardo y pérdida bajo el protocolo actual. Sus módulos se preservan como API heredada.

## Alcance y no alcance

Se estudian coaliciones rígidas abstractas que eligen entre dos rutas sobre recursos compartidos. Se varían número de robots y cargas, densidad del grafo de comunicación, retardo discreto y pérdida Bernoulli. Se mide calidad estratégica, conflictos invisibles, CPU, estado protocolario, mensajes, bytes y certificación del oráculo. No se modelan radio físico, TCP/ROS 2, colas MAC, interferencia, dinámica continua de contacto, seguridad euclídea ni consumo eléctrico real; la energía queda fuera por no disponer de una planta comparable en todos los tamaños.

## Supuestos y preguntas resueltas

Cada carga es transportada por una coalición de dos robots, de modo que `N=2K`. Cada coalición dispone de dos rutas, cada catálogo contiene al menos un perfil global sin conflictos y los costes permanecen congelados durante una ejecución estratégica. El grafo de comunicación es no dirigido y estático por mundo; los mensajes contienen versión y ruta, ocupan un número fijo de bytes y pueden retrasarse o perderse de forma independiente. La ejecución es digital y asíncrona, no libre de reloj.

## Diseño matemático/técnico

Para un grafo de comunicación `G_C`, el juego visible penaliza solo pares de rutas conflictivos conectados por una arista. Su potencial `Phi_8^G` conserva exactamente las diferencias unilaterales y toda mejora estricta termina en un Nash visible. Los conflictos entre agentes no adyacentes no aparecen en ese equilibrio; un resultado de indistinguibilidad demostrará que una partición permanente impide garantizar coordinación global en todas las instancias acopladas. Para un estado congelado retransmitido `s` veces con pérdida independiente `p_loss`, la probabilidad de no recepción es `p_loss^s`.

La implementación comparará retransmisión periódica versionada, mensajería solo por evento, mejor respuesta con información perfecta, perfil aleatorio y oráculo exhaustivo restringido. El coste protocolario local se separará del espacio `2^K` del oráculo.

## Plan experimental

Escalas previstas: `K={4,8,12,16,32,64}` coaliciones y `N=2K` robots. Regímenes: nominal, radio reducido, retardo, pérdida y combinación adversa. Se usarán 30 semillas pareadas. El oráculo enumerará todos los perfiles solo cuando `2^K` no exceda el límite versionado; fuera de ese dominio se registrará como no certificado, sin fabricar un óptimo. Hipótesis: la retransmisión mejora la tasa libre de conflictos frente a la mensajería por evento bajo degradación; la red adversa empeora la calidad frente a información perfecta; el coste por agente del protocolo se mantiene acotado por el grado y el horizonte, mientras el catálogo exhaustivo crece como `2^K`.

## Hitos

- [x] Hito 1 — fuentes canónicas, SP7 y evidencia SP8 heredada auditadas.
- [x] Hito 2 — teoría de equilibrio visible, frontera de partición y pruebas unitarias.
- [x] Hito 3 — simulador de red, oráculo restringido, métricas y humo reproducible.
- [x] Hito 4 — campaña confirmatoria, auditoría, tablas y figuras.
- [x] Hito 5 — memoria, anexo, notación y matriz de evidencia sincronizados.
- [x] Hito 6 — PDF integral compilado y revisado visualmente.

## Validación

Ejecutar pruebas de identidad de potencial, terminación, conteo de conflictos visibles/no visibles, probabilidad de retransmisión, hashes pareados, métricas finitas y respeto del límite del oráculo. Ejecutar un humo y la configuración confirmatoria, comprobar que todas las figuras/tablas proceden de datos, compilar la memoria y renderizar las páginas de SP8 y su anexo.

## Riesgos y mitigaciones

La medición de CPU de Python no es una cota asintótica y se rotulará como observación de esta implementación. El modelo de paquetes independientes no representa ráfagas ni interferencia. Un Nash visible no equivale a Nash global ni seguridad física. El oráculo es exacto solo para el catálogo binario y los tamaños enumerados. La campaña heredada no se mezclará con la nueva evidencia.

## Registro de decisiones

- 2026-07-17: extender el juego de rutas de SP7 en lugar de introducir otra planta, para aislar el efecto de la red y mantener trazabilidad incremental.
- 2026-07-17: usar un grafo estático no dirigido por mundo; topología variable y pérdidas correlacionadas quedan como limitaciones explícitas.
- 2026-07-17: conservar los módulos y resultados SP8 históricos, pero separar la nueva campaña canónica bajo `results/processed/sp8/`.

## Progreso

Los seis hitos están cerrados. La campaña confirmatoria contiene 900 mundos pareados, 4500 registros de método y 450 mundos certificados por el oráculo dentro de su dominio. La auditoría automática pasa, las 25 pruebas de continuidad SP5–SP8 pasan y la memoria integral compila en 153 páginas. La revisión visual cubrió SP8, la discusión transversal, el inicio de conclusiones y el anexo de demostraciones; no se observaron desbordamientos, solapamientos ni páginas huérfanas. Permanece como riesgo editorial global que la memoria excede el objetivo VIU de 50–80 páginas de cuerpo y 20 páginas de anexos.
