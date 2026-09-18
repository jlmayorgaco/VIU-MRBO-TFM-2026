# Snapshot de código del preflight Cargo minimal-v5

Este directorio conserva, byte a byte, los nueve módulos Python cuyos hashes
figuran en `results/coppelia_cargo_preflight_minimal_v5/manifest.json`. La copia
se tomó antes de añadir la atestación obligatoria de preflight y de reforzar la
elegibilidad confirmatoria.

Su único propósito es verificar el artefacto histórico sin exigir que la fuente
viva de `src/viu_mrob_tfm/coppelia_cargo/` permanezca congelada. Los módulos de
este directorio no son una implementación activa, no deben importarse y no
autorizan una campaña confirmatoria. `manifest.json` enlaza la copia con los
hashes del manifiesto, gates, configuración y corridas originales.

El artefacto histórico permanece inalterado. Sus gates de transmisión de
fuerza, rueda--twist, desempeño terminal y sensibilidad multirrate continúan
cerrados; por ello esta instantánea tampoco eleva su nivel de evidencia.
