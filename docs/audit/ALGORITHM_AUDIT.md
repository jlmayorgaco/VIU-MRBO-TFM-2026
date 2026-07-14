# Algorithm semantic audit

## Canonical taxonomy

The repository must separate **proposed method**, **ablation**, **classic baseline**, **learned comparator**, and **oracle/reference**. Current per-SP metadata often labels several unrelated variants “proposed”; this is a taxonomy bug. Only Wrench-Gated Pair-Aware Smith–QR is the canonical candidate. Other Smith, marginal, primal-dual, tensor, learned, and guarded variants are ablations or comparators until specifically promoted by a frozen protocol.

| Public name | Internal implementation | Nature | Information | Objective/constraints | Decoder/solver | Complexity/message note | Fidelity status |
|---|---|---|---|---|---|---|---|
| SP0 Hungarian | `sp0.methods.hungarian_assignment` | oracle/reference for SP0 assignment | global | min cost, max cardinality | SciPy Hungarian | polynomial centralized | exact for SP0 only |
| Greedy | generic and SP-specific greedy allocators | classic baseline | local/global varies | nearest or utility score | none | roughly O(NK); few/no messages | repository baseline |
| Auction/CBBA-like | `allocation.static_methods`, SP1/SP3/SP6 aliases | classic/SOTA-like baseline | local bids/proxy | deficit/score auction | none | implementation-specific | adaptation, not certified faithful CBBA |
| SP0 Smith | `sp0.methods._smith_vector_field` + `run_population_method` | ablation | declared architecture | continuous population payoff | RAW/ARG/REPAIR/QR1/QR2/QRA | O(iter·NK²) style; recorded messages | explicit repository dynamic |
| Generic SmithQR | `allocation.SmithQRAllocator` | legacy/cardinality ablation | local cost/capacity | greedy cardinality/capacity utility | implicit integer assignment | O(NK) | not equivalent to SP0 Smith–QR |
| SP1 Smith cardinality | wrapper around generic SmithQR | ablation | local scores | integer quorum/capacity proxy | allocator output only | O(NK) | not a continuous Smith + QR pipeline |
| Replicator/BNN/logit | SP0 dynamic IDs and SP1 utility-rule names | baselines/ablations | varies | population or proxy utility | optional local repair | implementation-specific | SP1 names are approximations, not the SP0 dynamics |
| Primal-dual | SP1 recruitment, SP6 recovery | ablation | local/global varies | deficit/capacity/wrench proxy | optional repair | iterative/heuristic | repository formulation |
| SP3 Smith wrench marginal | `SmithWrenchMarginalAllocator` | ablation | local marginal wrench score | residual reduction | optional guarded repair | bounded local search | repository formulation |
| Pair-aware guarded Smith | `smith_wrench_pairs_guarded` | canonical candidate component | local pair complementarity + guard | score then pair insert/drop under wrench feasibility | guarded local repair, no external solver | pair neighborhoods increase combinatorics | implemented allocation layer; end-to-end claim unvalidated |
| Residual-support wrench market | SP3 support-dual variants | comparator/ablation | current residual direction | residual support score | optional guard | bounded heuristic | repository formulation |
| SP1 coalition MILP | `CentralizedCoalitionOracleAllocator` | oracle/reference | global | reward − travel − overassignment; robot exclusivity, quorum, activation, capacity, idle | SciPy MILP/HiGHS | exponential worst case; exact when optimal | exact for declared SP1 model after current fix |
| Hungarian expanded | SP1 method | imperfect baseline | global | slot distance assignment | Hungarian | polynomial | not a coalition oracle |
| SP0 MAPPO/IPPO-GNN | `sp0.data_driven` | learned comparator | local actor; centralized MAPPO critic in training | PPO reward, then deterministic repair | argmax iteration + `repair_assignment` | GNN inference + closure | real checkpoints; behavioral learning claim blocked |
| SP1 MAPPO recruitment | `sp1.mappo` | learned comparator/ablation | decentralized pair actor; centralized critic in training | PPO/BC then quorum decoder | Hungarian-like quorum decoder | checkpoint inference + decoder | implemented; decoder dependency requires new audit |
| CBF/HOCBF | `control.explicit_law`, SP5/SP6/SP9 proxies | safety/control component | state/obstacle data | half-space safety projection | closed-form sequential projection | per-constraint projection | reduced-order simulation, not universal CBF guarantee |
| Recovery | `sp6.methods` | validation layer | method-specific | completion/safety/resource score after events | guarded replanning | temporal simulation | not the same algorithm as SP3 allocation |
| Hierarchical/mean-field | warehouse/SP8 policies | scalability comparators | aggregate/hierarchical | mesoscopic proxies | none | scalable approximation | exploratory, not rigorous mean-field limit |

## “Smith-QR” is not semantically stable

- **SP0:** a continuous simplex population dynamic followed by one of several explicitly named closures.
- **SP1:** `smith_cardinality` currently instantiates a generic integer utility allocator; it does not expose the SP0 continuous state or an independently persisted QR stage.
- **SP3:** `smith_qr_capacity`, `smith_qr_wrench`, marginal, and pair-aware guarded variants operate over role/wrench problem structures with different repair semantics.
- **SP5:** method names are mapped to SP3 allocation labels and combined with transport controllers.
- **SP6:** `smith_qr_recovery` is a temporal recovery policy/configuration, not SP0’s assignment dynamic.
- **Warehouse/SP8:** “smith_qr” names include belief, stickiness, clearing guards, and quorum rescue.

Required naming pattern: `SP<id>_<signal>_<dynamic>_<closure>_<guard>_<information>`. Example: `SP3_pair_wrench_Smith_pairQR_wrenchGuard_local`.

## Information and oracle leakage

SP0 public/oracle views are separated and tested. SP1 runners compute the oracle outside method execution and pass ordinary `DecisionContext` to deployed methods; however, imitation learning explicitly consumes oracle labels and must be labeled oracle-trained. Per-method metadata must be enforced at runtime, not trusted as descriptive text. A method called distributed must fail validation if it reads global state not declared by its information contract.

## Promotion decision

No implementation is currently promotable as the fully validated canonical end-to-end method. `smith_wrench_pairs_guarded` is the correct candidate component. Promotion requires the integrated cumulative ablation, RAW/closure/guard attribution, paired worlds, finite statistics, OOD tests, and nontrivial precision–coverage.
