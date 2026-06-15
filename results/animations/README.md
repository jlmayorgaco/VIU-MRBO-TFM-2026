# Animaciones de trayectorias

Artefactos generados desde el simulador Python propio. No son validacion en CoppeliaSim.

- Semillas: 2026, 2027, 2028
- FPS: 24
- Duracion objetivo por video: 30 s
- Horizonte maximo de simulacion visual: 180 s
- Logging: 12 Hz, Parquet

## Escenarios

- `abundance`: Abundancia. Semilla canonica 2026 usada por v2.7; no fue elegida por rendimiento.
- `scarcity_priority`: Escasez con prioridad. Semilla canonica 2026 usada por v2.7; no fue elegida por rendimiento.
- `robot_failure`: Fallo de robot. Semilla canonica 2026 usada por v2.7; no fue elegida por rendimiento.
- `comm_degradation`: Degradacion comunicacion R3. Semilla canonica 2026 usada por v2.7; no fue elegida por rendimiento.

## Sanity

Ver `trajectory_sanity.csv`: el hash de metricas con exportacion de trayectoria coincide con el run sin exportacion.
