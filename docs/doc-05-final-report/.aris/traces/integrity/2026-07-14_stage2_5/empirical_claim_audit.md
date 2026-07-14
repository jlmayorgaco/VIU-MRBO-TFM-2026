# Auditoría exhaustiva de afirmaciones empíricas, estadísticas y de reproducibilidad

**Artefacto auditado:** `docs/doc-05-final-report/main.tex` y su clausura recursiva de `\input`/`\include`  
**Fecha de corte (UTC):** 2026-07-14T12:50:56.5121656Z  
**Commit base:** `ee6520081aeb3e4ebc6b6cb1f4f8089a2c210ccd` (árbol de trabajo con cambios no confirmados)  
**SHA-256 de `main.tex`:** `fd05b3c5a7fd39af3f2bdb77d815a24e89fa25922134378d89da22a31ba0fa21`  
**Clausura TeX:** 28 archivos; SHA-256 compuesto `e37320f0fb441c44d3e0b4f8f0534cb0d17671d4a12ecabc65e71df981484fd4`  
**Protocolos aplicados:** `integrity_verification_agent.md`, `claim_verification_protocol.md` y `reproducibility_audit.md`.

## 1. Resultado ejecutivo

La evidencia cuantitativa interna del TFM queda **verificada contra los artefactos canónicos locales**. Tras las correcciones aplicadas durante esta ronda, no permanece ninguna discrepancia numérica, estadística o de alcance en A0--FULL, V1--V3 ni SP1--SP8.

| Universo | Denominador | VERIFIED | MISMATCH | UNVERIFIABLE | Cobertura |
|---|---:|---:|---:|---:|---:|
| Afirmaciones internas contrastables con resultados/configuración local | 142 | 142 | 0 | 0 | 100 % |
| Hechos contextuales que dependen de fuentes externas | 4 | 0 en esta auditoría local | 0 | 4 `UNVERIFIABLE_LOCAL` | 100 % clasificadas |
| **Total registrado** | **146** | **142** | **0** | **4** | **100 %** |

**Veredicto empírico local: PASS.** Las cuatro unidades externas no son fallos de los resultados del TFM: se remiten a la auditoría bibliográfica/citacional independiente. Un veredicto integral que incluya literatura debe incorporar esa traza antes de declarar cierre absoluto.

No se modificaron manuscrito, bibliografía, código ni resultados durante esta auditoría. Este archivo es la única salida creada por el auditor.

## 2. Método, denominador y clausura

Una **unidad de afirmación** es la proposición mínima que puede ser verdadera o falsa de forma independiente. Cada fila de una tabla de resultados o hipótesis cuenta como una unidad, aunque contenga efecto, IC, valor p y decisión; se comprobaron todos sus campos. Repeticiones exactas en resumen, abstract, índice de resultados, conclusiones y anexos se deduplicaron en el denominador, pero se rastrearon contra la misma unidad.

La clausura contiene 28 archivos: `main.tex`, 20 secciones, la tabla generada `sections/a0-full-precision-contrasts.tex` y seis figuras TeX. No entran en la compilación actual las secciones modulares extensas `sp1-*.tex`, `sp2-capacity.tex`, `sp3-wrench.tex`, `sp5-transport.tex`, `sp6-resilience.tex`, `sp7-connectivity.tex` ni `sp8-scalability.tex`; se usaron solo como apoyo de trazabilidad. Las afirmaciones SP1--SP8 que sí llegan al PDF están en `modular-evidence-synthesis.tex`, `sp4-motion.tex`, `index.tex`, conclusiones y anexos.

Clasificación usada:

- **VERIFIED:** coincide con manifiesto, CSV, informe, configuración, código o auditoría canónica; el redondeo del manuscrito es compatible.
- **MISMATCH:** el texto contradice el artefacto canónico o presenta una inferencia estadística incorrecta.
- **UNVERIFIABLE:** no existe evidencia suficiente para decidir con los artefactos disponibles.
- **UNVERIFIABLE_LOCAL:** el hecho depende de una fuente externa; queda fuera del universo de resultados locales.

### Huellas de las fuentes canónicas

Los hashes siguientes son compuestos sobre los archivos `.json`, `.csv`, `.md`, `.yaml` y `.sha256` de cada árbol, ordenados por ruta. Permiten detectar cambios posteriores a esta auditoría.

