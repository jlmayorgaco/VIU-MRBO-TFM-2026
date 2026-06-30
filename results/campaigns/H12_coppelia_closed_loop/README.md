# H12 CoppeliaSim closed-loop fallback campaign

Generates CoppeliaSim Lua scene recipes, playback CSVs, validation cameras and synthetic fallback videos.

This campaign is not a physical CoppeliaSim validation run. The MP4 files are
offline renders from generated playback data, not videos captured from a
CoppeliaSim dynamics simulation. Use `H12_coppelia_real` for the real physics
route.

- Status: `fallback_synthetic_render`
- Coppelia available: `True`
- Scene count: `10`

Regenerate:

```powershell
python scripts\coppelia\run_h12_coppelia_campaign.py
```
