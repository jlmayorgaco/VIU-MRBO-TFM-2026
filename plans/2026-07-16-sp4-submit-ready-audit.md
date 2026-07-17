# Cierre submit-ready de SP4

## Propósito y resultado observable

Revisar y corregir SP4 con la microestructura canónica del TFM, de modo que el capítulo distinga con precisión reclutamiento/acoplamiento, transporte de pose y extensión empuje/caging. El resultado observable será una sección compilable, con claims trazados, aportes propios identificados, teoría demostrada en anexo, resultados reproducibles y limitaciones explícitas.

## Contexto y archivos canónicos

- `docs/00_TFM_CHARTER.md` a `docs/05_NOTATION.md`.
- `docs/07_SP_SECTION_TEMPLATE.md`.
- `thesis/sections/mainmatter/06-results-and-analysis/sp4.tex`.
- `results/sp4/STATUS.md` y campañas SP4 conservadas.
- `results/sp3/SP3_POSE_suite_euler_lagrange_transport/` como evidencia histórica de transporte de pose que debe reclasificarse con cautela.
- Código, contratos y pruebas históricas de SP4 disponibles en `HEAD`, actualmente eliminados del árbol de trabajo.

## Alcance y no alcance

Incluye auditoría matemática, experimental, bibliográfica, redacción LaTeX, anexo de pruebas, notación, matriz de claims, pruebas y revisión visual. No convierte el replay cinemático de CoppeliaSim en validación física independiente ni atribuye a la rama empuje/caging garantías de Cargo.

## Supuestos y preguntas resueltas

- La campaña canónica declarada es docking v3; v4 y CoppeliaSim se consideran evidencia adicional hasta verificar protocolo y trazabilidad.
- La suite Euler--Lagrange demuestra transporte planar simulado, pero su tamaño pequeño y el cierre auxiliar de slots impiden una afirmación confirmatoria general.
- SP4 puede quedar submit-ready con evidencia parcial honesta si el alcance acreditado se formula con precisión y las extensiones pendientes no se presentan como resultados.

## Diseño matemático/técnico

Se separarán dos lazos: (1) regulación estratégica/local de admisión y conflictos durante el docking; (2) servorregulación física de la pose de la carga mediante wrench acotado. Se auditarán el potencial del juego congelado, sus KKT/VE, la proyección HOCBF y la energía del modelo planar. Cada resultado tendrá supuestos y prueba o se etiquetará como observación empírica.

## Plan experimental

Se usarán las campañas pareadas existentes sin mezclar dominios: docking dinámico para acoplamiento seguro; suite Euler--Lagrange para transporte de pose; replay CoppeliaSim solo para geometría/reproducibilidad visual. Baselines, semillas, métricas, fallos y diferencias informativas se declararán por campaña.

## Hitos

- [x] Inventario y diagnóstico científico completados.
- [x] Formulación, control, teoría y tabla de métodos corregidos.
- [x] Claims, notación y anexo sincronizados.
- [x] Pruebas y artefactos reproducibles verificados.
- [x] PDF compilado y revisado visualmente.

## Validación

- Pruebas unitarias focalizadas de potencial, simplex, HOCBF y control de pose.
- Auditoría de claves bibliográficas contra el `.bib` y el ledger.
- Compilación completa de la memoria.
- Inspección del log y renderizado de las páginas de SP4.

## Riesgos y mitigaciones

- **Generadores eliminados:** no restaurar cambios ajenos sin necesidad; usar historia Git para auditoría y crear solo el mínimo artefacto canónico autorizado por el cierre de SP4.
- **Confusión docking/transporte:** separar explícitamente ambos niveles y no usar llegada a slots como prueba de entrega de carga.
- **Sobreafirmación de CoppeliaSim:** declarar replay cinemático y ausencia de validación física independiente.
- **Poca potencia en transporte:** tratar los 18 casos como evidencia piloto descriptiva.

## Registro de decisiones

- 2026-07-16: se adopta revisión en modo de fidelidad; ningún resultado pendiente se redactará como alcanzado.
- 2026-07-16: Cargo permanece como modalidad primaria y empuje/caging como extensión secundaria no acreditada.

## Progreso

Cierre completado. El manuscrito separa la campaña dinámica de docking del estrato `open_nominal` de transporte rígido, incorpora dos proposiciones con pruebas en anexo y mantiene como pendiente la validación dinámica extremo a extremo. La síntesis de evidencia pasó 13/13 comprobaciones, la regresión pasó 26 pruebas y el PDF final fue compilado e inspeccionado. La auditoría metodológica extensa se conserva en el repositorio, pero se retiró del PDF principal para mantener los anexos en 19 páginas, por debajo del máximo VIU de 20.