| Evidencia | Archivos | SHA-256 compuesto |
|---|---:|---|
| A0--FULL | 25 | `045bbbe15b7d0ce76dc649564de48d96bde4952bf633cddba5338c135a1e553a` |
| SP1 v1.1 | 9 | `54073ec2efa79ae871efac71289578a7a050074334bbfdfd1b72153a7a3e1f51` |
| SP2 v1.2 | 9 | `c21661dc4c370bca4d643a7a9ec076936438d169ce7ddc46d397c575a8984096` |
| SP3 v1.1 | 6 | `7a514c0d39c5f235d9d740ab4e9d951e9a70e3592032ce65ba464ac46c1e230f` |
| SP4 v3 | 8 | `2d4af14caf2a33aa2b6d4296cb79b8d139e02ce6d920ad642c4c755326f99bda` |
| SP5 v2 | 16 | `0002bba337edd27daf1c59aef4c8e7940dcb075d6b0c8c278ba60620f7647099` |
| SP6 | 14 | `21e265bc5b7af1f639a9be9ccca6ddd140a1d7567a6d5ea7e722497a87747412` |
| SP7 | 13 | `46bff6ea0e217aa0e1dc492fc18b45d9b818d9b3c1c523ccac1366342bc58449` |
| SP8 | 9 | `cab5d4b45efe7097c8157520060d84e6a684fd5804f69602b8c1f46561a8110f` |
| V1--V3 | 12 | `5ce3f387ae9c25cbfce84001042812f0ba147b5c414b704bf9ff292ef9725939` |

## 3. Registro exhaustivo de afirmaciones

### 3.1 A0--FULL — 35/35 VERIFIED

Fuentes principales: `FINAL_RUN_MANIFEST.json`, `FINAL_REPORT.md`, `campaign/base_manifest.json`, `campaign/precision_decisions.csv`, `statistics/summary.csv`, `statistics/paired_contrasts_holm.csv`, `protocol/frozen_manifest.json`, `audit/seed_opening.json`, `protocol/environment.lock.json`, `protocol/HASHES.sha256`, `INTEGRITY_ADDENDUM_2026-07-14.md`, la configuración congelada y `experiments/physical_coalition/simulation.py`.

| ID | Afirmación comprobada | Evidencia canónica | Veredicto |
|---|---|---|---|
| A0-01 | Dry-run de 24 casos antes de confirmatoria | `smoke/manifest.json`, protocolo | VERIFIED |
| A0-02 | Freeze anterior a apertura confirmatoria y posterior a V1--V3 | manifiesto 19:04:06Z; apertura 19:04:21Z enlazada por SHA-256 | VERIFIED; defecto de metadato revelado |
| A0-03 | Base `4×40×6=960` ejecuciones emparejadas | `base_manifest.json` | VERIFIED |
| A0-04 | Checkpoints 40--60--100; extensión solo por anchura máxima `>0,20` | configuración y `precision_decisions.csv` | VERIFIED |
| A0-05 | Nominal termina en 60; las otras tres familias en 100; 20 anchuras finales `≤0,20` | decisiones y contrastes | VERIFIED |
| A0-06 | 2.160 filas únicas, cero errores numéricos, estado `campaign_closed` | `FINAL_RUN_MANIFEST.json` | VERIFIED |
| A0-07 | Tiempo base 71,1 s, cuatro procesos; no hay cronómetro separado de extensión | `base_manifest.json` y ausencia documentada | VERIFIED |
| A0-08 | CPU, sin GPU, sin entrenamiento nuevo | manifiesto y lock de entorno | VERIFIED |
| A0-09 | Python 3.13.9, NumPy 2.3.5, 22 CPU lógicas, cuatro workers, un hilo por worker | `environment.lock.json` | VERIFIED |
| A0-10 | FULL nominal: `n=60`, éxito 0,95, FP 0,05, mensajes 471,00 | `statistics/summary.csv` | VERIFIED |
| A0-11 | FULL escasez: `n=100`, éxito 0,89, FP 0,11, mensajes 501,72 | mismo | VERIFIED |
| A0-12 | FULL torque: `n=100`, éxito 1,00, FP 0,00, mensajes 427,64 | mismo | VERIFIED |
| A0-13 | FULL obstáculo/red: `n=100`, éxito 0,86, FP 0,14, mensajes 661,46 | mismo | VERIFIED |
| A0-14 | FULL 0,86--1,00; FP residual 11 %/5 %; colisión 14 %; mensajes 428--661 frente a 5--8 en A0 | `summary.csv`; A0 exacto 5,47--7,90 | VERIFIED |
| A0-15 | Calibración: `ρ≤0,16`, masa 18 kg, inercia 5,2 kg·m², `dt=0,1`, horizonte 22 s, radio 0,82 m, `k1=k2=2,4`, ocho proyecciones | configuración/código congelado | VERIFIED |

