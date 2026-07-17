# H12 CoppeliaSim real physics campaign

This campaign is the real CoppeliaSim route. It is not a synthetic fallback render.

- Status: `coppelia_real_error`
- Coppelia executable: `C:\Program Files\CoppeliaRobotics\CoppeliaSimEdu\coppeliaSim.exe`
- Scene: `h12_real_rectangular_transport_physics`

Regenerate:

```powershell
python scripts\coppelia\run_h12_coppelia_real.py
```

Error:

`TimeoutError("Could not connect to CoppeliaSim ZMQ on port 23000: Exception('Failed connecting to CoppeliaSim.')")`
