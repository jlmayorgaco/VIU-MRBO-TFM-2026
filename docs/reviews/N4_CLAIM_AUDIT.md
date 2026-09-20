# Auditoría de afirmaciones SP1.N4 v4

| ID | Afirmación | Familia | Estado | Supuestos | Evidencia y ubicación |
|---|---|---|---|---|---|
| N4-C1 | Las desviaciones F-I se evalúan con los agregados de las cargas afectadas. | F-I | `proved` + tests | perfil estático, capacidades escalares, versiones coherentes | derivación en `n4_v2.tex`; `tests/test_sp1_n4.py` |
| N4-C2 | BR–2BR–C3 forman vecindades anidadas y cada commit estricto termina en un mínimo local del orden examinado. | F-I | `proved` | búsqueda finita y exhaustiva dentro de cada `N_h` | `geo_qpg.py`; tests de barreras y monotonicidad |
| N4-C3 | DMIS compone propuestas no conflictivas y TX conserva atomicidad nominal. | F-I | `proved` + `numerical` | fase y versiones comunes; entrega fiable; proponente vivo | E4; `tests/test_sp1_n4.py` |
| N4-C4 | Las cuatro dinámicas F-II usan el mismo potencial y fitness. | F-II | `proved` por construcción | normalización y pesos congelados | `continuous.py`; derivada verificada por test |
| N4-C5 | El símplex se conserva en la integración implementada. | F-II | `proved` por invariantes numéricos | paso y proyección/mirror update implementados | `test_sp1_n4_continuous.py` |
| N4-C6 | El ranking por endpoint continuo no predice el ranking después de `R`. | F-II | `numerical` | 1.200 mundos E7, presupuesto fijo, cierre común | 74,8 % de discordancia; `FII_POPULATION_REPORT.md` |
| N4-C7 | PD-vGNE distribuido cruzó el criterio conjunto en 91,9 % de E7. | F-III | `numerical` | umbral `5×10⁻⁴`, máximo 4.000 iteraciones, grafo N3 estático | RAW E7; `FIII_VGNE_REPORT.md` |
| N4-C8 | En presión 0,85, PD-vGNE+R fue más factible y tuvo menor gap que Smith+R. | F-III | `numerical` | pares con mismo mundo; gap solo cuando está definido; Holm | +5,50 pp y −7,39 pp; `primary_contrasts.csv` |
| N4-C9 | El algoritmo F-III converge globalmente para cualquier grafo conectado. | F-III | `proposed` / no demostrado | faltan hipótesis completas de discretización y ganancias | se prohíbe formular como resultado en la memoria |
| N4-C10 | El oráculo temporal reduce el coste descontado frente a ambas políticas Geo-QPG. | F-IV | `numerical` | horizonte finito, secuencia conocida, `N=5`, `K=3` | E8; `FIV_STOCHASTIC_REPORT.md` |
| N4-C11 | F-IV es un juego potencial de Markov. | F-IV | `failed` / no establecido | no se verificó la definición ni se estimó `P` | el texto lo clasifica como juego repetido con eventos exógenos |
| N4-C12 | Geo-QPG-C3 domina toda la frontera estática. | transversal | `failed` como afirmación general | los ejes son gap, factibilidad, mensajes y CPU | C3 lidera gap/factibilidad entre distribuidos, pero BR y DMIS+TX usan menos comunicación |
| N4-C13 | La sección valida transporte físico. | transversal | `failed` / fuera de alcance | SP1 termina en coalición lógica | transición explícita a SP2 |
| N4-C14 | El terminal BR alcanzado desde reposo suele requerir coordinación de orden dos para escapar. | F-I | `numerical` | 1.200 mundos E9; coaliciones conectadas; enumeración exacta hasta tres | 1.156/1.200 casos con $h_G^\star=2$; `N4_HSTAR_REPORT.md` |
| N4-C15 | La categoría `>3` identifica un mínimo global. | F-I | `failed` / no identificable | la enumeración termina en orden tres | solo significa que no apareció una mejora conectada con dos o tres robots |

## Regla editorial

Las filas `numerical` deben redactarse en pasado y con campaña, denominador y
alcance. Las filas `proposed` o `failed` no pueden reaparecer como garantías en
resumen, conclusiones o pie de figura. Ninguna cifra de E7/E8 se transfiere a
robots reales ni a la dinámica de transporte.