#### Registro completo de 20 contrastes

Cada fila se verificó contra `statistics/paired_contrasts_holm.csv`, incluidos `n`, efecto, IC95 %, anchura, discordancias, p de Holm y decisión. Los veinte IC tienen anchura entre 0 y 0,20.

| ID | Familia; paso | n | Efecto [IC95 %]; anchura; +/−; p Holm | Veredicto |
|---|---|---:|---|---|
| A0-16 | Nominal; A0→A1 | 60 | 0,00 [0,00; 0,00]; 0,00; 0/0; 1 | VERIFIED |
| A0-17 | Nominal; A1→A2 | 60 | 0,00 [0,00; 0,00]; 0,00; 0/0; 1 | VERIFIED |
| A0-18 | Nominal; A2→A3 | 60 | 0,05 [−0,05; 0,15]; 0,20; 6/3; 1 | VERIFIED |
| A0-19 | Nominal; A3→A4 | 60 | 0,00 [0,00; 0,00]; 0,00; 0/0; 1 | VERIFIED |
| A0-20 | Nominal; A4→FULL | 60 | 0,00 [0,00; 0,00]; 0,00; 0/0; 1 | VERIFIED |
| A0-21 | Escasez; A0→A1 | 100 | 0,67 [0,58; 0,76]; 0,18; 67/0; 2,71e−19 | VERIFIED |
| A0-22 | Escasez; A1→A2 | 100 | 0,33 [0,24; 0,42]; 0,18; 33/0; 3,96e−9 | VERIFIED |
| A0-23 | Escasez; A2→A3 | 100 | −0,18 [−0,25; −0,11]; 0,14; 0/18; 1,14e−4 | VERIFIED |
| A0-24 | Escasez; A3→A4 | 100 | 0,07 [0,03; 0,12]; 0,09; 7/0; 0,219; inconcluyente | VERIFIED |
| A0-25 | Escasez; A4→FULL | 100 | 0,00 [0,00; 0,00]; 0,00; 0/0; 1 | VERIFIED |
| A0-26 | Torque; A0→A1 | 100 | 0,00 [0,00; 0,00]; 0,00; 0/0; 1 | VERIFIED |
| A0-27 | Torque; A1→A2 | 100 | 0,00 [0,00; 0,00]; 0,00; 0/0; 1 | VERIFIED |
| A0-28 | Torque; A2→A3 | 100 | 0,60 [0,50; 0,70]; 0,20; 61/1; 4,92e−16 | VERIFIED |
| A0-29 | Torque; A3→A4 | 100 | 0,01 [0,00; 0,03]; 0,03; 1/0; 1 | VERIFIED |
| A0-30 | Torque; A4→FULL | 100 | 0,00 [0,00; 0,00]; 0,00; 0/0; 1 | VERIFIED |
| A0-31 | Obstáculo/red; A0→A1 | 100 | 0,00 [0,00; 0,00]; 0,00; 0/0; 1 | VERIFIED |
| A0-32 | Obstáculo/red; A1→A2 | 100 | 0,00 [0,00; 0,00]; 0,00; 0/0; 1 | VERIFIED |
| A0-33 | Obstáculo/red; A2→A3 | 100 | 0,00 [0,00; 0,00]; 0,00; 0/0; 1 | VERIFIED |
| A0-34 | Obstáculo/red; A3→A4 | 100 | 0,24 [0,16; 0,33]; 0,17; 24/0; 1,91e−6 | VERIFIED |
| A0-35 | Obstáculo/red; A4→FULL | 100 | 0,62 [0,52; 0,71]; 0,19; 62/0; 8,24e−18 | VERIFIED |

### 3.2 V1--V3 — 4/4 VERIFIED

