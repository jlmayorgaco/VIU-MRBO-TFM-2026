# Experimentos

La carpeta `experiments/` agrupa configuraciones reproducibles para simulacion. Cada
experimento debe disponer de un `config.yaml` autocontenido y, cuando no sea trivial, un
`README.md` breve que documente intencion, tratamiento, metricas y alcance.

## Protocolo de configuracion

- La configuracion del experimento vive aqui, no dentro del controlador.
- Los parametros globales o entrenamientos reutilizables viven en `configs/`.
- Los scripts en `scripts/` solo cargan configuracion, ejecutan y guardan resultados.
- Una nueva politica debe poder correr cambiando `controller.type` o parametros YAML,
  sin editar `Simulator`, `SimulationEngine` ni los modelos de dominio.

## Experimentos base

- `exp-001-baseline-nominal`: linea base nominal.
- `exp-002-mass-variation`: sensibilidad a variaciones de masa.
- `exp-003-center-of-mass-shift`: desplazamiento del centro de masas.
- `exp-004-communication-degradation`: degradacion del grafo de comunicacion.
- `exp-005-disturbance-robustness`: perturbaciones externas y robustez.
- `exp-010-scenario-a-smoke`: smoke test de escenario A.
- `exp-011-scenario-b-smoke`: smoke test de escenario B.

## Campanas fuera de esta carpeta

Las campanas H10--H12 se orquestan desde `scripts/campaigns/` y `scripts/coppelia/`
porque generan multiples CSV, figuras y videos bajo `results/campaigns/`. Aun asi, su
configuracion debe mantenerse separada de los metodos de control.
