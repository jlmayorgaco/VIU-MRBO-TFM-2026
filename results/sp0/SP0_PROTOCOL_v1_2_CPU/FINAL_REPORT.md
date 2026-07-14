# SP0_PROTOCOL_v1_2_CPU Final Report

Overall status: confirmatory_blocks_complete

## 1. Gates B0

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

## 2. Changes from v1

The active SP0 revision separates continuous convergence, timeout, closure success and final assignment success; uses method-specific residuals, isolates public/oracle views, records seconds-only runtimes, implements checkpoint-backed PPO with local GNN actors, and preserves audit trajectories.

## 3. IPPO/MAPPO training state

{
  "results\\sp0\\SP0_PROTOCOL_v1_2_CPU\\training\\dry_run\\status.json": {
    "artifact_scope": "dry_run_only",
    "champion_id": "MAPPO-GNN",
    "confirmatory_seeds_opened": false,
    "device": "cpu",
    "final_seeds": [
      {
        "algorithm": "MAPPO-GNN",
        "checkpoint_hash": "4cbad6f0688751446e32303a66b4a105a826945784cbba25f63351f690448283",
        "checkpoint_path": "results\\sp0\\SP0_PROTOCOL_v1_2_CPU\\training\\dry_run\\final_seeds\\DD_seed_1\\checkpoint.pt",
        "device": "cpu",
        "discount_factor": 0.99,
        "entropy_coefficient": 0.01,
        "episode_horizon": 4,
        "gnn_layers": 3,
        "gpu_hours": 0.0,
        "hidden_dim": 128,
        "history": [
          {
            "loss": {
              "entropy": 3.042659534348382,
              "policy_loss": -3.094060553598954e-08,
              "total_loss": 0.2157486379146576,
              "value_loss": 0.24617523493038282
            },
            "optimizer_updates": 1,
            "training_steps": 64,
            "validation": {
              "CVaR95_NR": 0.00902286603061031,
              "NR_minus_Greedy": 0.0014528857498620107,
              "algorithm": "MAPPO-GNN",
              "greedy_mean_NR": 0.0014670780605179064,
              "inference_time_s": 0.009099170371579627,
              "mean_NR": 0.002919963810379917,
              "mean_closure_NR_delta": -0.9291205059061481,
              "mean_closure_vs_raw_decode_NR_delta": -0.9291205059061481,
              "mean_raw_decode_NR": 0.9320404697165284,
              "n_validation_worlds": 54.0,
              "raw_success": 0.0,
              "success": 1.0
            }
          }
        ],
        "learning_rate": 0.0001,
        "optimizer_updates": 1,
        "policy_version": "sp0_gnn_ppo_v1_2_cpu_batched",
        "ppo_clip": 0.1,
        "ppo_epochs": 1,
        "progress_checkpoint_path": "results\\sp0\\SP0_PROTOCOL_v1_2_CPU\\training\\dry_run\\final_seeds\\DD_seed_1\\progress.pt",
        "resume_reused": true,
        "resumed_from_step": 0,
        "rollout_environment_steps": 512,
        "timestamp_utc": "2026-07-11T11:38:07.344555+00:00",
        "train_seed": 15001,
        "trainer_version": "sp0_gnn_ppo_v1_2_cpu_batched",
        "training_converged": false,
        "training_step_unit": "joint_environment_transition",
        "training_steps": 64,
        "training_wall_s": 1.086513200076297
      },
      {
        "algorithm": "MAPPO-GNN",
        "checkpoint_hash": "49895f8e4ca28b0c125d355c32239e237b8e4ef8fc653f5f6f6d0988680dfdf7",
        "checkpoint_path": "results\\sp0\\SP0_PROTOCOL_v1_2_CPU\\training\\dry_run\\final_seeds\\DD_seed_2\\checkpoint.pt",
        "device": "cpu",
        "discount_factor": 0.99,
        "entropy_coefficient": 0.01,
        "episode_horizon": 4,
        "gnn_layers": 3,
        "gpu_hours": 0.0,
        "hidden_dim": 128,
        "history": [
          {
            "loss": {
              "entropy": 3.216702710257637,
              "policy_loss": -4.6359168131074324e-08,
              "total_loss": 0.22113177180290222,
              "value_loss": 0.25329883909887735
            },
            "optimizer_updates": 1,
            "training_steps": 64,
            "validation": {
              "CVaR95_NR": 0.0034952203386420856,
              "NR_minus_Greedy": -0.0007083554756718499,
              "algorithm": "MAPPO-GNN",
              "greedy_mean_NR": 0.0014670780605179064,
              "inference_time_s": 0.009840214816870651,
              "mean_NR": 0.0007587225848460564,
              "mean_closure_NR_delta": -0.9202233437445989,
              "mean_closure_vs_raw_decode_NR_delta": -0.9202233437445989,
              "mean_raw_decode_NR": 0.9209820663294446,
              "n_validation_worlds": 54.0,
              "raw_success": 0.0,
              "success": 1.0
            }
          }
        ],
        "learning_rate": 0.0001,
        "optimizer_updates": 1,
        "policy_version": "sp0_gnn_ppo_v1_2_cpu_batched",
        "ppo_clip": 0.1,
        "ppo_epochs": 1,
        "progress_checkpoint_path": "results\\sp0\\SP0_PROTOCOL_v1_2_CPU\\training\\dry_run\\final_seeds\\DD_seed_2\\progress.pt",
        "resume_reused": true,
        "resumed_from_step": 0,
        "rollout_environment_steps": 512,
        "timestamp_utc": "2026-07-11T11:38:08.524277+00:00",
        "train_seed": 15002,
        "trainer_version": "sp0_gnn_ppo_v1_2_cpu_batched",
        "training_converged": false,
        "training_step_unit": "joint_environment_transition",
        "training_steps": 64,
        "training_wall_s": 1.1765865000197664
      },
      {
        "algorithm": "MAPPO-GNN",
        "checkpoint_hash": "09903587e65e1590bdc50a0de26a6cd29ef65458003b423329dd2d37092f2f75",
        "checkpoint_path": "results\\sp0\\SP0_PROTOCOL_v1_2_CPU\\training\\dry_run\\final_seeds\\DD_seed_3\\checkpoint.pt",
        "device": "cpu",
        "discount_factor": 0.99,
        "entropy_coefficient": 0.01,
        "episode_horizon": 4,
        "gnn_layers": 3,
        "gpu_hours": 0.0,
        "hidden_dim": 128,
        "history": [
          {
            "loss": {
              "entropy": 3.048321897333319,
              "policy_loss": -1.2824029632652056e-07,
              "total_loss": 0.23617589473724365,
              "value_loss": 0.2666592557321895
            },
            "optimizer_updates": 1,
            "training_steps": 64,
            "validation": {
              "CVaR95_NR": 0.01194461288310461,
              "NR_minus_Greedy": 0.002734446642629561,
              "algorithm": "MAPPO-GNN",
              "greedy_mean_NR": 0.0014670780605179064,
              "inference_time_s": 0.006610633316018653,
              "mean_NR": 0.004201524703147467,
              "mean_closure_NR_delta": -1.6941461830220252,
              "mean_closure_vs_raw_decode_NR_delta": -1.6941461830220252,
              "mean_raw_decode_NR": 1.6983477077251725,
              "n_validation_worlds": 54.0,
              "raw_success": 0.0,
              "success": 1.0
            }
          }
        ],
        "learning_rate": 0.0001,
        "optimizer_updates": 1,
        "policy_version": "sp0_gnn_ppo_v1_2_cpu_batched",
        "ppo_clip": 0.1,
        "ppo_epochs": 1,
        "progress_checkpoint_path": "results\\sp0\\SP0_PROTOCOL_v1_2_CPU\\training\\dry_run\\final_seeds\\DD_seed_3\\progress.pt",
        "resume_reused": true,
        "resumed_from_step": 0,
        "rollout_environment_steps": 512,
        "timestamp_utc": "2026-07-11T11:38:09.383272+00:00",
        "train_seed": 15003,
        "trainer_version": "sp0_gnn_ppo_v1_2_cpu_batched",
        "training_converged": false,
        "training_step_unit": "joint_environment_transition",
        "training_steps": 64,
        "training_wall_s": 0.8535536000272259
      }
    ],
    "status": "dry_run_complete",
    "timestamp_utc": "2026-07-11T12:42:04.467364+00:00"
  },
  "results\\sp0\\SP0_PROTOCOL_v1_2_CPU\\training\\status.json": {
    "champion_id": "MAPPO-GNN",
    "champion_path": "results\\sp0\\SP0_PROTOCOL_v1_2_CPU\\training\\champion.yaml",
    "champion_sha256": "dcf690e1f3e417aab639ad123d04b460c27a58e379a779fd8447e9e00ccef807",
    "confirmatory_seeds_opened": false,
    "final_seeds": [
      {
        "algorithm": "MAPPO-GNN",
        "checkpoint_hash": "de6de33136dc5b71017deb71485f73ba1336e43c5e50b4a8a3e28dc18fb3e4ac",
        "checkpoint_path": "results\\sp0\\SP0_PROTOCOL_v1_2_CPU\\training\\final_seeds\\DD_seed_1\\checkpoint.pt",
        "device": "cpu",
        "discount_factor": 0.95,
        "entropy_coefficient": 0.001,
        "episode_horizon": 4,
        "gnn_layers": 3,
        "gpu_hours": 0.0,
        "hidden_dim": 64,
        "history": [
          {
            "loss": {
              "entropy": 2.794031613943528,
              "policy_loss": -7.04510683124937e-09,
              "total_loss": 0.045061253011226654,
              "value_loss": 0.047855286472508696
            },
            "optimizer_updates": 98,
            "training_steps": 50176,
            "validation": {
              "CVaR95_NR": 0.0034952203386420856,
              "NR_minus_Greedy": -0.0007083554756718499,
              "algorithm": "MAPPO-GNN",
              "greedy_mean_NR": 0.0014670780605179064,
              "inference_time_s": 0.0034721462870948017,
              "mean_NR": 0.0007587225848460564,
              "mean_closure_NR_delta": -0.9202233437445989,
              "mean_closure_vs_raw_decode_NR_delta": -0.9202233437445989,
              "mean_raw_decode_NR": 0.9209820663294446,
              "n_validation_worlds": 54.0,
              "raw_success": 0.0,
              "success": 1.0
            }
          },
          {
            "loss": {
              "entropy": 2.8345029329684,
              "policy_loss": 2.644574672097666e-09,
              "total_loss": 0.03166806325316429,
              "value_loss": 0.034502559796026545
            },
            "optimizer_updates": 196,
            "training_steps": 100352,
            "validation": {
              "CVaR95_NR": 0.0034952203386420856,
              "NR_minus_Greedy": -0.0007083554756718499,
              "algorithm": "MAPPO-GNN",
              "greedy_mean_NR": 0.0014670780605179064,
              "inference_time_s": 0.003173716665952708,
              "mean_NR": 0.0007587225848460564,
              "mean_closure_NR_delta": -0.9202233437445989,
              "mean_closure_vs_raw_decode_NR_delta": -0.9202233437445989,
              "mean_raw_decode_NR": 0.9209820663294446,
              "n_validation_worlds": 54.0,
              "raw_success": 0.0,
              "success": 1.0
            }
          },
          {
            "loss": {
              "entropy": 2.8967535660998656,
              "policy_loss": -1.8442028069595717e-11,
              "total_loss": 0.03388368710875511,
              "value_loss": 0.0367804372640136
            },
            "optimizer_updates": 293,
            "training_steps": 150016,
            "validation": {
              "CVaR95_NR": 0.0034952203386420856,
              "NR_minus_Greedy": -0.0007083554756718499,
              "algorithm": "MAPPO-GNN",
              "greedy_mean_NR": 0.0014670780605179064,
              "inference_time_s": 0.0034101759320711374,
              "mean_NR": 0.0007587225848460564,
              "mean_closure_NR_delta": -0.9202233437445989,
              "mean_closure_vs_raw_decode_NR_delta": -0.9202233437445989,
              "mean_raw_decode_NR": 0.9209820663294446,
              "n_validation_worlds": 54.0,
              "raw_success": 0.0,
              "success": 1.0
            }
          },
          {
            "loss": {
              "entropy": 2.8406622152960757,
              "policy_loss": 5.842634165538485e-09,
              "total_loss": 0.033612675964832306,
              "value_loss": 0.03645332548664419
            },
            "optimizer_updates": 391,
            "training_steps": 200000,
            "validation": {
              "CVaR95_NR": 0.0034952203386420856,
              "NR_minus_Greedy": -0.0007083554756718499,
              "algorithm": "MAPPO-GNN",
              "greedy_mean_NR": 0.0014670780605179064,
              "inference_time_s": 0.0031800314814231737,
              "mean_NR": 0.0007587225848460564,
              "mean_closure_NR_delta": -0.9202233437445989,
              "mean_closure_vs_raw_decode_NR_delta": -0.9202233437445989,
              "mean_raw_decode_NR": 0.9209820663294446,
              "n_validation_worlds": 54.0,
              "raw_success": 0.0,
              "success": 1.0
            }
          }
        ],
        "learning_rate": 0.001,
        "optimizer_updates": 391,
        "policy_version": "sp0_gnn_ppo_v1_2_cpu_batched",
        "ppo_clip": 0.2,
        "ppo_epochs": 1,
        "progress_checkpoint_path": "results\\sp0\\SP0_PROTOCOL_v1_2_CPU\\training\\final_seeds\\DD_seed_1\\progress.pt",
        "resume_reused": false,
        "resumed_from_step": 0,
        "rollout_environment_steps": 512,
        "timestamp_utc": "2026-07-11T12:22:03.322992+00:00",
        "train_seed": 15001,
        "trainer_version": "sp0_gnn_ppo_v1_2_cpu_batched",
        "training_converged": true,
        "training_step_unit": "joint_environment_transition",
        "training_steps": 200000,
        "training_wall_s": 572.8382164000068
      },
      {
        "algorithm": "MAPPO-GNN",
        "checkpoint_hash": "58655bb1adf2660fce2df4520a516f1c1326a417a0fe9efb7dbf9f833a4a7776",
        "checkpoint_path": "results\\sp0\\SP0_PROTOCOL_v1_2_CPU\\training\\final_seeds\\DD_seed_2\\checkpoint.pt",
        "device": "cpu",
        "discount_factor": 0.95,
        "entropy_coefficient": 0.001,
        "episode_horizon": 4,
        "gnn_layers": 3,
        "gpu_hours": 0.0,
        "hidden_dim": 64,
        "history": [
          {
            "loss": {
              "entropy": 2.8560756213373417,
              "policy_loss": -1.10418676424473e-08,
              "total_loss": 0.05052801966667175,
              "value_loss": 0.053384098458847555
            },
            "optimizer_updates": 98,
            "training_steps": 50176,
            "validation": {
              "CVaR95_NR": 0.0034952203386420856,
              "NR_minus_Greedy": -0.0007083554756718499,
              "algorithm": "MAPPO-GNN",
              "greedy_mean_NR": 0.0014670780605179064,
              "inference_time_s": 0.003303359251866048,
              "mean_NR": 0.0007587225848460564,
              "mean_closure_NR_delta": -0.9202233437445989,
              "mean_closure_vs_raw_decode_NR_delta": -0.9202233437445989,
              "mean_raw_decode_NR": 0.9209820663294446,
              "n_validation_worlds": 54.0,
              "raw_success": 0.0,
              "success": 1.0
            }
          },
          {
            "loss": {
              "entropy": 2.758724585374196,
              "policy_loss": -8.046627045232846e-09,
              "total_loss": 0.029471376910805702,
              "value_loss": 0.032230105387667816
            },
            "optimizer_updates": 196,
            "training_steps": 100352,
            "validation": {
              "CVaR95_NR": 0.0034952203386420856,
              "NR_minus_Greedy": -0.0007083554756718499,
              "algorithm": "MAPPO-GNN",
              "greedy_mean_NR": 0.0014670780605179064,
              "inference_time_s": 0.0032627351918361252,
              "mean_NR": 0.0007587225848460564,
              "mean_closure_NR_delta": -0.9202233437445989,
              "mean_closure_vs_raw_decode_NR_delta": -0.9202233437445989,
              "mean_raw_decode_NR": 0.9209820663294446,
              "n_validation_worlds": 54.0,
              "raw_success": 0.0,
              "success": 1.0
            }
          },
          {
            "loss": {
              "entropy": 2.689457595543783,
              "policy_loss": 1.954250650193501e-09,
              "total_loss": 0.032508403062820435,
              "value_loss": 0.035197860967428954
            },
            "optimizer_updates": 293,
            "training_steps": 150016,
            "validation": {
              "CVaR95_NR": 0.0034952203386420856,
              "NR_minus_Greedy": -0.0007083554756718499,
              "algorithm": "MAPPO-GNN",
              "greedy_mean_NR": 0.0014670780605179064,
              "inference_time_s": 0.0030990407491723695,
              "mean_NR": 0.0007587225848460564,
              "mean_closure_NR_delta": -0.9202233437445989,
              "mean_closure_vs_raw_decode_NR_delta": -0.9202233437445989,
              "mean_raw_decode_NR": 0.9209820663294446,
              "n_validation_worlds": 54.0,
              "raw_success": 0.0,
              "success": 1.0
            }
          },
          {
            "loss": {
              "entropy": 2.7973415729950886,
              "policy_loss": 9.95944956887207e-09,
              "total_loss": 0.02245783619582653,
              "value_loss": 0.025255165428721478
            },
            "optimizer_updates": 391,
            "training_steps": 200000,
            "validation": {
              "CVaR95_NR": 0.0034952203386420856,
              "NR_minus_Greedy": -0.0007083554756718499,
              "algorithm": "MAPPO-GNN",
              "greedy_mean_NR": 0.0014670780605179064,
              "inference_time_s": 0.003611696301959455,
              "mean_NR": 0.0007587225848460564,
              "mean_closure_NR_delta": -0.9202233437445989,
              "mean_closure_vs_raw_decode_NR_delta": -0.9202233437445989,
              "mean_raw_decode_NR": 0.9209820663294446,
              "n_validation_worlds": 54.0,
              "raw_success": 0.0,
              "success": 1.0
            }
          }
        ],
        "learning_rate": 0.001,
        "optimizer_updates": 391,
        "policy_version": "sp0_gnn_ppo_v1_2_cpu_batched",
        "ppo_clip": 0.2,
        "ppo_epochs": 1,
        "progress_checkpoint_path": "results\\sp0\\SP0_PROTOCOL_v1_2_CPU\\training\\final_seeds\\DD_seed_2\\progress.pt",
        "resume_reused": false,
        "resumed_from_step": 0,
        "rollout_environment_steps": 512,
        "timestamp_utc": "2026-07-11T12:31:22.036863+00:00",
        "train_seed": 15002,
        "trainer_version": "sp0_gnn_ppo_v1_2_cpu_batched",
        "training_converged": true,
        "training_step_unit": "joint_environment_transition",
        "training_steps": 200000,
        "training_wall_s": 558.7004057000158
      },
      {
        "algorithm": "MAPPO-GNN",
        "checkpoint_hash": "ac07f856d8fe7aee84d8f97aabcd6eb2539b70dfa7a8c6f3df569eec44f6ff8f",
        "checkpoint_path": "results\\sp0\\SP0_PROTOCOL_v1_2_CPU\\training\\final_seeds\\DD_seed_3\\checkpoint.pt",
        "device": "cpu",
        "discount_factor": 0.95,
        "entropy_coefficient": 0.001,
        "episode_horizon": 4,
        "gnn_layers": 3,
        "gpu_hours": 0.0,
        "hidden_dim": 64,
        "history": [
          {
            "loss": {
              "entropy": 2.9921135483561336,
              "policy_loss": -1.4599110621793532e-08,
              "total_loss": 0.0407123863697052,
              "value_loss": 0.04370451212634106
            },
            "optimizer_updates": 98,
            "training_steps": 50176,
            "validation": {
              "CVaR95_NR": 0.0034952203386420856,
              "NR_minus_Greedy": -0.0007083554756718499,
              "algorithm": "MAPPO-GNN",
              "greedy_mean_NR": 0.0014670780605179064,
              "inference_time_s": 0.003343424072092468,
              "mean_NR": 0.0007587225848460564,
              "mean_closure_NR_delta": -0.9202233437445989,
              "mean_closure_vs_raw_decode_NR_delta": -0.9202233437445989,
              "mean_raw_decode_NR": 0.9209820663294446,
              "n_validation_worlds": 54.0,
              "raw_success": 0.0,
              "success": 1.0
            }
          },
          {
            "loss": {
              "entropy": 2.7222670944335183,
              "policy_loss": -1.9955972060600735e-08,
              "total_loss": 0.03784457966685295,
              "value_loss": 0.04056686195857533
            },
            "optimizer_updates": 196,
            "training_steps": 100352,
            "validation": {
              "CVaR95_NR": 0.0034952203386420856,
              "NR_minus_Greedy": -0.0007083554756718499,
              "algorithm": "MAPPO-GNN",
              "greedy_mean_NR": 0.0014670780605179064,
              "inference_time_s": 0.0035785925941093375,
              "mean_NR": 0.0007587225848460564,
              "mean_closure_NR_delta": -0.9202233437445989,
              "mean_closure_vs_raw_decode_NR_delta": -0.9202233437445989,
              "mean_raw_decode_NR": 0.9209820663294446,
              "n_validation_worlds": 54.0,
              "raw_success": 0.0,
              "success": 1.0
            }
          },
          {
            "loss": {
              "entropy": 2.6579052250960786,
              "policy_loss": 9.480221517532694e-09,
              "total_loss": 0.028712168335914612,
              "value_loss": 0.031370070281213726
            },
            "optimizer_updates": 293,
            "training_steps": 150016,
            "validation": {
              "CVaR95_NR": 0.0034952203386420856,
              "NR_minus_Greedy": -0.0007083554756718499,
              "algorithm": "MAPPO-GNN",
              "greedy_mean_NR": 0.0014670780605179064,
              "inference_time_s": 0.003103553701226634,
              "mean_NR": 0.0007587225848460564,
              "mean_closure_NR_delta": -0.9202233437445989,
              "mean_closure_vs_raw_decode_NR_delta": -0.9202233437445989,
              "mean_raw_decode_NR": 0.9209820663294446,
              "n_validation_worlds": 54.0,
              "raw_success": 0.0,
              "success": 1.0
            }
          },
          {
            "loss": {
              "entropy": 2.5738576034923177,
              "policy_loss": -1.3591169016613502e-08,
              "total_loss": 0.03505243733525276,
              "value_loss": 0.03762629194246544
            },
            "optimizer_updates": 391,
            "training_steps": 200000,
            "validation": {
              "CVaR95_NR": 0.0034952203386420856,
              "NR_minus_Greedy": -0.0007083554756718499,
              "algorithm": "MAPPO-GNN",
              "greedy_mean_NR": 0.0014670780605179064,
              "inference_time_s": 0.0028991851744379986,
              "mean_NR": 0.0007587225848460564,
              "mean_closure_NR_delta": -0.9202233437445989,
              "mean_closure_vs_raw_decode_NR_delta": -0.9202233437445989,
              "mean_raw_decode_NR": 0.9209820663294446,
              "n_validation_worlds": 54.0,
              "raw_success": 0.0,
              "success": 1.0
            }
          }
        ],
        "learning_rate": 0.001,
        "optimizer_updates": 391,
        "policy_version": "sp0_gnn_ppo_v1_2_cpu_batched",
        "ppo_clip": 0.2,
        "ppo_epochs": 1,
        "progress_checkpoint_path": "results\\sp0\\SP0_PROTOCOL_v1_2_CPU\\training\\final_seeds\\DD_seed_3\\progress.pt",
        "resume_reused": false,
        "resumed_from_step": 0,
        "rollout_environment_steps": 512,
        "timestamp_utc": "2026-07-11T12:40:34.314045+00:00",
        "train_seed": 15003,
        "trainer_version": "sp0_gnn_ppo_v1_2_cpu_batched",
        "training_converged": true,
        "training_step_unit": "joint_environment_transition",
        "training_steps": 200000,
        "training_wall_s": 552.2554412999889
      }
    ],
    "status": "complete",
    "timestamp_utc": "2026-07-11T15:09:17.605889+00:00"
  }
}