| ID | Afirmación | Fuente | Veredicto |
|---|---|---|---|
| V-01 | V1: 250 casos, 1.239 filas; error L2 máximo `2,8477e−14`; PASS | `v1/manifest.json`, tablas | VERIFIED |
| V-02 | V2 energía: 600 filas; error máximo `1,35817e−8` | `v2/tables/v2_hamiltonian_identity.csv` | VERIFIED |
| V-03 | V2 HOCBF: 350 filas; error de proyección máximo `6,9084e−14`; cero fallos | `v2/tables/v2_hocbf_vs_qp.csv` | VERIFIED |
| V-04 | V3: `λmin=0,277956`, residual de Lyapunov `9,042e−16`, ninguna violación de cota; PASS | `v3/manifest.json`, tablas | VERIFIED |

### 3.3 SP1 — 9/9 VERIFIED

Fuentes: `manifest.json`, `report.md`, `tables/hypothesis_results.csv`, `tables/summary.csv`, `tables/runs.csv`, `theory_audit.json`, configuración y ejecutor.

| ID | Afirmación | Resultado canónico | Veredicto |
|---|---|---|---|
| SP1-01 | 900 mundos, 7.200 ejecuciones, ocho métodos, semillas 330000--330899 | manifiesto | VERIFIED |
| SP1-02 | Smith+QR vs greedy | −0,021159; IC [−0,028352; −0,014087] | VERIFIED |
| SP1-03 | Smith queda detrás de subasta proxy | +0,029889 | VERIFIED |
| SP1-04 | Smith queda detrás de uniforme+QR | +0,015283 | VERIFIED |
| SP1-05 | Smith completo: regret 0,011687 | `runs.csv` | VERIFIED |
| SP1-06 | Smith anillo, cuatro rondas: regret 0,107615 | configuración y `runs.csv` | VERIFIED |
| SP1-07 | Símplex/potencial: error máx. 6,66e−16, cero violaciones, PASS | `theory_audit.json` | VERIFIED |
| SP1-08 | v1 no canónica por sobrepaso de potencial; v1.1 cambia integración/horizonte/semillas, no payoff ni hipótesis | artefactos supersedidos y anexo | VERIFIED |
| SP1-09 | La calidad CLOSED depende sustancialmente del cierre global; no hay superioridad general de Smith | controles uniforme/subasta y resultados | VERIFIED |

### 3.4 SP2 — 12/12 VERIFIED

| ID | Afirmación | Resultado canónico | Veredicto |
|---|---|---|---|
| SP2-01 | 96 celdas × 5 réplicas = 480 mundos; 14 métodos; 6.720 ejecuciones; semillas 360000--360479 | manifiesto/configuración | VERIFIED |
| SP2-02 | Marginal vs plain, Smith | −0,026387 | VERIFIED |
| SP2-03 | Marginal vs plain, replicator | −0,017818 | VERIFIED |
| SP2-04 | Marginal vs plain, ERV--BNN | −0,033784 | VERIFIED |
| SP2-05 | Bajo marginal-log, ERV--BNN vs Smith y vs replicator incluye cero | IC [−0,007507; 0,008526] y [−0,004407; 0,012602] | VERIFIED |
| SP2-06 | ERV--BNN+log vs greedy | −0,050405 | VERIFIED |
| SP2-07 | MILP conserva ventaja sobre ERV--BNN+log | +0,287958 para candidato vs MILP | VERIFIED |
| SP2-08 | Uniforme+closure: regret 0,248871 | resumen | VERIFIED |
| SP2-09 | Uniforme+closure es menor que las nueve variantes de juego | resumen/runs | VERIFIED |
| SP2-10 | RAW sirve 0; el cierre final llega a 0,599444 | resumen | VERIFIED |
| SP2-11 | Auditoría teórica PASS | `theory_audit.json` | VERIFIED |
| SP2-12 | v1: dos fallos Smith/63 pasos auditados; v1.1 midió replay MILP; v1.2 usa semillas nuevas y tiempo de solver | trazas de versiones | VERIFIED |

### 3.5 SP3 — 7/7 VERIFIED

