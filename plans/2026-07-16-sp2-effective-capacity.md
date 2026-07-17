# SP2: capacidad efectiva heterogénea y alineación marginal

## Propósito y resultado observable

Convertir `sp2.tex` de una formulación prospectiva multidimensional en un subcapítulo formal y empírico sobre capacidad efectiva escalar dependiente del par robot--carga. El resultado debe demostrar la diferencia entre cardinalidad, cobertura y completitud; formular dos referencias centralizadas; verificar la alineación potencial del payoff marginal; reproducir tablas y figuras desde los CSV de campaña; y delimitar explícitamente que fuerza, torque, contacto y wrench comienzan en SP3.

## Contexto y archivos canónicos

- `docs/00_TFM_CHARTER.md` fija SP2 en el núcleo obligatorio y reserva la factibilidad física completa para SP3.
- `docs/02_RESEARCH_MATRIX.md` y `docs/03_EXPERIMENT_PROTOCOL.md` describen actualmente SP2 como multidimensional; la campaña ejecutada usa capacidad efectiva escalar. La contradicción se resolverá reduciendo el alcance empírico de SP2 y trasladando fuerza/torque al certificado SP3.
- `docs/04_CLAIMS_EVIDENCE.md` mantiene C2 pendiente.
- `docs/05_NOTATION.md` aún no registra capacidad efectiva, demanda escalar ni los dos gaps.
- `docs/07_SP_SECTION_TEMPLATE.md` obliga a conservar diagrama, optimización, tabla comparada, juego, delimitación de control, protocolo, resultados y conclusión, en ese orden.
- `results/sp2/SP2_MC_capacity_comparison/` y `results/sp2/SP2_MC_marginal_payoff_ablation/` contienen las campañas finales que se auditarán; los números del texto adjunto no se usarán si difieren de estos artefactos.

## Alcance y no alcance

Incluye modelo escalar, dos MILP, prueba de alineación marginal para una matriz efectiva fija, verificador de evidencia, postproceso reproducible, tabla y figura generadas, redacción LaTeX y trazabilidad. No incluye contacto, fuerza/torque, wrench, movimiento de la carga, una prueba de convergencia de Smith muestreado ni la reconstrucción completa del pipeline histórico de trece métodos.

## Supuestos y preguntas resueltas

- La batería se representa como fracción en `[0,1]`; la reserva usa la misma escala.
- La distancia descuenta capacidad entregable dentro del horizonte operacional, no capacidad mecánica nominal.
- La campaña ejecutada no usa una matriz de compatibilidad: `h_ik=1` se considera fijo en las instancias reportadas y no se incorporará retroactivamente a la fórmula empírica.
- La matriz `E=[e_ik]` permanece fija durante cada instante de decisión analizado.
- `x_ik` es binaria en los oráculos; `rho_ik` es la preferencia continua del juego.
- Los dos oráculos optimizan estimandos distintos: score operativo y techo de cobertura; ninguno representa la arquitectura distribuida.
- Las campañas heredadas se tratarán como evidencia empírica del dominio registrado, con la limitación de que su generador histórico fue eliminado del árbol de trabajo. El nuevo postproceso sí será reproducible desde una configuración versionada.

## Diseño matemático/técnico

Se definirá `e_ik=c_i psi_i^b psi_ik^d`, `S_k=sum_i e_ik x_ik` y completitud `S_k>=D_k`. El oráculo de cobertura maximiza `sum_k min(S_k,D_k)`; el oráculo de score maximiza exactamente `5 sum_k V_k z_k + 100 sum_k s_k/D_k - 0.0005 sum delta_ik x_ik - 0.00001 sum E_ik^travel x_ik`, sujeto a exclusividad, cardinalidad, cobertura y cotas de `s_k`.

Para la relajación continua se compararán `f_ik^plain=V_k sigma(D_k-S_k)-g_ik` y `f_ik^marg=e_ik V_k sigma(D_k-S_k)-g_ik`. La proposición se limitará a la integrabilidad: el campo marginal es el gradiente de `Phi=sum_k V_k int_0^{S_k} sigma(D_k-s)ds-sum_ik g_ik rho_ik`; el plano falla en general por derivadas cruzadas desiguales. No se inferirá optimalidad, cierre entero ni convergencia del integrador.

## Plan experimental

El postproceso validará las 40 semillas `3100--3139`, cinco generadores, filas pareadas, ausencia de fallos en las auditorías y consistencia entre ranking e hipótesis. Generará una tabla principal, una tabla de ablación y una figura de tres paneles desde los CSV procesados. Las hipótesis preespecificadas serán: menor gap de score, mayor completitud, menor capacidad incompleta y mayor alineación para Smith marginal; y mayor éxito de primal--dual frente a greedy como contraste negativo.

## Hitos

- [x] Hito 1 — Modelo formal, oráculos, auditoría de gradiente y pruebas unitarias pasan.
- [x] Hito 2 — Configuración y postproceso regeneran tablas/figura y validan ambas campañas.
- [x] Hito 3 — SP2 integra teoría, evidencia y resultado negativo sin sobreafirmar.
- [x] Hito 4 — Matriz de investigación, protocolo, notación y claims quedan sincronizados.
- [x] Hito 5 — La tesis compila y las páginas de SP2 pasan revisión visual.

## Validación

- `python -m pytest -q tests/test_sp2_effective_capacity.py`
- `python -m viu_mrob_tfm.cli.run_sp2_evidence --config experiments/configs/sp2_effective_capacity.yaml`
- `thesis/build.ps1`
- búsqueda de referencias/citas indefinidas, marcadores prospectivos y cifras manuales;
- inspección del diff y del PDF renderizado.

## Riesgos y mitigaciones

- **Confundir cobertura con completitud:** se reportan dos oráculos y dos gaps.
- **Sobreafirmar compatibilidad:** se declara fija y ausente del cálculo ejecutado.
- **Presentar el potencial como convergencia:** la proposición solo prueba integrabilidad para `E` fija.
- **Inventar reproducibilidad completa:** se distingue postproceso reproducible de generador histórico no presente.
- **Codificar resultados en LaTeX:** las tablas cuantitativas se generan desde CSV.
- **Alterar cambios del usuario:** no se restauran los módulos históricos eliminados ni se modifica el resto del árbol sucio.

## Registro de decisiones

- 2026-07-16 — Se adopta capacidad efectiva escalar porque coincide con los artefactos ejecutados; fuerza/torque y contacto se reservan para SP3.
- 2026-07-16 — Se corrige el adjunto: la campaña no multiplicó por `h_ik`; se fija compatibilidad universal para los resultados reportados.
- 2026-07-16 — Se separan 20.280 filas/auditorías del comparativo, 9.360 de la ablación y los catálogos de vídeo de cada campaña.
- 2026-07-16 — La garantía formal se formula como proposición de alineación/integrabilidad, no como convergencia del algoritmo digital.
- 2026-07-16 — Se conservan ocho páginas de SP2 en el PDF final para mantener legibles la prueba, las tablas y la figura bajo el formato VIU; no se fuerza la meta orientativa de seis páginas.

## Progreso

Trabajo completado. El núcleo formal y el postproceso reproducible están implementados; las dos campañas heredadas superan la auditoría de integridad; las tablas y la figura se generan desde los CSV; la trazabilidad documental está sincronizada; cinco pruebas unitarias pasan; y el PDF completo de 103 páginas compila y ha sido revisado visualmente en las ocho páginas de SP2. Permanece como limitación explícita que el generador histórico de las campañas no está presente en el árbol de trabajo y que los métodos etiquetados como Smith no ejecutaron una ODE de Smith.
