# Plan de ejecución — SP1 DRD-simple frente a CBBA-1-Capacity V1

## Propósito

Implementar y ejecutar una campaña separada, emparejada y auditable para
comparar una relajación poblacional distribuida (`DRD-simple`) con una
adaptación distribuida de subasta de coaliciones con bundle unitario
(`CBBA-1-Capacity`). El estudio se limita a asignación estática de un recurso
escalar de carga; no aporta evidencia sobre movimiento ni transporte físico.

## Pregunta e hipótesis

La pregunta, las hipótesis H1--H6, los criterios de atractivo y dominancia, los
claims permitidos y los claims prohibidos son los predeclarados en
`experiments/configs/sp1_drd_vs_cbba_simple_v1.yaml`. No se cambiarán después de
observar las semillas de evaluación.

## Decisiones congeladas antes de evaluación

- Problema físico: capacidad escalar, coste euclídeo bruto y una asignación por
  robot.
- Potencial común: coste espacial normalizado y penalización cuadrática de
  déficit. Solo DRD incluye entropía como regularizador continuo.
- DRD: actualización exponencial estable, inicialización uniforme y dynamic
  average consensus con pesos Metropolis--Hastings.
- CBBA: adaptación síncrona, no CBBA canónico. Cada robot libre emite una puja
  a una carga; por época se acepta como máximo un candidato por carga. Los
  registros se propagan por aristas y los empates son deterministas.
- Recuperación: el mismo operador de cadenas aumentantes para los cierres
  enteros de ambos generadores, con parámetros fijos.
- Oráculos: LP en todos los tamaños y MILP solo para `N <= 50`, con 60 s.
- Comunicación: payload lógico real, sin cabeceras físicas. Cada envío
  unidireccional a un vecino es un paquete. Los logs agregados por ronda deben
  permitir recomputar paquetes, escalares y bytes sin usar los totales
  declarados por el método.
- Comparación primaria: variantes recuperadas. Comparación del generador:
  variantes raw. Nunca se presenta `DRD recovered` contra `CBBA raw` como
  comparación única.
- Gráficas principales: intervalos y censura visibles; ningún censurado se
  dibuja como solución convergida.

## Riesgos científicos

1. Una penalización cuadrática finita no garantiza cobertura exacta; la
   calibración puede seleccionar un `rho` grande y un `alpha` pequeño. Si el
   gate no se cumple persistentemente, el resultado será censurado.
2. La adaptación CBBA tiene decisiones greedy y no hereda garantías del CBBA
   uno-a-uno.
3. La reparación es heurística y acotada; no garantiza recuperar cualquier
   instancia factible.
4. El LP es únicamente una cota inferior fraccionaria.
5. Alcanzar `N=500` caracteriza las distribuciones y presupuestos evaluados, no
   demuestra escalabilidad general.

## Fases y puertas de calidad

### Fase 1 — Infraestructura y pruebas

- Implementar mundos plantados, grafo, pesos, DRD, CBBA, recuperación, oráculos
  escalares, métricas, trazas, mensajes, checkpoint y auditoría.
- Añadir pruebas unitarias e invariantes del prompt.
- Puerta: todos los tests pertinentes pasan y el repositorio de campaña sigue
  limpio fuera de los cambios intencionados.

### Fase 2 — Calibración

- Usar exclusivamente semillas 80000--80019 y las escalas (20,4), (50,10),
  (100,20).
- Un piloto pre-evaluación adicional con semilla 99999 reveló oscilación para
  `alpha*rho >= 1` en el grafo disperso de N=100. Antes de observar cualquier
  semilla de evaluación se sustituyó la malla inicial por seis perfiles que
  acotan `alpha*rho` entre 0.05 y 0.50. Los checkpoints de la malla descartada
  se eliminaron por completo para impedir mezclar protocolos.
- Evaluar perfiles compartidos de `rho`; ordenar lexicográficamente por
  factibilidad raw, distancia, tiempo, bytes y estabilidad.
- Congelar `selected_parameters.yaml` antes de ejecutar preview/evaluación.

### Fase 3 — Preview

- Ejecutar 15 mundos emparejados y los cuatro outputs físicos.
- Auditar simplex, consensus tracker, asignación unitaria, common random
  numbers, oráculos, recuperación, comunicación, censura y estimaciones de
  coste.
- No reducir la campaña completa en respuesta al preview.

### Fase 4 — Evaluación E1--E6

- E1: 10 casos deterministas.
- E2: 120 mundos de escala conjunta N/K.
- E3: 150 mundos de escala independiente en K.
- E4: 240 mundos de heterogeneidad.
- E5: 240 mundos de topología.
- E6: 160 mundos de utilización.
- Total exacto: 920 mundos, 3 680 filas primarias (cuatro variantes por mundo),
  además de oráculos y ablaciones secundarias separadas.

### Fase 5 — Estadística, figuras e informe

- Wilson y McNemar exacto para factibilidad.
- Bootstrap emparejado, Wilcoxon, rank-biserial y Holm para métricas continuas.
- Kaplan--Meier y RMST para tiempo/bytes censurados.
- Generar F1--F10 en PNG/PDF desde datos procesados.
- Revisar visualmente cada PNG representativo y comprobar integridad de cada
  PDF.

### Fase 6 — Cierre auditable

- Crear todos los artefactos predeclarados, validar sus hashes y el recuento
  exacto.
- Actualizar `docs/02_RESEARCH_MATRIX.md`, `docs/03_EXPERIMENT_PROTOCOL.md` y
  `docs/04_CLAIMS_EVIDENCE.md` solo con evidencia realmente observada.
- Commit final y estado Git limpio.

## Reproducción prevista

```powershell
python -m viu_mrob_tfm.cli.run_sp1_drd_vs_cbba_simple_v1 --stage calibrate
python -m viu_mrob_tfm.cli.run_sp1_drd_vs_cbba_simple_v1 --stage preview
python -m viu_mrob_tfm.cli.run_sp1_drd_vs_cbba_simple_v1 --stage full --resume
python -m pytest tests/test_sp1_drd_cbba_simple.py -q
```

Los comandos finales y los hashes concretos se registrarán en los manifiestos
generados por la propia campaña.