| ID | Afirmación | Resultado canónico | Veredicto |
|---|---|---|---|
| SP3-01 | 600 mundos, 7.200 ejecuciones, seis escenarios, 12 métodos, semillas 461000--461099 | manifiesto/configuración | VERIFIED |
| SP3-02 | PD exacto: brecha máx. frente QP 0,003386 y KKT medio 0,002208 | auditoría/resumen | VERIFIED |
| SP3-03 | FP sin guardia 0,3333; con guardia 0; efecto IC [−0,370; −0,295] | hipótesis | VERIFIED |
| SP3-04 | Escalar, greedy-wrench y CBBA: FP condicional 0,5000 | resumen | VERIFIED |
| SP3-05 | Uniforme+guardia: cobertura 1 y brecha 0,0015 | resumen | VERIFIED |
| SP3-06 | Auditoría teórica PASS | `theory_audit.json` | VERIFIED |
| SP3-07 | v1 no canónica: brecha 0,019722 > gate 0,01; v1.1 usa 1.200 pasos solo en PD exacto y semillas nuevas | versión/anexo | VERIFIED |

### 3.6 SP4 — 24/24 VERIFIED

Fuentes: `manifest.json`, `tables/summary.csv`, `tables/hypothesis_results.csv`, `tables/runs.csv`, `theory_audit.json`, `report.md` y configuración v3.

**Diseño y tabla principal (12 unidades).** SP4 contiene 108 mundos, 1.188 ejecuciones, seis escenarios, tres tamaños, seis semillas y 11 métodos; `dt=0,16`, horizonte 35 s, tolerancias 0,18 m/0,24 rad/0,16 m·s⁻¹ y predicciones 0,45/0,90/1,35/1,80 s. Las once filas coinciden:

| ID | Método | Éxito | Colisión | Timeout | KKT | Tiempo s | Veredicto |
|---|---|---:|---:|---:|---:|---:|---|
| SP4-02 | Directo | 0,1667 | 0,8333 | 0 | — | 0,025 | VERIFIED |
| SP4-03 | APF | 0,1111 | 0,7593 | 0,1296 | — | 0,136 | VERIFIED |
| SP4-04 | RVO proxy | 0,1667 | 0,8333 | 0 | — | 0,028 | VERIFIED |
| SP4-05 | Proyección CBF | 0,1759 | 0 | 0,8241 | — | 1,598 | VERIFIED |
| SP4-06 | PD central | 0,0370 | 0 | 0,9630 | 0,0661 | 2,939 | VERIFIED |
| SP4-07 | Nash--PD RAW | 0,0278 | 0 | 0,9722 | 0,0576 | 1,843 | VERIFIED |
| SP4-08 | Nash--PD exacto | 0,0278 | 0 | 0,9722 | 0,0892 | 1,767 | VERIFIED |
| SP4-09 | Nash--PD anillo | 0,0093 | 0 | 0,9907 | 0,4244 | 2,038 | VERIFIED |
| SP4-10 | Smith+CBF | 0,0093 | 0 | 0,9907 | 0,1286 | 2,164 | VERIFIED |
| SP4-11 | Replicator+CBF | 0,2685 | 0 | 0,7315 | 1,7036 | 2,250 | VERIFIED |
| SP4-12 | ERV--BNN+CBF | 0 | 0 | 1 | 0,1884 | 2,157 | VERIFIED |

`SP4-01` es la unidad de diseño descrita antes de la tabla. Las doce unidades anteriores están VERIFIED.

**Escenarios, hipótesis y auditorías (12 unidades).** 

| ID | Afirmación | Resultado canónico | Veredicto |
|---|---|---|---|
| SP4-13 | Replicator por escenario | abierto 1; cruce 0,2778; bloqueo 0,2222; dispersos 0,1111; estrecho/actuadores 0 | VERIFIED |
| SP4-14 | CBF por escenario | abierto 1; dispersos 0,0556; otros cuatro 0 | VERIFIED |
| SP4-15 | H4.1 éxito Replicator−CBF | +0,0926; IC [0,0370; 0,1574]; p Holm 0,00317 | VERIFIED |
| SP4-16 | H4.2 colisión Replicator−directo | −0,8333; IC [−0,8981; −0,7593]; 4,04e−27 | VERIFIED |
| SP4-17 | H4.3 KKT exacto−anillo | −0,3351; IC [−0,3952; −0,2760]; 1,81e−14 | VERIFIED |
| SP4-18 | H4.4 éxito Replicator−Nash--PD | +0,2407; IC [0,1574; 0,3241]; 2,98e−8 | VERIFIED |
| SP4-19 | H4.5 error posicional Replicator−PD central | −1,0436; IC [−1,1881; −0,9067]; 3,74e−19 | VERIFIED |
| SP4-20 | Auditoría: despeje 0,2724; símplex 2,22e−16; capacidad 0; QP 1,139e−4; gradiente 8,07e−10; 6/6 QP; sin reparaciones | `theory_audit.json` | VERIFIED |
| SP4-21 | Escalado Replicator N=4/8/12 y mensajes; anillo N=12≈4,30e7 | `runs.csv` | VERIFIED |
| SP4-22 | Cero saturaciones en 1.188 ejecuciones; EXEC positivos 48,64 Replicator y 98,81 CBF | `runs.csv` | VERIFIED |
| SP4-23 | RAW y cerrado empatan éxito 0,0278; cierre medio 6,26; no mejora terminal | resumen/runs | VERIFIED |
| SP4-24 | El cierre y la información completa son globales; la carga permanece fija | código/configuración | VERIFIED |

