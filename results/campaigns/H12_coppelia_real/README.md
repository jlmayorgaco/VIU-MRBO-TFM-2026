# H12 CoppeliaSim real physics campaign

This folder is for the real CoppeliaSim validation route. It is intentionally
separate from `H12_coppelia_closed_loop`, whose videos are synthetic fallback
renders.

Regenerate from the repository root:

```powershell
python scripts\coppelia\run_h12_coppelia_real.py
```

Expected outputs after a successful real run:

- `summary.json` with status `coppelia_real_pass` or an explicit failure state.
- `manifest.csv` pointing to every generated artifact.
- `data/h12_real_rectangular_transport_physics.csv` with measured CoppeliaSim object states.
- `data/h12_real_metrics.csv` with physical validation gates.
- `coppeliasim/real_scenes/h12_real_rectangular_transport_physics.ttt`.
- MP4/PNG artifacts under `animations/`, `plots/`, and, when the headless renderer provides images, `frames/`.

Acceptance gate:

- The rectangular load must move at least 4 m in the real simulator.
- Rack collision count must be zero.
- The load must remain inside the corridor and yaw must remain bounded.
- The campaign must not fall back to synthetic rendering.