## 4. Three final seeds

| Train seed | Steps | Converged | Checkpoint hash |
|---:|---:|---:|---|
| 15001 | 200000 | True | de6de33136dc5b71017deb71485f73ba1336e43c5e50b4a8a3e28dc18fb3e4ac |
| 15002 | 200000 | True | 58655bb1adf2660fce2df4520a516f1c1326a417a0fe9efb7dbf9f833a4a7776 |
| 15003 | 200000 | True | ac07f856d8fe7aee84d8f97aabcd6eb2539b70dfa7a8c6f3df569eec44f6ff8f |

## 5. Planned vs executed counts

| Block | Planned | Executed |
|---|---:|---:|
| B0 | 300 | 300 |
| B2 | 2400 | 2400 |
| B3 | 1536 | 1536 |
| B4 | 5760 | 5760 |
| B5 | 4000 | 4000 |
| B6 | 960 | 960 |
| B7 | 480 | 480 |
| TOTAL | 15436 | 15436 |

## 6. Duration and hardware

- commit: 72418e13f1bed1a6d37698e59bf0d07400dc8b10
- generated_at_utc: 2026-07-11T15:33:12.768431+00:00
- hardware_id: 1d4fdee9c285efbf

{
  "MKL_NUM_THREADS": "",
  "OMP_NUM_THREADS": "",
  "OPENBLAS_NUM_THREADS": "",
  "batch_size": 1,
  "cpu_model": "Intel64 Family 6 Model 170 Stepping 4, GenuineIntel",
  "gpu_memory_bytes": null,
  "gpu_model": "not_detected",
  "jax_version": "not_installed",
  "num_workers": 1,
  "python_version": "3.13.9",
  "ram_bytes": 33863831552,
  "torch_version": "2.11.0+cpu"
}