**Comprobación especial SP4:** los tres IC que estaban desalineados al inicio de la ronda quedaron corregidos a los valores canónicos de H4.3, H4.4 y H4.5 indicados arriba. No queda discrepancia.

### 3.7 SP5 — 16/16 VERIFIED

| Grupo de IDs | Unidades | Contenido verificado | Fuente | Veredicto |
|---|---:|---|---|---|
| SP5-01--04 | 4 | seis escenarios; N=4/8/12; seis semillas; ocho métodos; 108 mundos/864 ejecuciones; CPU; freeze y apertura hashados | manifiesto/protocolo | VERIFIED |
| SP5-05--09 | 5 | CBF local 0,5926/0 colisión; VO 0,6574/0,3426; Hamiltoniano RAW 0,1667/0,8333; Ham+CBF 0,4259/0; central 0,1667/0 | `summary.csv` | VERIFIED |
| SP5-10 | 1 | H5.1: −0,8333; IC [−0,8981; −0,7593]; p Holm 4,04e−27 | hipótesis | VERIFIED |
| SP5-11 | 1 | H5.2: +0,2593; IC [0,1759; 0,3426]; 1,12e−8 | hipótesis | VERIFIED |
| SP5-12 | 1 | H5.3: central−local −0,4259; no respaldada | hipótesis | VERIFIED |
| SP5-13 | 1 | H5.4 EXEC +0,0011846; IC [−0,0305; 0,0390]; p Holm 0,003764, dirección no respaldada | hipótesis | VERIFIED |
| SP5-14 | 1 | H5.5 preview−VO colisión −0,3426; respaldada | hipótesis | VERIFIED |
| SP5-15 | 1 | Residual mecánico máx. 1,139e−13; despeje 0,241667; cero reparaciones; RAW/SAFE/EXEC separados | auditoría | VERIFIED |
| SP5-16 | 1 | Histórico 20.040 filas no canónico por proyección posterior a integración | `protocol_deviations.md` | VERIFIED |

### 3.8 SP6 — 5/5 VERIFIED

| ID | Afirmación | Resultado | Veredicto |
|---|---|---|---|
| SP6-01 | 20.000 ejecuciones, 10 métodos, ocho escenarios, 250 semillas 7200--7449 | manifiesto | VERIFIED |
| SP6-02 | Método propuesto: completitud 0,7117, recuperación 0,5155, factibilidad postevento 0,9673 | resumen | VERIFIED |
| SP6-03 | Pérdida de carga vs greedy −0,0227; IC [−0,0300; −0,0155]; p Holm <0,001 | hipótesis | VERIFIED |
| SP6-04 | Completitud vs Smith +0,0044; IC incluye 0; inconcluyente | hipótesis | VERIFIED |
| SP6-05 | 20.000 comprobaciones teóricas, cero fallos | auditoría | VERIFIED |

### 3.9 SP7 — 4/4 VERIFIED

| ID | Afirmación | Evidencia | Veredicto |
|---|---|---|---|
| SP7-01 | 20.176 filas = cinco perfiles nominales × cinco familias × 97 semillas × ocho métodos, más un perfil MC por semilla × ocho métodos | configuración/runs | VERIFIED |
| SP7-02 | Correlación radio--conectividad temporal `ρ=0,8934` | hipótesis/resumen | VERIFIED |
| SP7-03 | H7.3: `n_bloques=0`, no estimable; p heredado 1 no acredita nulidad | hipótesis | VERIFIED |
| SP7-04 | Pérdida/retardo/jitter no cierran una cola de mensajes dentro del controlador histórico; evidencia descriptiva | código/configuración | VERIFIED |

