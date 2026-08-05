# SP1.N1 confirmatorio y tres páginas de resultados

## Propósito y resultado observable

Repetir N1 con semillas nuevas y un protocolo congelado que separe calidad,
escalabilidad y frontera de validez. El paquete final debe contener datos RAW,
resúmenes, contrastes, tres figuras vectoriales y tres páginas de resultados
añadidas inmediatamente después de la formulación homogénea de N1.

## Fuentes y restricciones

- `scripts/sp1_a1_hungarian.py` conserva el generador homogéneo y el LSAP.
- `scripts/sp1_a2_milp.py` se usa únicamente para auditar la frontera de
  heterogeneidad; no convierte N1 en un método heterogéneo.
- `docs/03_EXPERIMENT_PROTOCOL.md` fija mundos pareados, fallos visibles,
  intervalos y corrección de Holm.
- La regresión log--log describe el intervalo observado y no demuestra
  complejidad asintótica.
- El fallo de N1 es reasignación central estática, no recuperación física ni
  distribuida.

## Hipótesis congeladas

1. `H-N1.1`: el ahorro mediano del Húngaro frente a greedy supera el umbral
   práctico del 5 % en la batería espacial agregada; los contrastes por
   escenario son secundarios y usan Holm.
2. `H-N1.2`: en el barrido controlado el tiempo del solver no presenta una
   meseta constante (`beta > 0`); la memoria coincide con `8*N*M` bytes.
3. `H-N1.3a`: la recuperación homogénea coincide con la condición cardinal
   posterior al fallo.
4. `H-N1.3b`: aumentar la heterogeneidad de capacidad eleva la tasa de falsos
   factibles de la reducción a slots; el MILP solo audita si existe una
   coalición heterogénea certificada.

## Diseño

- Calidad: cinco geometrías, tres tamaños, tres perfiles de demanda y 100
  semillas por celda; Húngaro y greedy comparten mundo y matriz.
- Escalabilidad: siete tamaños, tres relaciones `M/N` y 30 semillas por celda;
  se separan matriz, solver y tiempo total.
- Fallos: tres tamaños, cuatro márgenes de reserva, cinco fracciones de fallo y
  100 semillas; cada tratamiento comparte el mundo base.
- Heterogeneidad: dos tamaños, cinco geometrías, cinco niveles de capacidad y
  30 semillas; la geometría y la demanda permanecen pareadas entre niveles.

## Artefactos

- `experiments/configs/sp1_n1_confirmatory.yaml`
- `scripts/results/sp1_levels/n1/raw/*.csv`
- `scripts/results/sp1_levels/n1/processed/*.csv`
- `scripts/results/sp1_levels/n1/figures/n1_*.pdf|png`
- `scripts/results/sp1_levels/n1/manifest.json`
- `output/pdf/sp1_levels_26p/SP1_NIVELES_26P.pdf`

## Validación

- Pruebas unitarias de auditoría de capacidad, frontera de fallo, bootstrap y
  estructura del paquete.
- Repetición determinista de un experimento de humo.
- Compilación LuaLaTeX, comprobación de 26 páginas, render Poppler e inspección
  visual de las páginas N1.
- Actualización de `docs/04_CLAIMS_EVIDENCE.md` con resultados y limitaciones.

## Progreso

- [x] Diseño e hipótesis congelados.
- [x] Campaña y análisis implementados.
- [x] Campaña confirmatoria ejecutada: 12.630 registros RAW y 6.630
  mundos--semilla independientes.
- [x] Tres páginas integradas y revisadas en el PDF autónomo de 26 páginas.
- [x] Trazabilidad y pruebas cerradas.

## Resultado y decisión

- `H-N1.1`: el ahorro mediano agregado fue 6,65 % (IC bootstrap 95 %:
  6,29--6,99 %); tres de cinco escenarios superaron el umbral práctico del
  5 %. La ventaja es real en la batería agregada, pero depende de la geometría.
- `H-N1.2`: el exponente log--log descriptivo del solver fue 2,25 (IC 95 %:
  2,22--2,29; $R^2=0,998$) y el P95 alcanzó 487,8 ms para $N=M=2048$.
  Se rechaza una meseta constante en el intervalo medido; no se infiere una
  ley asintótica.
- `H-N1.3a`: las 6.000 reasignaciones coincidieron con la condición cardinal
  del modelo homogéneo. Es recálculo central estático, no recuperación física.
- `H-N1.3b`: la tasa agregada de falso factible pasó de 0 % en capacidad
  homogénea a 42,7 %, 79,0 %, 92,3 % y 96,0 % al aumentar la heterogeneidad.
  Los cuatro contrastes McNemar siguieron significativos tras Holm; el MILP
  HiGHS se conservó como auditor externo de factibilidad.
