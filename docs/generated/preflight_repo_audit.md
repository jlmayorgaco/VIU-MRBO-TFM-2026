# Preflight Repo Audit

- Branch: `main`
- Python: `3.13.9`
- Dirty entries: `0`
- CoppeliaSim in PATH: `not found`

## Canonical SP Status

| SP | Result dir | Core artifacts | Separate ranking (optional) | Hypotheses | Audit failed checks |
|---|---|---:|---:|---:|---:|
| SP1 | `results\sp1\SP1_HOMOGENEOUS_v1_1` | True | False | True | 0 |
| SP2 | `results\sp2\SP2_HETEROGENEOUS_GAME_v1_2` | True | False | True | 0 |
| SP3 | `results\sp3\SP3_WRENCH_NASH_GAME_v1_1` | True | False | True | 0 |
| SP4 | `results\sp4\SP4_DOCKING_GAME_CONFIRMATORY_v3` | True | True | True | 0 |
| SP5 | `results\sp5\SP5_PAYLOAD_TRANSPORT_CONFIRMATORY_v2` | True | False | True | 0 |
| SP6 | `results\sp6\SP6_MC_robustness_comparison_high_power` | True | True | True | 0 |
| SP7 | `results\sp7\SP7_MC_communication_robustness_high_power` | True | True | True | 0 |
| SP8 | `results\sp8\SP8_MC_fleet_ladder_high_power` | True | True | True | 0 |

## Import Decision

`src/viu_mrob_tfm/simulation` and `src/viu_mrob_tfm/controllers` remain live because current tests/scripts import them.

## Required Script Presence

| Script | Exists |
|---|---:|
| `scripts/preflight_repo_audit.py` | True |
| `scripts/generate_method_matrix.py` | True |
| `scripts/generate_regime_map.py` | True |
| `scripts/build_stats_annex.py` | True |
| `scripts/check_claims.py` | True |
| `scripts/validate_theory_vgne_share.py` | True |
| `scripts/validate_theory_poa.py` | True |
| `scripts/validate_theory_stability.py` | True |
| `scripts/build_theory_validation_report.py` | True |
| `scripts/run_sp9_experiment.py` | True |

## Pytest Collect

```text
tests/test_world_pairing.py::test_checkpoint_audit_world_pairing_is_stable_and_order_sensitive
tests/test_wrench_market_games_integration.py::test_wrench_market_games_configs_are_factory_valid
tests/test_wrench_market_games_integration.py::test_wrench_market_games_documentation_is_linked_from_tfm

350 tests collected in <duration>
```