## 7. Results by regime

| Block | Method | N | K | Success | Mean NR | CVaR95 |
|---|---|---:|---:|---:|---:|---:|
| B4 | BNN | 8.0 | 6.0 | 1 | 9.54e-05 | 0.00118 |
| B4 | BNN | 8.0 | 8.0 | 1 | 6.96e-05 | 0.000713 |
| B4 | BNN | 8.0 | 12.0 | 1 | 4.52e-05 | 0.000287 |
| B4 | BNN | 16.0 | 11.0 | 1 | 6.58e-05 | 0.000365 |
| B4 | BNN | 16.0 | 16.0 | 1 | 6.3e-05 | 0.000362 |
| B4 | BNN | 16.0 | 24.0 | 1 | 7.76e-05 | 0.000285 |
| B4 | BNN | 32.0 | 22.0 | 1 | 7.37e-05 | 0.000246 |
| B4 | BNN | 32.0 | 32.0 | 1 | 4.52e-05 | 0.000161 |
| B4 | BNN | 32.0 | 48.0 | 1 | 3.17e-05 | 8.96e-05 |
| B4 | BNN | 64.0 | 43.0 | 1 | 2.78e-05 | 7.03e-05 |
| B4 | BNN | 64.0 | 64.0 | 1 | 3.02e-05 | 8.17e-05 |
| B4 | BNN | 64.0 | 96.0 | 1 | 2.14e-05 | 8.36e-05 |
| B4 | EPS-AUCTION | 8.0 | 6.0 | 1 | 5.17e-07 | 5.17e-07 |
| B4 | EPS-AUCTION | 8.0 | 8.0 | 1 | 1.22e-06 | 1.49e-05 |
| B4 | EPS-AUCTION | 8.0 | 12.0 | 1 | 7.44e-07 | 1.12e-05 |
| B4 | EPS-AUCTION | 16.0 | 11.0 | 1 | 3.29e-07 | 4.72e-06 |
| B4 | EPS-AUCTION | 16.0 | 16.0 | 1 | 4.47e-07 | 3.49e-06 |
| B4 | EPS-AUCTION | 16.0 | 24.0 | 1 | 8.89e-08 | 1.72e-06 |
| B4 | EPS-AUCTION | 32.0 | 22.0 | 1 | 4e-07 | 4.23e-06 |
| B4 | EPS-AUCTION | 32.0 | 32.0 | 1 | 3.57e-07 | 1.84e-06 |
| B4 | EPS-AUCTION | 32.0 | 48.0 | 1 | 2.53e-07 | 2.13e-06 |
| B4 | EPS-AUCTION | 64.0 | 43.0 | 1 | 1.65e-07 | 1.28e-06 |
| B4 | EPS-AUCTION | 64.0 | 64.0 | 1 | 2.35e-07 | 1.03e-06 |
| B4 | EPS-AUCTION | 64.0 | 96.0 | 1 | 1.17e-07 | 6.24e-07 |
| B4 | GRD | 8.0 | 6.0 | 1 | 0.00447 | 0.0126 |
| B4 | GRD | 8.0 | 8.0 | 1 | 0.00243 | 0.00599 |
| B4 | GRD | 8.0 | 12.0 | 1 | 0.000726 | 0.00257 |
| B4 | GRD | 16.0 | 11.0 | 1 | 0.00399 | 0.00868 |
| B4 | GRD | 16.0 | 16.0 | 1 | 0.00127 | 0.00285 |
| B4 | GRD | 16.0 | 24.0 | 1 | 0.000453 | 0.00159 |
| B4 | GRD | 32.0 | 22.0 | 1 | 0.00206 | 0.00359 |
| B4 | GRD | 32.0 | 32.0 | 1 | 0.000752 | 0.00146 |
| B4 | GRD | 32.0 | 48.0 | 1 | 0.000222 | 0.000562 |
| B4 | GRD | 64.0 | 43.0 | 1 | 0.00108 | 0.00173 |
| B4 | GRD | 64.0 | 64.0 | 1 | 0.000341 | 0.000538 |
| B4 | GRD | 64.0 | 96.0 | 1 | 6.03e-05 | 0.000119 |
| B4 | HUN | 8.0 | 6.0 | 1 | 0 | 0 |
| B4 | HUN | 8.0 | 8.0 | 1 | 3.12e-19 | 2.78e-18 |
| B4 | HUN | 8.0 | 12.0 | 1 | 3.82e-19 | 2.78e-18 |
| B4 | HUN | 16.0 | 11.0 | 1 | 2.14e-19 | 1.55e-18 |
| B4 | HUN | 16.0 | 16.0 | 1 | 2.7e-19 | 1.8e-18 |
| B4 | HUN | 16.0 | 24.0 | 1 | 3.08e-19 | 1.54e-18 |
| B4 | HUN | 32.0 | 22.0 | 1 | 9.46e-20 | 8.41e-19 |
| B4 | HUN | 32.0 | 32.0 | 1 | 1.63e-19 | 8.16e-19 |
| B4 | HUN | 32.0 | 48.0 | 1 | 1.02e-19 | 4.54e-19 |
| B4 | HUN | 64.0 | 43.0 | 1 | 8.03e-20 | 4.59e-19 |
| B4 | HUN | 64.0 | 64.0 | 1 | 1.42e-19 | 4.47e-19 |
| B4 | HUN | 64.0 | 96.0 | 1 | 5.52e-20 | 2.31e-19 |
| B4 | HYB | 8.0 | 6.0 | 1 | 0.000177 | 0.00244 |
| B4 | HYB | 8.0 | 8.0 | 1 | 5.1e-05 | 0.000444 |
| B4 | HYB | 8.0 | 12.0 | 1 | 7.11e-05 | 0.000656 |
| B4 | HYB | 16.0 | 11.0 | 1 | 6.92e-05 | 0.0006 |
| B4 | HYB | 16.0 | 16.0 | 1 | 6.42e-05 | 0.00039 |
| B4 | HYB | 16.0 | 24.0 | 1 | 5.57e-05 | 0.000256 |
| B4 | HYB | 32.0 | 22.0 | 1 | 5.18e-05 | 0.000209 |
| B4 | HYB | 32.0 | 32.0 | 1 | 3.48e-05 | 0.000109 |
| B4 | HYB | 32.0 | 48.0 | 1 | 2.64e-05 | 6.29e-05 |
| B4 | HYB | 64.0 | 43.0 | 1 | 2.03e-05 | 5.79e-05 |
| B4 | HYB | 64.0 | 64.0 | 1 | 2.45e-05 | 7.73e-05 |
| B4 | HYB | 64.0 | 96.0 | 1 | 1.24e-05 | 2.63e-05 |
| B4 | LOG | 8.0 | 6.0 | 1 | 6.97e-05 | 0.000471 |
| B4 | LOG | 8.0 | 8.0 | 1 | 4.78e-05 | 0.000444 |
| B4 | LOG | 8.0 | 12.0 | 1 | 8.97e-05 | 0.000734 |
| B4 | LOG | 16.0 | 11.0 | 1 | 6.57e-05 | 0.000377 |
| B4 | LOG | 16.0 | 16.0 | 1 | 4.86e-05 | 0.000282 |
| B4 | LOG | 16.0 | 24.0 | 1 | 5.4e-05 | 0.000247 |
| B4 | LOG | 32.0 | 22.0 | 1 | 4.96e-05 | 0.000189 |
| B4 | LOG | 32.0 | 32.0 | 1 | 4.03e-05 | 0.000148 |
| B4 | LOG | 32.0 | 48.0 | 1 | 3.47e-05 | 0.000104 |
| B4 | LOG | 64.0 | 43.0 | 1 | 2.13e-05 | 5.48e-05 |
| B4 | LOG | 64.0 | 64.0 | 1 | 2.45e-05 | 6.8e-05 |
| B4 | LOG | 64.0 | 96.0 | 1 | 1.45e-05 | 3.06e-05 |
| B4 | MAPPO-GNN::train_seed=15001 | 8.0 | 6.0 | 1 | 0.00106 | 0.0054 |
| B4 | MAPPO-GNN::train_seed=15001 | 8.0 | 8.0 | 1 | 0.0018 | 0.00497 |
| B4 | MAPPO-GNN::train_seed=15001 | 8.0 | 12.0 | 1 | 0.000672 | 0.00256 |
| B4 | MAPPO-GNN::train_seed=15001 | 16.0 | 11.0 | 1 | 0.000593 | 0.00313 |
| B4 | MAPPO-GNN::train_seed=15001 | 16.0 | 16.0 | 1 | 0.00102 | 0.00274 |
| B4 | MAPPO-GNN::train_seed=15001 | 16.0 | 24.0 | 1 | 0.000385 | 0.00116 |
| B4 | MAPPO-GNN::train_seed=15001 | 32.0 | 22.0 | 1 | 0.000345 | 0.0012 |
| B4 | MAPPO-GNN::train_seed=15001 | 32.0 | 32.0 | 1 | 0.000618 | 0.000983 |

