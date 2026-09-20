# SP2 — registro de revisión mayor, ronda 1

Fecha: 2026-08-20  
Entregable: `output/pdf/SP2_HONORS_VIU.pdf`

## Dictamen de cierre

El subdocumento queda apto para una revisión exigente de TFM dentro de la
evidencia disponible. No se declara validación industrial ni se ocultan
resultados adversos. Cargo es el modo primario; caging se conserva como
extensión con dinámica de contacto y certificado propios.

## Cambios verificables

| Objeción | Remediación | Evidencia de cierre |
|---|---|---|
| Propósito y alcance difusos | Pregunta local, contrato de entrada/salida y conclusión que responde explícitamente | `Subdocuments/SP2/sp2.tex` |
| Inferencia con escenarios tratados como independientes | Bootstrap de 5.000 remuestras sobre 30 bloques de semilla completos; siete escenarios permanecen dentro de cada bloque | `results/sp2_canonical/SP2_HONORS_v3/protocol/analysis_contract.json`; `processed/paired_endpoint_statistics.csv` |
| Hipótesis de seguridad mal cerrada | H6 refutada: diferencia gobernado--crudo en colisión +0,0524, IC95 % [0,0393; 0,0643] | `Subdocuments/SP2/n4_controller_benchmark.tex` |
| Comparación PID/LQR/LQI/MPC sobregeneralizada | Ganancias declaradas como fijadas por ingeniería; comparación entre familias descriptiva; inferencia dentro de controlador | contrato de análisis y Tabla 2 |
| Ausencia de integración de misión | Campaña Cargo de 360 mundos/2.160 ejecuciones incorporada con 359/360 entregas y 89/90 sustituciones | `results/processed/integrated/CARGO_E2E_CONFIRMATORY_v1/` |
| Etiqueta “distribuido” excesiva | Renombrado como demostrador híbrido: solo el gossip de identificadores es vecinal; líder, atributos, selección, planta y reparto usan registro/estado global | sección “Demostrador híbrido” y matriz de evidencia |
| Docking y final de misión sobredimensionados | Docking delimitado como llegada posicional; liberación/desacoplamiento marcado como no ejecutado | Figura 10 y texto Cargo |
| SLAM y Pioneer confundidos con resultado | RBPF, grafo SE(2), marcos, sensores y fuerza se presentan como protocolo instrumentable pendiente, no validación | Figura 5 y sección N3 |
| Figuras comprimidas o ambiguas | Figura 1 en cuatro paneles antes/después; arquitectura de control redistribuida; cadena Cargo sin solapamientos; caging compacto y legible | inspección visual de las 20 páginas renderizadas |
| Presupuesto editorial | Caging condensado sin mezclar garantías con Cargo; doce figuras vectoriales; documento en 20 páginas | compilación y `pdfinfo` |

## Resultados negativos preservados

- La estructura virtual no domina en todos los canales N3.
- H6 queda refutada en el agregado de N4 aunque MPC muestre el signo opuesto en
  el diagnóstico por controlador.
- E2E-H1 no acredita ventaja temporal y E2E-H4 no acredita equivalencia con
  información perfecta.
- E2E-H2 solo identifica el bloque conjunto criterio agregado--rodeo--filtro;
  no separa sus componentes.

## Verificación final

- `python -m pytest tests/test_sp2_canonical.py tests/test_sp2_submit_ready.py tests/test_cargo_e2e.py -q`: **34 passed**.
- `Subdocuments/SP2/build.ps1`: **PASS**, 20 páginas, sin cajas desbordadas ni
  citas/referencias sin resolver.
- Revisión visual completa mediante render Poppler; reinspección específica de
  páginas 14, 15, 18 y 20 tras las últimas correcciones.
- Las tablas, macros y figuras cuantitativas se sincronizan desde resultados
  procesados; no se codificaron resultados manualmente en el PDF.

## Limitaciones que permanecen

No existen ensayos físicos del Pioneer 3-DX, ejecución de SLAM/grafo relativo,
calibración de fuerzas, contacto deformable, dinámica rueda--suelo, sensibilidad
en el paso temporal, docking físico ni liberación. Además, los hashes N4
añadidos son post hoc: como las fuentes/configuraciones SP2 aparecían sin
seguimiento al auditar el árbol, el commit histórico del manifiesto no identifica
de forma suficiente el código que produjo los datos crudos. Cerrar esa deuda
requiere congelar un snapshot versionado y repetir la campaña.
