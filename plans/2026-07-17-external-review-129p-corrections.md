# Plan de corrección del dictamen sobre la memoria de 129 páginas

Fecha: 2026-07-17
Estado: completado con riesgos administrativos abiertos

## Objetivo

Contrastar el dictamen externo adjunto con las fuentes actuales, corregir las incidencias verificables y dejar un registro honesto de las observaciones ya resueltas o que requieren una decisión posterior. Se conserva **AMR** como término y título administrativo por instrucción expresa del autor y por precedencia de `docs/00_TFM_CHARTER.md`.

## Alcance y supuestos

- No se incorporarán resultados dinámicos de CoppeliaSim que no existan.
- Las cifras se corregirán desde los datos o generadores, nunca manualmente solo en la narrativa.
- La revisión estilística conservará las delimitaciones científicas aunque varíe su sintaxis.
- El límite VIU de 50--80 páginas de cuerpo y 20 de anexos se medirá tras recompilar. Una reducción estructural que elimine evidencia requiere una decisión separada si no puede resolverse sin alterar el alcance científico.

## Riesgos

1. Los artefactos SP2--SP5 no conservan todos un generador histórico completo.
2. El PDF actual excede previsiblemente el intervalo administrativo de extensión.
3. El repositorio público aún carece de una versión archivada e inmutable con DOI.

## Hitos

- [x] Leer las fuentes de verdad y clasificar el dictamen contra el manuscrito actual.
- [x] Bloque A: aplicar correcciones puntuales y comprobar la existencia de renders de SP2.
- [x] Bloque B: definir `\kappa^{\mathrm{pad}}`, `\mathcal D_0`, `P(N,K)` y justificar `B=1.05` contra código y notación.
- [x] Bloque C: derivar conteos y condicionamientos desde datos/scripts; corregir nomenclatura e intervalos.
- [x] Bloque D: uniformar decimales, operadores, terminología del algoritmo húngaro y primeras apariciones de anglicismos.
- [x] Bloque E: aplicar únicamente los reemplazos literales autorizados.
- [x] Bloque F: insertar síntesis arquitectónica, entorno reproducible, marcador de repositorio, nota de CoppeliaSim y trabajo futuro.
- [x] Bloque G: regenerar la figura de SP3 en PDF vectorial.
- [x] Bloque H: corregir Holm (1979) y auditar su identificador sin inventar metadatos.
- [x] Bloque I: ejecutar pruebas, compilación limpia, búsquedas, recuentos y revisión visual de las páginas afectadas.
- [x] Registrar páginas finales, limitaciones y riesgo administrativo residual. No se crearon commits para evitar mezclar el amplio trabajo preexistente del árbol sucio.

## Decisiones de ejecución

- El árbol de trabajo contiene una migración amplia preexistente. Cada commit se construirá con rutas explícitas y se auditará con `git diff --cached --name-status`; no se incluirán borrados ni cambios ajenos.
- El directorio canónico `thesis/` aún no está seguido por Git. El primer bloque que toque cada archivo lo añadirá completo; los bloques posteriores quedarán como diferencias incrementales sobre ese archivo.
- Las cifras de SP4, SP8 y la misión integrada se resolverán desde tablas, manifiestos y scripts de agregación antes de editar la prosa.
- La URL/DOI y la etiqueta del release se conservarán como marcadores con `% TODO` si no existe un release verificable.

## Verificación prevista

- `python -m pytest -q`
- `powershell -ExecutionPolicy Bypass -File thesis/build.ps1`
- búsqueda de citas/referencias indefinidas y errores de compilación;
- renderizado de páginas afectadas con Poppler e inspección visual;
- recuento final de páginas y comprobación del resumen/abstract.

## Cierre

- Pruebas: 74 superadas.
- PDF verificado: 134 páginas A4, sin errores LaTeX, referencias indefinidas ni cajas `Overfull`.
- Resumen/abstract: 281/278 palabras.
- Extensión: cuerpo aproximado de 98 páginas, fuera del intervalo VIU; anexos de 18 páginas, dentro del máximo.
- Pendientes que requieren una fase distinta: reducción estructural del cuerpo, release inmutable con DOI y validación dinámica/contacto/hardware en CoppeliaSim.
