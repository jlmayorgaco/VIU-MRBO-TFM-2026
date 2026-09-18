# Validación de pruebas

Fecha: 2026-09-09.

## Pruebas focales del entregable

Comando:

```powershell
python -m pytest -q tests/test_pre_thesis_page_budget.py tests/test_pre_thesis_snapshot_provenance.py tests/test_pre_thesis_release_manifest.py tests/test_literature_coverage.py tests/test_pre_thesis_bibliography.py tests/test_pre_thesis_formal_semantic_audit.py tests/test_pre_thesis_idea_ledger.py tests/test_pre_thesis_source_consultation_audits.py tests/test_protected_tikz_figures.py
python -m pytest -q tests/test_coppelia_cargo_controller.py tests/test_coppelia_cargo_design.py tests/test_coppelia_cargo_preflight_authorization.py tests/test_coppelia_cargo_preflight_evidence.py tests/test_coppelia_cargo_runtime.py tests/test_coppelia_cargo_scene_builder.py tests/test_cargo_e2e.py
```

La pasada final del bloque documental —presupuesto, procedencia, sello portátil, bibliografía, auditoría formal, adjudicación claim--archivo, inventarios, cobertura de unidades LaTeX etiquetadas, identidad de libros y TikZ— cerró con **57 passed in 3.44 s**. La batería Cargo completa cerró con **62 passed in 37.46 s**.

El ledger ampliado conserva 13.019 filas y 24 columnas. El cruce por contención exacta identifica contexto formal en 21 de las 477 unidades LaTeX etiquetadas —2 `PASS`, 15 `LIMITED`, 2 `FAIL` y 2 `DUPLICATE`— sin poblar su claim propio. Las otras 456 etiquetas poseen una decisión semántica hash-bound y no queda ninguna pendiente. Los veinte bindings del corpus histórico `thesis` reúnen 140 etiquetas: 137 decisiones y tres contextos formales; 72 se destinan al cuerpo, 48 a la monografía y 20 quedan `archive-only`. Dos bindings de `paper/` añaden quince decisiones del ensayo exploratorio `megajuego`: nueve resúmenes empíricos limitados, cinco figuras contextuales y una síntesis excluida. Veinticinco bindings técnicos añaden 304 decisiones: 44 definiciones, 121 límites, 128 contextos, un protocolo y diez resúmenes históricos de evidencia; 214 sobreviven como candidatos monográficos y 90 quedan excluidas. Globalmente, las 456 decisiones se reparten en 116 definiciones, 123 límites, 169 contextos, doce protocolos y 36 resúmenes de evidencia. La importación independiente del CSV confirmó el rango `A1:X13020`, inspeccionó las 47 fuentes y produjo una tabla visual de 48 filas con `pending=0`, sin fórmulas ni recortes críticos en claim, relación, función probatoria o destino.

Tras integrar los gates documentales de procedencia, inventario, adjudicación claim--archivo, auditoría formal, ledger de ideas e identidad bibliográfica, ambas interfaces completas volvieron a pasar: `build.ps1 -Target thesis -Verify` produjo 97 páginas y `build.ps1 -Target monograph -Verify`, 110. La variante `-AuditSources` pasó en el repositorio completo. Una copia con solo los 291 archivos declarados en `release-manifest.json` y el propio manifiesto, sin las nueve raíces externas, produjo exactamente los mismos SHA-256 que el checkout original. Los valores quedan congelados en `build-reproducibility.md`.

Estas pruebas cubren el controlador, la escena, los gates y el contrato de ejecución de Cargo; los inventarios y auditorías documental, formal y bibliográfica; la preservación de las cinco figuras TikZ; la procedencia de la instantánea y las dos interpretaciones conservadoras del presupuesto VIU.

La auditoría contextual independiente ejecutó además 38 pruebas focales y cerró con 38 aprobadas.

## Endurecimiento del gate Cargo confirmatorio

Se añadió la prueba focal `tests/test_coppelia_cargo_preflight_authorization.py`
y se volvió a verificar el bloque Cargo sin iniciar CoppeliaSim ni ejecutar una
campaña confirmatoria:

```powershell
python -m pytest -q tests/test_coppelia_cargo_controller.py tests/test_coppelia_cargo_design.py tests/test_coppelia_cargo_preflight_authorization.py tests/test_coppelia_cargo_preflight_evidence.py tests/test_coppelia_cargo_runtime.py tests/test_coppelia_cargo_scene_builder.py tests/test_cargo_e2e.py
```

Resultado final del bloque ampliado: **62 passed in 27.71 s**. La batería incluye aceptación de una
atestación unitaria hash-bound, rechazo de autorización ausente, evidencia
ausente, evidencia histórica incompatible, manipulación de `gate_status.json`,
gate físico fallido y divergencias de backend, controlador, escena o código.
También comprueba que ningún rechazo cree el directorio de salida y que la
elegibilidad exige `physical_success`, contacto, deslizamiento, colisión y
estado terminal en todas las corridas; además, cierra la inyección de backends
y exige autorización API literalmente booleana, las tres guardas pareadas, la
matriz/registro de semillas reconstruidos y ACK MuJoCo/ruedas válidos.
El preflight vuelve a calcular cada hash de contrato SI y los hashes internos
de la auditoría de escena antes de permitir que exista una salida física.

## Suite completa del repositorio

Comando:

```powershell
python -m pytest -q
```

Resultado final observado sobre el árbol preservado: **403 passed, 10 failed in 305.94 s**.

Los diez fallos se concentran en contratos históricos SP1 ajenos a `pre-thesis`: falta `plans/2026-07-24-sp1-geo-qpg-signal-engine-closure-v1.md`; faltan `thesis/sp1_levels_23p/main.tex`, `output/pdf/sp1_levels/manifest.json` y `output/pdf/sp1_levels/SP1_levels_N1_N2_N3_N4.pdf`; y dos manifiestos históricos ya no coinciden con los hashes actuales de `scripts/sp1_levels_common.py` y `src/viu_mrob_tfm/sp1_n4/geo_qpg.py`. El estado de trabajo recibido conserva eliminaciones y modificaciones del autor. El plan aprobado prohíbe restaurarlas o sobrescribirlas, por lo que no se fabricaron sustitutos, no se reescribieron manifiestos históricos y no se relajaron pruebas.

## Veredicto

Las pruebas pertinentes al nuevo entregable están verdes. La suite global no está completamente verde por dependencias históricas ausentes y preservadas deliberadamente; esta limitación no debe presentarse como una regresión de `pre-thesis` ni ocultarse en el cierre.
