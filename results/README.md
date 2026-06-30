# Resultados

La carpeta `results/` conserva snapshots compactos que respaldan el reporte V6. No es un
almacen general de artefactos pesados.

- `validation_suite_v1/`: CSV, JSON y tablas LaTeX de la suite H1--H12 y gates G3--G7.
- `smith_qr_validation_r3_20/`: comparacion principal bajo comunicacion R3.
- `marl_*`: entrenamiento o validacion de baselines aprendidos.
- `campaigns/H10_predictive_density/`: peaje de densidad predictiva.
- `campaigns/H11_integrated_engine/`: motor integrado wrench, energia y bateria.
- `campaigns/H12_coppelia_closed_loop/`: escenas y renders fallback de integracion visual.
- `campaigns/H12_coppelia_real/`: ruta reservada para ejecucion fisica/headless real cuando este disponible.

Los artefactos pesados o sustituidos estan fuera del repositorio y se referencian desde
`cleanup_manifest.csv`. Antes de citar nuevos resultados en la memoria, regenerar
`python -m viu_mrob_tfm.validation.suite` y revisar `summary.json`.
