# MARL proxy validation

- Seeds: 2026-2026 (`n=1`).
- Baseline: deterministic parameter-sharing proxy, local observation, decentralized execution.
- This is an empirical comparator, not a trained PPO/MAPPO contribution.
- Scope: smoke validation, not the final 20-seed statistical campaign.

| Scenario | Case | Method | n | Capture | Delivered | Wasted distance |
|---|---|---|---:|---:|---:|---:|
| comm_degradation | R3_p0 | greedy | 1 | 0.3722 | 9 | 12.68 |
| comm_degradation | R3_p0 | marl_proxy | 1 | 0.352 | 9 | 11.17 |
| comm_degradation | R3_p0 | smith | 1 | 0.02229 | 1 | 70.07 |
| comm_degradation | R3_p0 | smith_qr_full | 1 | 0.2704 | 7 | 20.26 |

Full command:

```powershell
python scripts\validate_marl_proxy.py --seeds 20 --out results\marl_validation
```
