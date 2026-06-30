# Neural MARL CTDE training

- Baseline: shared residual neural actor trained from full multi-robot episode returns.
- Execution: decentralized; each robot scores visible loads from local features.
- Optimizer: centralized cross-entropy search, not labelled as PPO/MAPPO.
- Initial objective: 0.4065.
- Best objective: 0.4585.
- Best capture: 0.4898.
- Runtime: 346.6 s.