## 8. Continuous dynamics vs closures

See the versioned Parquet tables and figures; no claim is emitted when its artifact is absent.

## 9. Dynamic-fitness interaction

See the versioned Parquet tables and figures; no claim is emitted when its artifact is absent.

## 10. Method-connectivity interaction

See the versioned Parquet tables and figures; no claim is emitted when its artifact is absent.

## 11. Robustness

See the versioned Parquet tables and figures; no claim is emitted when its artifact is absent.

## 12. Generalization

See the versioned Parquet tables and figures; no claim is emitted when its artifact is absent.

## 13. Pareto fronts

See the versioned Parquet tables and figures; no claim is emitted when its artifact is absent.

## 14. Observed PoA/PoS

See the versioned Parquet tables and figures; no claim is emitted when its artifact is absent.

## 15. Hypotheses with Holm

| Hypothesis | Status | Effect | CI95 | Raw p | Holm p | Decision | Claim | Source |
|---|---|---:|---|---:|---:|---|---|---|
| H0-SP0-P1 | confirmatory | 0.0 | [0.0, 0.0] | 1.0 | 1.0 | fail_to_reject_H0 | not_supported | B4 |
| H0-SP0-P2 | confirmatory | 0.0014886450172317447 | [0.0013252764578807407, 0.001682779476008436] | 7.100712713627627e-79 | 2.840285085451051e-78 | reject_H0 | empirically_supported | B4 |
| H0-SP0-P3 | confirmatory | 23893581.86026697 | [nan, nan] | 0.0 | 0.0 | reject_H0 | empirically_supported | cox_time_to_epsilon_world_cluster |
| H0-SP0-P4 | confirmatory | 6039216685.82423 | [nan, nan] | 0.0 | 0.0 | reject_H0 | empirically_supported | negative_binomial_messages_to_epsilon_solution_GEE |
| H0-SP0-P5 | confirmatory | 298.79821075973445 | [nan, nan] | 8.507197566994097e-53 | 2.552159270098229e-52 | reject_H0 | empirically_supported | robust_regret_GEE_world_cluster |
| H0-SP0-P6 | confirmatory | 172.90082151520517 | [nan, nan] | 1.5340415447174375e-32 | 3.068083089434875e-32 | reject_H0 | empirically_supported | robust_regret_GEE_world_cluster |
| H0-SP0-G1 | exploratory_preregistered_B2_only | nan | [nan, nan] | nan | nan | exploratory_only | exploratory_only | B2_exploratory |
| H0-SP0-G2 | exploratory_preregistered_B2_only | nan | [nan, nan] | nan | nan | exploratory_only | exploratory_only | B2_exploratory |
| H0-SP0-G3 | exploratory_preregistered_B2_only | nan | [nan, nan] | nan | nan | exploratory_only | exploratory_only | B2_exploratory |
| H0-SP0-G4 | exploratory_preregistered_B2_only | nan | [nan, nan] | nan | nan | exploratory_only | exploratory_only | B2_exploratory |
| H0-SP0-G5 | exploratory_preregistered_B2_only | nan | [nan, nan] | nan | nan | exploratory_only | exploratory_only | B2_exploratory |
| H0-SP0-G6 | exploratory_preregistered_B2_only | nan | [nan, nan] | nan | nan | exploratory_only | exploratory_only | B2_exploratory |
| H0-SP0-C1 | confirmatory | 0.0 | [0.0, 0.0] | 0.001999500124968758 | 0.001999500124968758 | reject_H0_noninferior | empirically_supported | locality |
| H0-SP0-C2 | confirmatory | 502.7506530635219 | [nan, nan] | 2.1485893125744205e-105 | 6.4457679377232614e-105 | reject_H0 | empirically_supported | connectivity_regret_GEE |
| H0-SP0-C3 | confirmatory | 53.93666195973947 | [nan, nan] | 2.1595939592020332e-10 | 4.3191879184040664e-10 | reject_H0 | empirically_supported | connectivity_regret_GEE |
| H0-SP0-R1 | confirmatory | 0.00024893627020277216 | [0.00010518404178080267, 0.00024893627020277254] | 0.0 | 0.0 | reject_H0 | empirically_supported | B6:G-BIAS_G-ZERO |
| H0-SP0-R2 | confirmatory | 71.83310623514146 | [nan, nan] | 4.2555249537410205e-14 | 4.2555249537410205e-14 | reject_H0 | empirically_supported | generalization_method_logN_GEE |
| H0-SP0-R3 | confirmatory | nan | [nan, nan] | nan | nan | not_estimable | not_supported | missing_or_nonestimable |
| H0-SP0-R4 | confirmatory | nan | [nan, nan] | nan | nan | not_estimable | not_supported | missing_or_nonestimable |

