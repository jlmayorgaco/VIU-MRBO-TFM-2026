# CoppeliaSim real scenes

This directory is reserved for scenes saved by the real CoppeliaSim H12 runner.

The real runner is:

```powershell
python scripts\coppelia\run_h12_coppelia_real.py
```

It launches CoppeliaSim through ZMQ Remote API, builds a physical transport scene,
advances the simulator with stepping enabled, saves a `.ttt` scene, and exports
measured CSV/video artifacts under `results/campaigns/H12_coppelia_real`.

The previous `H12_coppelia_closed_loop` campaign remains useful for layout
previews, but its MP4 files are synthetic fallback renders and must not be cited
as physical CoppeliaSim validation.