### 3.10 SP8 — 4/4 VERIFIED

| ID | Afirmación | Evidencia | Veredicto |
|---|---|---|---|
| SP8-01 | 20.000 filas programadas: 20 tamaños, 100 semillas, 10 métodos; N=5--50.000 | `runs.csv`/configuración | VERIFIED |
| SP8-02 | Completitud: tensor 0,1561; jerárquico 0,1529; greedy 0,0521 | `summary.csv` | VERIFIED |
| SP8-03 | Timeout declarado y memoria analítica, no wall-clock/RSS bajo watchdog común | código/runs | VERIFIED |
| SP8-04 | H8.1 suspendida como confirmatoria; H8.2--H8.3 son contrastes exploratorios de calidad | `hypothesis_results.csv` y redacción corregida | VERIFIED |

La clasificación ya no confunde H8.2 con memoria: el CSV define H8.1 como timeout, H8.2 como calidad jerárquico--greedy y H8.3 como calidad wrench--Hungarian.

### 3.11 Reproducibilidad, centralización y alcance — 22/22 VERIFIED

**Doce unidades de trazabilidad:** mundos compartidos; regla metodológica de disjunción cuando hay aprendizaje/ajuste; cierre completo hashado de A0--FULL; cronología del defecto de bandera A0; configuración/manifiesto/scripts de SP1--SP2; historia de versiones SP1--SP2; manifiesto/scripts y trazabilidad variable SP3--SP4; historia v1/piloto de SP3--SP4; freeze/hash/script de SP5; manifiesto limitado de SP6; ausencia de manifiesto/hash completo en SP7--SP8; y declaración de disponibilidad que distingue correctamente esos niveles. Todas están VERIFIED.

La frase global no verificable sobre semillas fue corregida a una **exigencia metodológica**: cuando hay aprendizaje o ajuste, el protocolo exige registros disjuntos; el sellado se afirma solo para campañas confirmatorias con freeze. La declaración de disponibilidad también es exacta: A0--FULL y SP5 tienen cierre hashado completo; SP1--SP4 tienen configuración, versión de campaña, manifiesto y tablas con trazabilidad variable; SP6--SP8 no satisfacen el contrato íntegro.

**Nueve unidades del presupuesto de centralización:**

| ID | Etapa | Operación global comprobada | Veredicto |
|---|---|---|---|
| R-13 | A0 | cuantil global 0,55, selección de flota, N mensajes | VERIFIED |
| R-14 | A1 | ranking global, cuórum y slots | VERIFIED |
| R-15 | A2 | ordenación/suma global de ociosos | VERIFIED |
| R-16 | A3 | altas/bajas/pares globales; candidatos O(N²) | VERIFIED |
| R-17 | A4 | unión global A2--A3 | VERIFIED |
| R-18 | FULL | reemplazo entre todos los ociosos | VERIFIED |
| R-19 | SP1--SP3 | QR/closure/guardia consultan preferencias o candidatos globales | VERIFIED |
| R-20 | SP4--SP6 | prioridades, cierres o reemplazos globales según variante | VERIFIED |
| R-21 | SP7--SP8 | red fuera del lazo histórico; evaluador mesoscópico conoce método | VERIFIED |

**R-22, CoppeliaSim:** la memoria no presenta A0--FULL/SP1--SP8 como validación física CoppeliaSim. SP1 se declara exclusivamente Python; SP5 v2 declara explícitamente no usar CoppeliaSim; cualquier uso de CoppeliaSim se limita a inspección cualitativa separada y el trabajo futuro pide motor independiente/hardware. VERIFIED como afirmación de alcance.

### 3.12 Hechos externos — 4/4 UNVERIFIABLE_LOCAL

| ID | Afirmación | Cita del manuscrito | Clasificación local | Acción |
|---|---|---|---|---|
| EXT-01 | 102.900 robots profesionales de transporte/logística vendidos en 2024 | `ifr2025service` | UNVERIFIABLE_LOCAL | auditoría de cita |
| EXT-02 | esa cifra supera la mitad de la categoría | `ifr2025service` | UNVERIFIABLE_LOCAL | auditoría de cita |
| EXT-03 | KUKA KMP 1500P/3000P: 1,5/3 t | `kukaAmr2026` | UNVERIFIABLE_LOCAL | auditoría de cita |
| EXT-04 | OMRON LD/MD/HD hasta 1.500 kg | `omronRobotics2026` | UNVERIFIABLE_LOCAL | auditoría de cita |

