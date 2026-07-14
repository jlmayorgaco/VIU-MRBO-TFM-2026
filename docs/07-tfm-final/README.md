# TFM final — paquete de entrega

Este directorio es el punto de entrada único para revisar y entregar el Trabajo Fin de Máster de Jorge Luis Mayorga Taborda. El material se ordena desde el documento que recibe el evaluador hasta la evidencia que permite auditar cada afirmación.

**Estado del paquete:** preparado para entrega en el ámbito local, sin bloqueadores técnicos. Permanecen pendientes los controles externos indicados en [CHECKLIST_ENTREGA.md](CHECKLIST_ENTREGA.md); por tanto, este estado no equivale a aprobación académica ni sustituye el informe institucional de similitud.

## Entrega inmediata

El archivo que debe remitirse como memoria es:

- [TFM_Jorge_Luis_Mayorga_Taborda_2026.pdf](01-entrega/TFM_Jorge_Luis_Mayorga_Taborda_2026.pdf)

Es un PDF A4 de 93 páginas. Su suma SHA-256 es `690fea2213c1374079f79fcdbe77df9e8df9627313c5dde8cacb5cbaddcfb56d`.

## Ruta de lectura

| Orden | Capa | Propósito |
|---:|---|---|
| 1 | [Entrega](01-entrega/README.md) | Memoria final y comprobación de integridad. |
| 2 | [Fuente canónica](02-fuentes/README.md) | Única fuente LaTeX editable y procedimiento de compilación. |
| 3 | [Revisión](03-revision/README.md) | Respuesta a observaciones, resolución y manifiesto de la etapa 4. |
| 4 | [Auditoría](04-auditoria/README.md) | Puerta de entrega, citas y vigencia de la verificación. |
| 5 | [Evidencia](05-evidencia/README.md) | Enlace entre teoría, estimandos, simulaciones y resultados promovidos. |

## Progresión científica de la memoria

La narrativa parte del problema de formar coaliciones multi-AMR y avanza por una cadena causal explícita:

1. se formaliza la demanda física de cada carga y la contribución de cada robot;
2. se plantean juegos de asignación, reparto y aproximación a equilibrio;
3. una decisión continua se transforma en una coalición entera;
4. las guardias de capacidad y *wrench* separan asignación de factibilidad física;
5. las campañas SP0–SP8 estudian cada interfaz de forma modular;
6. A0–FULL integra selección, mecánica, seguridad y recuperación sobre una misma planta;
7. CoppeliaSim queda como replay cinemático complementario, no como evidencia dinámica ni validación física.

Esta secuencia evita mezclar resultados de plantas, unidades experimentales o alcances distintos.

## Veredicto técnico local

| Control | Resultado |
|---|---:|
| Compilación LuaLaTeX + Biber | correcta |
| Referencias o citas indefinidas | 0 |
| Cajas desbordadas / glifos ausentes | 0 / 0 |
| Extensión | 19.103 palabras |
| Cuerpo principal / anexos | 72 / 8 páginas |
| Suite automatizada | 350 pruebas superadas, 0 fallos |
| Auditoría de afirmaciones | 0 hallazgos críticos |
| Auditoría local de citas | 110 entradas, 61 citadas, 123 usos, 0 claves sin resolver |
| Puerta *submit-ready* | `PASS_WITH_WARNINGS`: 0 bloqueadores, 1 advertencia externa |

La única advertencia de la puerta local es la ausencia de un informe institucional de similitud. También quedan reservadas a terceros la verificación bibliográfica independiente y la evaluación académica.

## Política de fuente única

La memoria editable vive únicamente en [`docs/doc-05-final-report`](../doc-05-final-report/). Este paquete contiene el PDF final y copias congeladas de informes de revisión y auditoría; no contiene una segunda fuente LaTeX. Si se modifica la memoria, deben recompilarse el PDF, las auditorías y este paquete antes de entregar.

La relación exacta entre archivos, procedencia y hashes se conserva en [DELIVERY_MANIFEST.json](DELIVERY_MANIFEST.json) y [PACKAGE_HASHES.sha256](PACKAGE_HASHES.sha256).

## Cierre antes del envío

Complete [CHECKLIST_ENTREGA.md](CHECKLIST_ENTREGA.md), adjunte el informe de similitud cuando la institución lo emita y obtenga la conformidad humana correspondiente. Ningún resultado local debe redactarse como «aprobado» antes de esos controles.
