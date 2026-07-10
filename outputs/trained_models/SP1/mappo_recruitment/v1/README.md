# SP1_mappo_recruitment_v1

MAPPO-style CTDE checkpoint for SP1 recruitment.
- Actor: shared decentralized AMR-load pair scorer.
- Critic: centralized state-value network used only during training.
- PPO rollout action mode: `sampled_policy`
- Execution quorum decoder: `True`
- Actor parameters: `4674`
- Training parameters actor+critic: `9411`
- Training episodes: `768`
- Validation runs: `200`
- Validation demand satisfaction: `0.9083`
- Test runs: `200`
- Test demand satisfaction: `0.8901`