## 16. Claims

- Theoretically guaranteed: oracle optimality, declared simplex contracts, finite QR termination and declared QRA scope.
- Empirically supported: only frozen confirmatory hypotheses at final sample size with Holm correction.
- Exploratory only: B0, smoke, B2 dynamic-fitness screening and nonconfirmatory closure ablations.
- Not supported: universal stability, universal graph convergence, theoretical PoA from Monte Carlo, or physical transfer.

## 17. Failure cases

Preserved failure/timeout rows found: 8498.

## 18. Deviations

# Protocol Deviations

No confirmatory deviations recorded.

| date_utc | commit_before | commit_after | reason | affected_blocks | affected_hypotheses | impact_on_confirmatory_validity | resolution |
|---|---|---|---|---|---|---|---|
| 2026-07-11T11:37:53.179670+00:00 | 72418e13f1bed1a6d37698e59bf0d07400dc8b10 | pending | B0 audit instrumentation added before freezing; no confirmatory seeds opened. | B0 | none | none | pending validation |

## CPU-only revision before confirmatory seed opening

- `date_utc`: 2026-07-11
- `commit_before`: 72418e13f1bed1a6d37698e59bf0d07400dc8b10
- `commit_after`: pending_worktree
- `reason`: The available host has no CUDA device and the corrected v1.1 budget of 26,000,000 joint environment transitions was measured at a minimum of 114.6 hours before optimization. Batched PPO reached 208.9 transitions/s with one PPO epoch and rollout batches of 512. To satisfy the user-imposed three-hour total wall-clock limit, v1.2 pre-registers 1,120,000 training transitions: DD-1 uses 10,000 per configuration, DD-2 uses 50,000 per seed/configuration, and each of the three final seeds uses exactly 200,000.
- `affected_blocks`: data-driven tuning, final IPPO/MAPPO training, freeze, B4-B7.
- `affected_hypotheses`: comparisons involving the data-driven champion in P, C and R.
- `impact_on_confirmatory_validity`: Confirmatory seeds remain unopened, so there is no post-hoc test selection. Statistical comparisons remain valid for the declared resource-constrained CPU protocol, but results are not evidence for equivalence to the original 26M-step learning budget.
- `resolution`: Freeze and report v1.2 as `resource_constrained_cpu_budget`; retain all three final seeds and exact final checkpoints; do not compare learning convergence claims across v1.1 and v1.2 as if budgets were equal.

