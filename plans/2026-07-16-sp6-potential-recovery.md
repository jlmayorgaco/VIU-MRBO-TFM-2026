# SP6-C: juego potencial de recuperación y simulación reproducible

## Propósito y resultado observable

Convertir SP6-C desde una propuesta sin evidencia en una contribución formal y experimental de nivel B. El resultado observable será un juego finito de re-reclutamiento con potencial exacto, caracterización de equilibrios, convergencia finita y cota temporal condicionada; las demostraciones completas quedarán en anexos y una campaña Python pareada producirá datos, tablas y figuras sin usar los resultados históricos no canónicos.

## Contexto y archivos canónicos

- `docs/00_TFM_CHARTER.md` hace SP6-C obligatorio y fija H4.
- `docs/02_RESEARCH_MATRIX.md` exige nivel B para Cargo.
- `docs/03_EXPERIMENT_PROTOCOL.md` exige semillas pareadas, imposibilidad explícita, baselines y fallos preservados.
- `docs/07_SP_SECTION_TEMPLATE.md` fija la microestructura de `sp6.tex`.
- `thesis/sections/mainmatter/06-results-and-analysis/sp5.tex` entrega una carga rígida con separación RAW--SAFE--EXEC.
- La campaña histórica `results/sp6/SP6_MC_robustness_comparison/` proyectaba posiciones después de integrar y no se adopta como evidencia canónica.

## Alcance y no alcance

Incluye un fallo simple durante el transporte Cargo, una carga afectada, reserva de robots heterogéneos, certificado aditivo conservador de soporte/fuerza/torque, decisiones binarias asíncronas y tiempo de llegada del reemplazo. Incluye mundos recuperables, complementarios, con plazo estrecho e irrecuperables.

No incluye fallos simultáneos, contacto conmutado/friccional, SP6-E, partición persistente, diagnóstico probabilístico, control de bajo nivel ni una prueba conjunta del sistema híbrido completo.

## Supuestos y preguntas resueltas

- La detección entrega la identidad del robot fallado tras un retardo acotado.
- La carga afectada publica un vector de déficit local; cada reserva conoce capacidad y coste propios.
- La factibilidad se representa por cobertura multidimensional aditiva normalizada, como aproximación conservadora al certificado SP3-C.
- Las activaciones son asíncronas y justas; no existen rondas globales, aunque la ejecución digital usa eventos discretos.
- La reserva completa es suficiente exactamente en los mundos clasificados como físicamente recuperables.

## Diseño matemático/técnico

Para perfil binario `x`, déficit ponderado `D(x)` y coste de movilización `K(x)`, se define `Phi(x)=-lambda D(x)-K(x)`. La utilidad de cada robot es su contribución marginal respecto a permanecer libre. Se demostrará: potencial exacto; existencia y terminación de mejor respuesta; factibilidad de todo Nash bajo un umbral computable `lambda > kappa_max/delta_min`; minimalidad por inclusión de todo Nash factible; cota de tiempo condicionada; y ausencia de cota universal de eficiencia mediante un contraejemplo.

## Plan experimental

- Escenarios: recuperable balanceado, capacidades complementarias, plazo estrecho e irrecuperable.
- Escala: reservas de 4, 6 y 8 robots; 40 semillas confirmatorias por escenario/escala.
- Métodos: juego potencial guardado, greedy local, subasta marginal, no reparación y oráculo exhaustivo central.
- Métricas: certificado restaurado, éxito antes del plazo, clasificación de imposibilidad, coste/gap, cardinalidad, sobre-reclutamiento, eventos, mensajes, tiempo de recuperación y auditorías de Nash/potencial/cota.
- Hipótesis preespecificadas: restauración frente a no reparación; menor sobre-reclutamiento frente a greedy; coste del mecanismo respecto al oráculo; corrección de la clasificación irrecuperable.

## Hitos

- [x] Formular y probar los resultados del juego.
- [x] Implementar teoría computable, simulador y oráculo.
- [x] Añadir pruebas unitarias y de invariantes.
- [x] Ejecutar humo y campaña confirmatoria pareada.
- [x] Generar tablas, figuras, manifiesto y auditoría.
- [x] Reescribir SP6 y añadir el anexo de demostraciones.
- [x] Actualizar notación, claims y matriz; compilar y revisar el PDF.

## Validación

- `python -m pytest tests/test_sp6_recovery.py -q`
- `$env:PYTHONPATH='src'; python -m viu_mrob_tfm.cli.run_sp6 experiments/configs/sp6_recovery_smoke.yaml`
- `$env:PYTHONPATH='src'; python -m viu_mrob_tfm.cli.run_sp6 experiments/configs/sp6_recovery_confirmatory.yaml`
- Auditoría exhaustiva de perfiles para potencial, Nash, factibilidad y umbral.
- Compilación LaTeX y revisión visual de SP6 y su anexo.

## Riesgos y mitigaciones

- **Sobreafirmar mecánica:** denominar el vector aditivo certificado conservador y no sustituto del reparto de wrench completo.
- **Confundir Nash con óptimo:** demostrar solo optimalidad uniflip y aportar un contraejemplo de precio de anarquía no acotado.
- **Resultado trivial por no reparación:** incluir greedy, subasta y oráculo, además de reportar coste de comunicación y plazo.
- **Árbol de trabajo muy modificado:** editar solo rutas declaradas y no restaurar componentes ajenos.
- **Presupuesto VIU:** mantener resultados principales en SP6 y desplazar álgebra completa al anexo.

## Registro de decisiones

- 2026-07-16: SP6-C es la única rama acreditada; SP6-E queda pendiente.
- 2026-07-16: se excluye como evidencia la campaña histórica que reparaba poses tras integrar.
- 2026-07-16: la garantía se limita a fallo simple, carga afectada única y activación asíncrona justa.

## Progreso

- 2026-07-16: fuentes canónicas, literatura verificada, SP6 actual y artefactos históricos auditados; formulación seleccionada antes de ejecutar la campaña.
- 2026-07-16: implementado el juego potencial exacto, su calibración exhaustiva, tres baselines y el oráculo de coste; 6/6 pruebas focalizadas pasan.
- 2026-07-16: humo de 4 mundos/20 ejecuciones y confirmatorio de 480 mundos/2400 ejecuciones completados con auditoría `passed`.
- 2026-07-16: en los 360 mundos recuperables todos los Nash auditados restauraron el certificado y fueron mínimos por inclusión; los 120 irrecuperables no se reabrieron.
- 2026-07-16: el plazo estrecho limita el éxito del juego a 0,175 y el gap medio de coste frente al oráculo es 0,155; ambos resultados negativos se conservaron.
- 2026-07-16: SP6 quedó en las páginas 95--101 y el anexo de pruebas en 137--139, revisados visualmente sin recortes ni solapamientos.
- 2026-07-16: la memoria completa alcanza 139 páginas y mantiene el riesgo transversal de exceder el presupuesto VIU; el anexo SP6 consume tres páginas del máximo de 20.
