# CoppeliaSim validation scenes

Generated deterministic warehouse scenes for the MRBO TFM validation package.
Status is `generated_not_opened`: this machine did not launch CoppeliaSim in this run.

| Scene | Policy | Robots | Racks | Humans | Lua |
|---|---|---:|---:|---:|---|
| nominal_smith_qr | smith_qr_full | 15 | 18 | 2 | `coppeliasim\scenes\nominal_smith_qr.lua` |
| comm_r3_smith | smith_full | 15 | 18 | 2 | `coppeliasim\scenes\comm_r3_smith.lua` |
| comm_r3_smith_qr | smith_qr_full | 15 | 18 | 2 | `coppeliasim\scenes\comm_r3_smith_qr.lua` |
| robot_failure_smith_qr | smith_qr_full | 15 | 18 | 2 | `coppeliasim\scenes\robot_failure_smith_qr.lua` |
| human_crossing_smith_qr | smith_qr_full | 15 | 18 | 6 | `coppeliasim\scenes\human_crossing_smith_qr.lua` |
| sensor_degraded_smith_qr | smith_qr_full | 15 | 18 | 4 | `coppeliasim\scenes\sensor_degraded_smith_qr.lua` |

Expected Coppelia smoke:

1. Open CoppeliaSim.
2. Run one generated Lua file from `coppeliasim/scenes`.
3. Confirm Pioneer 3-DX models load, or fallback bases appear with the same names.
4. Export MP4/captures and update `scene_manifest.csv` status from `generated_not_opened` to `opened_pass`.

Regenerate:

```powershell
python scripts\build_coppelia_scene.py --scene-dir coppeliasim\scenes --out results\coppeliasim_validation
```
