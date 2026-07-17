# SP1: reclutamiento por cuórum y cierre entero

## Propósito y resultado observable

Convertir `sp1.tex` de protocolo prospectivo en un subcapítulo formal y reproducible sobre coaliciones homogéneas de cardinalidad variable. El resultado debe distinguir abundancia, régimen crítico y escasez; demostrar la frontera entre cuotas obligatorias y selección todo-o-nada; caracterizar el juego de déficit/exceso; justificar un incentivo de cuórum; y separar preferencia continua, cierre entero y coalición lógica.

## Contexto y archivos canónicos

- `docs/00_TFM_CHARTER.md` fija SP1 como parte del núcleo obligatorio y reserva la factibilidad física para SP3.
- `docs/02_RESEARCH_MATRIX.md` asigna a SP1 evidencia A o B, con MILP y un referente distribuido.
- `docs/03_EXPERIMENT_PROTOCOL.md` exige demandas por debajo, iguales y superiores a la flota y cardinalidades 1--4.
- `docs/04_CLAIMS_EVIDENCE.md` mantiene C1-SP1 pendiente.
- `docs/05_NOTATION.md` separa cardinalidad `n_k`, preferencia `rho_ik` y decisión binaria `x_ik`.
- `docs/07_SP_SECTION_TEMPLATE.md` obliga a conservar diagrama, optimización, tabla comparada, juego, delimitación de control, protocolo, resultados y conclusión, en ese orden.
- `results/sp1/SP1_READINESS_REPORT.md` es posterior a las campañas heredadas y bloquea su uso como evidencia confirmatoria.

## Alcance y no alcance

Incluye formulación finita, pruebas delimitadas, contraejemplo de escasez, operador de cierre, implementación verificable, enumeración exacta de casos pequeños, campaña de desarrollo pareada, artefactos procesados y redacción LaTeX. No incluye movimiento, contacto, capacidad multidimensional, wrench, red imperfecta ni apertura de semillas confirmatorias.

## Supuestos y preguntas resueltas

- Los robots son homogéneos para factibilidad; su identidad solo cambia el coste espacial normalizado.
- Una carga está cerrada si recibe exactamente `n_k` robots; una coalición parcial no cuenta como servicio.
- La presión se define como demanda sobre flota, `rho_D=(sum_k n_k)/N`; se evita reutilizar `rho_ik`.
- La campaña heredada `SP1_HOMOGENEOUS_v1_1` se trata como desarrollo observado, aunque su manifest histórico diga `confirmatory`.
- La petición de retirar la tabla de literatura contradice la plantilla canónica; se conserva una tabla compacta que diferencia fuentes verificadas, métodos ejecutados y referencias contextuales.

## Diseño matemático/técnico

El juego base usa `J_Q=C+lambda_D D_n+lambda_O O_n` y utilidad marginal. Se probará que, si todas las cuotas son realizables y `lambda_D=lambda_O>kappa_max`, los Nash puros coinciden con las asignaciones exactas. En escasez se probará que el déficit lineal es constante cuando todos los robots están activos y no hay exceso. El incentivo de cuórum será la función exponencial normalizada y saturada

`B_beta,k(q)=(exp(beta min(q,n_k)/n_k)-1)/(exp(beta)-1)`,

con extensión lineal para `beta=0`; sus incrementos discretos son crecientes antes del cuórum. El cierre QR recibe una matriz de preferencias y produce asignaciones exclusivas con ocupaciones en `{0,n_k}` mediante selección iterativa de grupos completos.

## Plan experimental

Se ejecutará primero una auditoría enumerativa para `N<=5`. La campaña de desarrollo usará semillas pareadas, cardinalidades 1--4, presión de demanda por debajo, igual y por encima de uno, geometrías uniforme/agrupada y los tratamientos que estén implementados de forma verificable. Se reportarán cierre exacto, valor completado, déficit, exceso, robots en grupos parciales, calidad frente al MILP, eventos y CPU. Los resultados no se denominarán confirmatorios hasta satisfacer el informe de readiness.

## Hitos

- [x] Hito 1 — Formulación, pruebas unitarias y auditoría exacta pasan.
- [x] Hito 2 — Configuración y campaña de humo generan datos, tablas, figuras y manifest.
- [x] Hito 3 — SP1 integra teoría y evidencia sin sobreafirmar y sincroniza trazabilidad.
- [x] Hito 4 — SP1 compila de forma aislada en seis páginas y supera la revisión visual. La compilación integral queda bloqueada por una edición concurrente en SP2, ajena a este plan.

## Validación

- `python -m pytest -q tests/test_sp1_theory.py`
- `python -m viu_mrob_tfm.cli.run_sp1_theory --config experiments/configs/sp1_theory.yaml --smoke`
- `python -m viu_mrob_tfm.cli.run_sp1_theory --config experiments/configs/sp1_theory.yaml`
- compilación LaTeX con el flujo existente del repositorio;
- búsqueda de referencias/citas indefinidas, marcadores prospectivos y valores manuales;
- inspección del diff y del PDF renderizado.

## Riesgos y mitigaciones

- **Sobreafirmar campañas heredadas:** se subordinan al readiness posterior y se etiquetan como desarrollo.
- **Confundir cierre con convergencia:** RAW y CLOSED se almacenan y evalúan por separado.
- **Atribuir NP-dificultad a toda cardinalidad variable:** se separa el caso obligatorio polinómico de la selección opcional tipo mochila.
- **Prometer que el cuórum resuelve toda escasez:** se demuestra solo la ruptura del contraejemplo mínimo y el resto se evalúa empíricamente.
- **Alterar cambios del usuario:** no se restauran los módulos SP1 históricos eliminados; la implementación nueva es mínima y autónoma.

## Registro de decisiones

- 2026-07-16 — Se aplica la plantilla canónica sobre la estructura alternativa del diagnóstico adjunto.
- 2026-07-16 — Se adopta `rho_D` para presión de demanda y se reserva `rho_ik` para preferencias.
- 2026-07-16 — La evidencia histórica se reclasifica como desarrollo por la decisión BLOCKED del readiness report.
- 2026-07-16 — Se usa incentivo exponencial normalizado, no una sigmoide genérica inexistente en el código.

## Progreso

Trabajo completado el 2026-07-16: se implementó el núcleo formal autónomo, pasaron 17 pruebas del repositorio, se ejecutaron 1440 mundos pareados y 14/14 controles teóricos, y se generaron tablas, figuras y manifest de desarrollo. El subcapítulo y su anexo sincronizan notación y trazabilidad; la inspección rasterizada confirma seis páginas sin desbordes ni referencias internas indefinidas. La compilación integral alcanzó SP2 y falló en una macro estadística concurrente (`\SPTwoGapPHolm`), por lo que se conservó un PDF aislado de revisión sin modificar SP2.
