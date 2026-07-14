# SP0 Final Run Report

## A. Estado de gates

| Gate | Status | Failed checks |
|---|---:|---|
| G1 | PASS | - |
| G2 | PASS | - |
| G3 | PASS | - |
| G4 | PASS | - |
| G5 | PASS | - |
| G6 | PASS | - |
| G7 | PASS | - |
| SMOKE | PASS | - |

## B. Cambios realizados

B0 audit evidence, oracle isolation instrumentation, runtime separation, protocol freeze plumbing, and campaign guard rails.

## C. Reproducibilidad

- commit: `72418e13f1bed1a6d37698e59bf0d07400dc8b10`
- generated_at_utc: `2026-07-11T01:47:22.789585+00:00`
- hardware_id: `f14731301eb54764`

## D. Conteos

Base pre-registered total remains `15436`: B0 300, B2 2400, B3 1536, B4 5760, B5 4000, B6 960, B7 480.

## E. Data-driven

Real IPPO-GNN/MAPPO-GNN training is not reported unless executed under the frozen protocol.

## J. Incidencias y desviaciones

{
  "B1": {
    "catalog": "results\\sp0\\SP0_PROTOCOL_v1\\worlds\\world_catalog.parquet",
    "status": "reused",
    "worlds": 60
  },
  "B2": {
    "runs": 2400,
    "runs_path": "results\\sp0\\SP0_PROTOCOL_v1\\b2\\runs.parquet",
    "status": "reused"
  },
  "B3": {
    "champions": "results\\sp0\\SP0_PROTOCOL_v1\\b3\\champions.yaml",
    "expected_runs": 1536,
    "runs": 1536,
    "status": "reused"
  },
  "blocked_at": "training_before_B4",
  "completed_blocks": [
    "B1",
    "B2",
    "B3"
  ],
  "confirmatory_seeds_opened": false,
  "dry_run": false,
  "reason": "No frozen training/champion.yaml exists for IPPO-GNN/MAPPO-GNN with 3 final seeds and 5_000_000 environment steps per seed.",
  "resume": true,
  "started_at_utc": "2026-07-11T01:47:22.357295+00:00",
  "status": "blocked_before_confirmatory_seed_opening",
  "training": {
    "confirmatory_seeds_opened": false,
    "did_not_converge_under_preregistered_budget": null,
    "reason": "No frozen training/champion.yaml exists for IPPO-GNN/MAPPO-GNN with 3 final seeds and 5_000_000 environment steps per seed.",
    "status": "blocked_missing_real_trainer",
    "timestamp_utc": "2026-07-11T01:47:22.786785+00:00"
  }
}

## K. Claims permitidos

B0 evidence can support readiness only if all G1-G7 gates are PASS. Confirmatory claims require completed B1-B7 results.
