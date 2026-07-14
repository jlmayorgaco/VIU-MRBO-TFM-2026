# Thesis Narrative Lock

Fecha de bloqueo: 2026-07-10

## Frase madre

El transporte cooperativo de cargas heterogeneas por AMR se formula como un juego fisico-economico de wrench gobernado por una senal comun de deficit. Sobre esa senal se comparan familias clasicas, centralizadas, de mercado, poblacionales, primal-dual/Nash seeking, aprendidas y de control/safety, delimitando el regimen en el que cada una conserva valor.

## SP canonicos

- SP1: reclutamiento por quorum.
- SP2: capacidad efectiva heterogenea.
- SP3: factibilidad wrench planar y falsos positivos escalares.
- SP4: movimiento y llegada segura.
- SP5: transporte cooperativo con obstaculos, pose y formacion.
- SP6: robustez operativa ante fallos, bateria e inviabilidad.
- SP7: comunicacion, sensado y conectividad temporal.
- SP8: tendencias de calidad en un modelo warehouse mesoscopico; timeouts y memoria no son mediciones confirmatorias.
- SP9/Coppelia: evidencia complementaria no canonica. El replay cinematico existente no es validacion dinamica independiente ni hardware.

## Fuente de verdad

1. `docs/CANONICAL_RESULTS.md` fija rutas y evidencia SP1-SP8.
2. `docs/CLAIM_LEDGER.md` fija redaccion segura.
3. `ROADMAP.md` fija narrativa y orden de cierre.
4. `docs/doc-05-final-report/main.tex` es el entregable academico principal.
5. `TFM.md` queda como borrador/fuente auxiliar, no como entregable final.

## Claims prohibidos

- No presentar un metodo como ganador universal.
- No afirmar hardware real, validacion industrial, despliegue productivo ni contacto 3D completo.
- No reportar SP9 como ejecutado sin `results/sp9/<run_id>/manifest.json`, CSV, figuras y reporte.
- No promover SP4 v4 ni el replay Coppelia como evidencia confirmatoria sin registro canonico, potencia suficiente y dinamica independiente.
- No convertir resultados negativos en positivos por cambio de metrica.
- No mover ni regenerar campanas high-power SP1-SP8 salvo auditoria rota y solo con smoke/compact de equivalencia.

## Estado de limpieza

`src/viu_mrob_tfm/simulation` y `src/viu_mrob_tfm/controllers` permanecen vivos en esta congelacion porque tests y scripts actuales los importan. Cualquier migracion posterior debe hacerse con shims y pruebas verdes.
