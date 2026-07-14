# SP4 v4 paired CoppeliaSim scene

Status: `coppelia_real_kinematic_replay_pass`

The scene replays two controllers in the same frozen narrow-passage world. It validates CoppeliaSim geometry, scene reproducibility and visual plausibility. It does not constitute hardware or independent dynamics validation.

- Scene: `coppeliasim/real_scenes/sp4_v4_paired_narrow_passage.ttt`
- Real CoppeliaSim: `True`
- Synthetic fallback: `False`
- Maximum replay tracking error: `6.893e-09 m`
- Direct minimum swept clearance: `-0.0057 m`
- Proposed minimum swept clearance: `0.0571 m`
- Captured frames: `29`

Interpretation: the common HOCBF is not sufficient to resolve liveness in this paired world; the distributed game and admission closure complete the docking sequence.

Regenerate:

```powershell
python scripts\coppelia\run_sp4_v4_coppelia_paired_scene.py
```