## Pre-freeze environment-lock implementation correction

- `date_utc`: 2026-07-11
- `commit_before`: 72418e13f1bed1a6d37698e59bf0d07400dc8b10
- `commit_after`: pending_worktree
- `reason`: The first v1.2 freeze attempt stopped before artifact serialization because `environment_lock()` referenced `importlib.metadata` without importing it.
- `affected_blocks`: freeze only.
- `affected_hypotheses`: none.
- `impact_on_confirmatory_validity`: none; no frozen manifest or confirmatory seed-opening event was created.
- `resolution`: add the missing standard-library import, rerun tests and regenerate B0/dry-run so the implementation hash is current before freezing.

## Post-freeze orchestration correction without semantic changes

- `date_utc`: 2026-07-11
- `commit_before`: 72418e13f1bed1a6d37698e59bf0d07400dc8b10
- `commit_after`: frozen implementation unchanged
- `reason`: B5's thread-pool orchestration was limited by the Python GIL; a 96-row N=64 chunk required about 20 minutes and threatened the declared wall-clock envelope. The run was stopped after a valid 1056-row checkpoint and resumed with 12 isolated Python processes.
- `affected_blocks`: B5 execution orchestration; B6/B7 use the same process orchestration proactively.
- `affected_hypotheses`: none; task definitions, seeds, methods, worlds, numerical code, closures and metrics are unchanged.
- `impact_on_confirmatory_validity`: none. Existing rows were reused only after matching frozen `task_token`; pending rows were produced by the frozen `_execute_run_task`; final Parquet validation enforces the original primary keys, hashes and counts.
- `resolution`: record process count and preserve the original resume Parquet; report wall-clock as measured rather than as the preflight estimate.

