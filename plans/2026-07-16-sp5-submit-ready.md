# SP5: seguridad de la huella rígida y evidencia reproducible

## Propósito y resultado observable

Convertir SP5-C desde una propuesta pendiente en una sección de evidencia experimental de nivel C, reconstruible desde código, configuración y semillas. El resultado observable será: implementación SP5 restaurada y auditada, pruebas focalizadas y humo reproducible, memoria alineada con la campaña confirmatoria congelada y claims limitados al modelo planar reducido.

## Contexto y archivos canónicos

- `docs/00_TFM_CHARTER.md` fija Cargo como modo primario y SP5 como extensión prioritaria.
- `docs/02_RESEARCH_MATRIX.md` asigna nivel C y exige pasillo, obstáculo aislado, cuello de botella y obstáculo dinámico.
- `docs/03_EXPERIMENT_PROTOCOL.md` exige mundos pareados, fallos preservados, ablación y métricas de seguridad.
- `results/sp5/SP5_PAYLOAD_TRANSPORT_CONFIRMATORY_v2/` contiene 108 mundos, ocho métodos y 864 ejecuciones con auditoría semántica PASS.
- `thesis/sections/mainmatter/06-results-and-analysis/sp5.tex` todavía declara ausencia de campaña y debe sincronizarse.
- La implementación SP5 y sus configuraciones aparecen eliminadas en el árbol de trabajo, pero existen en `HEAD`; solo se recuperará el subconjunto necesario para reproducir la campaña, sin tocar eliminaciones ajenas.

## Alcance y no alcance

Incluye SP5-C: carga planar rígida, contactos fijos posteriores al docking, fuerzas planares acotadas, huella compuesta conservadora, obstáculos estáticos y dinámicos, separación RAW--SAFE--EXEC, baselines reactivos, CBF locales y referencia con previsualización.

No incluye SP5-E, fricción/contacto conmutado, dinámica rueda--suelo, percepción ruidosa, hardware, CoppeliaSim, optimalidad cinodinámica ni garantía general de invariancia digital.

## Supuestos y preguntas resueltas

- Se adopta la campaña `SP5_PAYLOAD_TRANSPORT_CONFIRMATORY_v2` como evidencia canónica porque preserva colisiones y timeouts, no repara poses tras integrar y registra la misma instancia para todos los métodos.
- La campaña histórica con proyección geométrica permanece no canónica.
- Cero colisiones observadas no se redactará como prueba de seguridad general.
- La rama empuje/caging se mantendrá explícitamente pendiente.

## Diseño matemático/técnico

El controlador nominal de SP4 produce un wrench deseado. La capa SP5 evalúa barreras sobre una huella compuesta carga--robots, transforma RAW en SAFE y proyecta SAFE al conjunto de wrench realizable antes de aplicar EXEC a la planta. La auditoría comprobará que solo EXEC mueve la planta, que las posiciones no se reparan después de Euler y que los residuos mecánicos y estados permanecen finitos.

La evidencia principal compara el Hamiltoniano amortiguado con y sin CBF, el CBF local con potencial artificial, la previsualización distribuida con el proxy de obstáculos de velocidad y una referencia central con ventaja informativa.

## Plan experimental

- Escenarios canónicos: abierto nominal, corredor estático, cruce móvil, cuello de botella, obstáculo aislado y caso mixto controlado según la configuración congelada.
- Factores: `N in {4,8,12}` y seis semillas confirmatorias, con mundos pareados.
- Métodos: ocho variantes ya congeladas.
- Métricas: éxito seguro, colisión, timeout, distancia mínima, violación de barrera EXEC, error final de pose, residual de wrench, saturación, trabajo, mensajes y CPU.
- Estadística: McNemar exacto para endpoints binarios, Wilcoxon pareado para la tasa de violación y corrección de Holm; intervalos bootstrap por mundo.
- Humo: configuración piloto de dos semillas y subconjunto de escenarios, sin sustituir la campaña confirmatoria.

## Hitos

- [x] Recuperar solo el código, pruebas, script y configuraciones SP5 necesarios.
- [x] Auditar semántica, configuración y consistencia con los artefactos congelados.
- [x] Ejecutar pruebas unitarias focalizadas y campaña piloto de humo.
- [x] Reescribir SP5 con microestructura canónica, resultados e incertidumbre.
- [x] Actualizar notación y matriz de claims con alcance y estado honestos.
- [x] Compilar/revisar la memoria y revisar el diff focalizado.

## Validación

- `python -m pytest tests/test_sp5_payload_transport.py tests/test_sp5_evidence.py -q`
- `python -m viu_mrob_tfm.cli.run_sp5 experiments/configs/sp5_payload_transport_smoke.yaml`
- `python -m viu_mrob_tfm.cli.run_sp5_evidence experiments/configs/sp5_safety_evidence.yaml`
- Auditoría de tablas, manifiesto y `theory_audit.json`.
- Compilación LaTeX mediante el objetivo disponible en `Makefile` y revisión de advertencias/figuras.

## Riesgos y mitigaciones

- **Árbol de trabajo muy modificado:** limitar todas las recuperaciones y ediciones a rutas SP5 declaradas; no restaurar ni limpiar archivos ajenos.
- **Código heredado voluminoso:** ejecutar pruebas y revisar invariantes antes de atribuirle evidencia.
- **Sobreafirmación por cero colisiones:** reportar proporciones, intervalos, timeouts y alcance de simulación; mantener nivel C.
- **Confusión SP4/SP5:** usar el estrato abierto solo como control de transporte y reservar el claim SP5 para escenarios con obstáculos y la ablación de seguridad.
- **Irreproducibilidad ambiental:** registrar Python/dependencias del humo y no afirmar identidad bit a bit si difieren de la campaña congelada.

## Registro de decisiones

- 2026-07-16: se adopta Cargo como única rama ejecutada; SP5-E queda propuesto.
- 2026-07-16: se usa v2 confirmatoria como evidencia canónica y se excluye la campaña histórica con proyección posterior a la integración.
- 2026-07-16: se autoriza recuperar desde `HEAD` únicamente las rutas SP5 necesarias, mediante parches, para respetar el resto de eliminaciones del usuario.

## Progreso

- 2026-07-16: fuentes canónicas y guía de redacción revisadas; detectada contradicción entre `sp5.tex` y los artefactos confirmatorios existentes.
- 2026-07-16: restaurada la implementación canónica `payload_transport_v2`; se excluyó del alcance ejecutable el simulador histórico que reparaba poses tras integrar.
- 2026-07-16: 5 pruebas focalizadas pasan; la campaña de humo produjo 8 ejecuciones pareadas y auditoría `PASS`.
- 2026-07-16: el procesador de evidencia auditó 108 mundos y 864 ejecuciones, generó tablas/figuras reproducibles y clasificó la evidencia como nivel C.
- 2026-07-16: SP5-C quedó redactado y revisado visualmente en las páginas 87--93; SP5-E, red real, contacto friccional y garantía general de invariancia permanecen pendientes.
- 2026-07-16: la memoria completa compila en 132 páginas; el exceso respecto al presupuesto global VIU es un riesgo transversal ajeno al cierre técnico de SP5 y requiere una fase posterior de compactación integral.