## 4. Auditoría especial de freeze A0

Existe una contradicción superficial en los metadatos, pero no en la secuencia autoritativa:

1. `protocol/hypotheses.yaml` conserva `frozen_before_confirmatory_seed_opening: false`.
2. El archivo no se reescribió porque su SHA-256 forma parte del freeze.
3. `protocol/frozen_manifest.json` registra `frozen_ready_for_execution`, semillas cerradas y hora `2026-07-12T19:04:06Z`.
4. `audit/seed_opening.json` registra `after_freeze: true`, enlaza exactamente el SHA-256 del manifiesto congelado y tiene hora `19:04:21Z`.
5. `protocol/HASHES.sha256` verifica los archivos y `INTEGRITY_ADDENDUM_2026-07-14.md` documenta la anomalía sin alterar el original.

Clasificación: **la afirmación “freeze antes de abrir semillas” está VERIFIED**. La bandera es un defecto de metadato inmutable, de severidad baja, revelado en el Anexo B; no hay evidencia de apertura anticipada.

## 5. Correcciones exactas examinadas

| ID | Corrección requerida durante la ronda | Estado al corte |
|---|---|---|
| C-01 | SP4 H4.3 → IC `[−0,3952; −0,2760]`; H4.4 → `[0,1574; 0,3241]`; H4.5 → `[−1,1881; −0,9067]` | APLICADA/VERIFIED |
| C-02 | A0 mensajes: “FULL 428--661 frente a **5--8** en A0”, no 7--8 | APLICADA/VERIFIED |
| C-03 | Tiempo A0: “manifiesto base 71,1 s; no se conservó cronómetro separado de extensión” | APLICADA/VERIFIED |
| C-04 | Freeze A0: revelar bandera `false` heredada y cronología hashada 19:04:06Z→19:04:21Z | APLICADA/VERIFIED |
| C-05 | SP8: suspender recursos por timeout/memoria; tratar **H8.2--H8.3** como calidad exploratoria | APLICADA/VERIFIED |
| C-06 | Disponibilidad: cierre hashado completo solo A0--FULL/SP5; SP1--SP4 con trazabilidad variable; SP6--SP8 sin contrato íntegro | APLICADA/VERIFIED |
| C-07 | Semillas: expresar disjunción como requisito cuando interviene aprendizaje/ajuste y sellado solo donde existe freeze | APLICADA/VERIFIED |
| C-08 | Tabla A0: publicar los 20 contrastes sin selección y declarar anchuras observadas `≤0,20`, sin afirmar que el tope lo garantizaba | APLICADA/VERIFIED |

**Correcciones locales pendientes: ninguna.**

## 6. Límites de reproducibilidad que permanecen correctamente declarados

- SP3 y SP4 conservan manifiesto, informe, tablas y auditoría, pero no un cierre hashado completo comparable al de A0/SP5.
- SP6 tiene manifiesto, pero no versión/hash de protocolo completo.
- SP7 y SP8 carecen de manifiesto/hash canónico completo; sus resultados se usan como descriptivos/exploratorios.
- SP8 no mide coste computacional comparable: timeouts y memoria son salidas declaradas/analíticas.
- SP7 no inyecta una red con colas y estados vecinos obsoletos dentro del lazo.
- CoppeliaSim y las figuras/vídeos no sustituyen tablas ni una validación física.
- Las tasas son del generador planar y no estiman prevalencia industrial.

Estas limitaciones ya aparecen en metodología, resultados, conclusiones y anexos; por tanto, no son `MISMATCH`, sino delimitaciones correctas del alcance.

## 7. Veredicto final

**PASS para integridad empírica local.** Se clasificó el 100 % de las 146 unidades registradas. Las 142 afirmaciones contrastables con artefactos locales están VERIFIED; no hay MISMATCH ni UNVERIFIABLE interno. Las cuatro unidades externas deben cerrarse en la auditoría de citas antes del veredicto integral de publicación.

Si cambia cualquiera de los 28 archivos de la clausura o cualquiera de los árboles canónicos hashados arriba, este informe debe considerarse obsoleto y repetirse sobre el nuevo snapshot.