## Precision diagnostic dtype correction

- `date_utc`: 2026-07-11
- `commit_before`: frozen implementation hash `8031084d625dbaa804bca06ad02273bddb49f480c8da0eca00688b34074f08e3`
- `commit_after`: frozen implementation unchanged
- `reason`: The precision-only extension decision aborted before producing extension rows because pandas preserved `final_success` as NumPy boolean and NumPy forbids boolean subtraction. Its first external retry also exposed that NumPy integer cell labels require conversion to Python scalars for JSON serialization.
- `affected_blocks`: precision diagnostics for B4, B5 and B7; no base run is affected.
- `affected_hypotheses`: none unless an extension is triggered; the decision rule and thresholds are unchanged.
- `impact_on_confirmatory_validity`: none. The external correction casts paired success indicators to float before subtraction, which is the declared success-rate difference, and uses the frozen bootstrap implementation unchanged.
- `resolution`: cast paired success to float, serialize cell labels through scalar `.item()`, rerun diagnostics from base Parquet, and extend only if the original width thresholds are exceeded; retain both failed tracebacks and this deviation record.

## Postprocessing nullable-value compatibility correction

- `date_utc`: 2026-07-11
- `commit_before`: frozen implementation hash `8031084d625dbaa804bca06ad02273bddb49f480c8da0eca00688b34074f08e3`
- `commit_after`: frozen implementation unchanged
- `reason`: Postprocessing aborted before analysis because `unit_id()` used Python boolean fallback on `pandas.NA`, whose truth value is intentionally undefined.
- `affected_blocks`: statistics, tables, figures, videos and final reporting only; no experimental run or metric computation is affected.
- `affected_hypotheses`: none; the shim only maps missing method/train-seed fields to the existing identifier semantics.
- `impact_on_confirmatory_validity`: none. The frozen run rows, planned contrasts, models, Holm procedure and rendering functions remain unchanged.
- `resolution`: apply an external audited compatibility shim that tests nullable scalars with `pandas.isna`, then delegate analysis and rendering to the frozen implementation.

