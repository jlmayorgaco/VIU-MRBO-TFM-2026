# Devil's Advocate review

## Strongest counter-argument

The thesis may be read as a carefully engineered demonstration of its own ladder rather than evidence for distributed coalition control. Each scenario family is designed around a specific bottleneck, and each stage bundles algorithmic choices with extra information. A3 changes coalition membership and slot allocation; A4 adds union-based reserve, a waypoint and HOCBF; FULL adds messaging, memory and a global replacement selector. Consequently, the large effects show that the bundles behave differently on scenarios built to separate them, but do not isolate which internal mechanism caused the difference. The $+0.62$ FULL effect is especially vulnerable: the global candidate selector can explain recovery without any genuinely local network decision.

The paper survives this counter-argument only if its central claim is diagnostic rather than competitive. It can show that cardinality, capacity, wrench, dynamic reserve, safety and recovery are non-equivalent in the stated simulator. It cannot show end-to-end distributed recovery or industrial safety. The revised limitations and post-hoc claim audit now make that distinction, so this is a MAJOR framing constraint rather than a fatal flaw.

## Issue list

### CRITICAL

None after the locality correction and claim audit.

### MAJOR

| # | Dimension | Issue | Location |
|---|---|---|---|
| M1 | Core thesis | “Distributed” can be misread as end-to-end; A3 and FULL use global information. | Abstract, Sections 5--7 |
| M2 | Alternative explanation | FULL improvement can be explained by global replacement, not network resilience. | Section 6.1 |
| M3 | Logic chain | The stages are cumulative in requirements but not nested algorithms; A3 can remove a robot and degrade success. | Section 6.1, scarcity result |

### MINOR

| # | Dimension | Issue | Location |
|---|---|---|---|
| m1 | So what | The defense should foreground the A2--A3 counterexample rather than the number of campaigns. | Abstract and conclusion |
| m2 | Overgeneralization | Scenario frequencies are not prevalence estimates for warehouses. | Limitations |

## Ignored alternatives

1. Treat the global selector explicitly as a fleet-manager baseline and compare it later with a graph-local selector.
2. Jointly constrain wrench realization and HOCBF feasibility so the system abstains before entering an unsafe corridor.

## Unexamined premise

The ladder assumes that more detailed evidence should be accumulated in a fixed order. Real systems may need a coupled feasibility problem in which contact, dynamics and safety are solved jointly. The observed A3 degradation is evidence for that coupled view.

## Observations

The preservation of unfavorable outcomes is unusually strong and reduces confirmation-bias concerns. The post-hoc locality finding was not hidden, which materially improves trustworthiness.