# Limpieza, organización y publicación del repositorio

## Propósito y resultado observable

Dejar el repositorio público coherente con su implementación actual: sin referencias a asistentes de desarrollo, con una guía de uso verificable, dependencias mínimas, comandos funcionales y una estructura fácil de recorrer. El resultado se valida con búsqueda textual, pruebas, compilación del paquete y publicación en la rama principal remota.

## Contexto y archivos canónicos

Rigen `docs/00_TFM_CHARTER.md`--`docs/05_NOTATION.md`, `docs/07_SP_SECTION_TEMPLATE.md`, el código de `src/`, las configuraciones de `experiments/configs/`, las pruebas de `tests/` y la memoria de `thesis/`. El árbol recibido contiene una migración amplia ya iniciada: elimina implementaciones y resultados no canónicos, incorpora una implementación compacta de SP0--SP8 y conserva cuatro commits locales de corrección de la memoria.

## Alcance y no alcance

Incluye documentación de entrada, metadatos del paquete, dependencias, comandos de desarrollo, ubicación de configuraciones, módulos residuales rotos, referencias internas a herramientas y publicación. No reescribe el historial de Git, no cambia resultados científicos, afirmaciones, notación, título administrativo ni referencias bibliográficas legítimas.

## Supuestos y preguntas resueltas

- Los borrados y archivos nuevos ya presentes forman parte de la migración solicitada y se revisan como un conjunto; no se restauran artefactos obsoletos.
- Los nombres oficiales de revistas y congresos se conservan aunque incluyan términos relacionados con inteligencia computacional, porque alterarlos falsearía la bibliografía.
- `experiments/configs/` es la ubicación única de configuraciones versionadas, según el contrato del repositorio.
- La rama `main` y el remoto `origin` son el destino de publicación solicitado.

## Diseño matemático/técnico

No se modifica el modelo matemático. La organización técnica conserva un paquete `src` por subproblema, entradas de consola explícitas, configuraciones YAML separadas de resultados y una suite de pruebas única. Se eliminan módulos residuales que dependen de paquetes ya retirados y no participan en las campañas actuales.

## Plan experimental

No se generan resultados confirmatorios nuevos. Se ejecutan las pruebas unitarias, un experimento de humo de SP5, comprobaciones de importación de todas las entradas públicas y, si el entorno lo permite, compilación de la memoria.

## Hitos

- [x] Inventariar la migración existente y localizar referencias y rutas obsoletas.
- [x] Unificar documentación, dependencias, configuraciones y comandos públicos.
- [x] Eliminar referencias solicitadas y módulos residuales no importables.
- [x] Ejecutar pruebas, humo, compilación y auditoría del diff.
- [x] Crear commit y publicar `main` en `origin`.

## Validación

- `python -m compileall -q src tests`
- `python -m pytest -q`
- `python -m viu_mrob_tfm.cli.run_sp5 experiments/configs/sp5_payload_transport_smoke.yaml`
- `powershell -ExecutionPolicy Bypass -File thesis/build.ps1`
- búsqueda de referencias de herramientas, rutas eliminadas y entradas de consola inexistentes.

## Riesgos y mitigaciones

- La migración comprende más de mil rutas: se revisan resumen, estados y archivos supervivientes antes de confirmar.
- Los resultados ocupan gran volumen: se conservan solo cuando están trazados por la memoria o los documentos de evidencia; no se regeneran campañas costosas.
- La compilación LaTeX puede depender del entorno local: se distingue un fallo de entorno de un fallo documental.
- La publicación puede fallar por autenticación o avance remoto: se verifica el remoto justo antes del push y no se fuerza la historia.

## Registro de decisiones

- 2026-07-17: conservar referencias bibliográficas oficiales y limitar la limpieza a metadatos, documentación y artefactos de desarrollo.
- 2026-07-17: adoptar `experiments/configs/` como raíz única de configuraciones.
- 2026-07-17: sustituir el volcado Conda por dependencias directas y versiones reproducibles del proyecto.

## Progreso

Limpieza y validación técnica completadas. Se reemplazaron la guía, los comandos y las dependencias; se unificaron las configuraciones en `experiments/configs/`; se retiraron módulos residuales y referencias de herramientas; y se movió el generador LaTeX fuera del directorio temporal. Pasan 74 pruebas, se importan 52 módulos, el humo SP5 completa 8/8 ejecuciones y la memoria compila en 134 páginas. Persisten avisos de sustitución tipográfica y caracteres de control ya presentes, sin error de compilación. El conjunto auditado queda preparado para su commit y publicación inmediata en `origin/main`.