## Post-hoc video encoder availability

- `date_utc`: 2026-07-11
- `commit_before`: frozen implementation unchanged
- `commit_after`: frozen implementation unchanged
- `reason`: All ten video render attempts reached the encoding stage but failed because no `ffmpeg` executable was available on `PATH`.
- `affected_blocks`: qualitative post-hoc videos only.
- `affected_hypotheses`: none.
- `impact_on_confirmatory_validity`: none; videos are generated from stored trajectories and are not statistical evidence.
- `resolution`: install `imageio-ffmpeg==0.6.0`, record the local encoder path/version, and rerun video rendering without reexecuting experimental worlds.

## Final acceptance accumulator initialization

- `date_utc`: 2026-07-11
- `commit_before`: frozen implementation hash `8031084d625dbaa804bca06ad02273bddb49f480c8da0eca00688b34074f08e3`
- `commit_after`: frozen implementation unchanged
- `reason`: The frozen final acceptance function references `block_integrity_ok` and `parquet_types_ok` before assigning initial values.
- `affected_blocks`: final acceptance manifest and report only.
- `affected_hypotheses`: none.
- `impact_on_confirmatory_validity`: none; each original acceptance predicate is preserved.
- `resolution`: run an external finalizer that initializes both conjunction accumulators to `true`, evaluates the unchanged block/schema/hash/artifact checks, and delegates report generation to the frozen writer.

## Seconds-only runtime schema validation

- `date_utc`: 2026-07-11
- `commit_before`: frozen implementation unchanged
- `commit_after`: frozen implementation unchanged
- `reason`: The generic acceptance schema still required legacy ambiguous fields `oracle_lookup_time` and `oracle_solve_time`, while the v1.1/v1.2 protocol explicitly migrated them to seconds-only `oracle_lookup_time_s` and `oracle_solve_time_s`.
- `affected_blocks`: schema validation for B2-B7 only.
- `affected_hypotheses`: none.
- `impact_on_confirmatory_validity`: none; all six Parquet files contain the seconds-only fields with numeric types and retain the measured values.
- `resolution`: validate the frozen v1.2 seconds-only schema by replacing the two legacy names with their `_s` counterparts; do not synthesize duplicate legacy columns.


## 19. Reproducibility

Frozen hashes, seed registry, environment lock, world/checkpoint/trajectory hashes are authoritative. Dry-run artifacts are exploratory and cannot open test seeds.

## 20. Final verdict

SP0 execution is complete. Regime-specific winners are reported from final Pareto/ranking tables; no universal winner is forced.
