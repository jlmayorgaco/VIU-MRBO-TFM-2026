# TFM literature-review scope contract

## Current research problem

The TFM concerns local/distributed coordination of multiple autonomous mobile robots (AMRs) for cooperative transport of heterogeneous loads in industrial environments. The literature review must not collapse the problem into a single “multi-robot task allocation” category. It must preserve the interfaces between logical coalition decision, physical feasibility, execution, recovery, and network authority.

## Layers that must be coded separately

1. **Recruit / membership** — which robots join which task/load; variable team size; heterogeneity; atomic closure.
2. **Certify** — capacity, geometry, contact, wrench/force feasibility, actuator limits.
3. **Dock / form** — approach, contact pose, rigid/support configuration, role/contact assignment.
4. **Transport** — shared-load motion, formation/pose control, distributed execution.
5. **Safety / traffic** — collision avoidance, CBF/VO/MAPF/reservations and inter-coalition conflicts.
6. **Recover / replace** — failures, re-recruitment, member substitution, reconfiguration during an active mission.
7. **Communication / authority** — local vs global information, server/leader/master, centralized closure, time-varying network, delay/loss.

## Physical modalities that must not be merged

- Supported cargo: payload supported by multiple mobile bases.
- Rigid attachment: fixed contact/connector or rigid formation.
- Pushing/caging: unilateral contact / non-prehensile manipulation.
- Grasping/arms: grasp matrix / force closure using manipulators.

## Candidate novelty conjunction to RED-TEAM

The legacy review did **not** identify, within the corpus it had reviewed, a single architecture integrating all of:

- local recruitment from a larger fleet,
- heterogeneous variable-size coalition,
- physical certification of shared-load feasibility,
- online replacement of a member during transport,
- coalition decision and execution without a permanent global authority.

This is not a fact to preserve. It is the strongest counterexample-search target for the new review.

## Known prior-art warnings from the legacy review

- Replacement during payload transport already exists in prior work; broad “first replacement” claims are invalid.
- Distributed/decentralized cooperative transport already exists; broad “first distributed transport” claims are invalid.
- Logical coalition formation and physical shared-load transport are mature subliteratures separately.
- Population/GNE methods may output continuous mass; integer/atomic closure is part of the method and must be audited.
- “1000 robots simulated” is not hardware scale. Code `N_sim`, `N_hw`, robots/team, and concurrent tasks separately.

## Review objective

Build an adversarial evidence map that can say exactly which conjunctions are already covered, partially covered, or not found after a reproducible search. Avoid novelty-by-absence unless the search and screening trail supports it.
