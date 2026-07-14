# SP5 status

Canonical campaign: `SP5_PAYLOAD_TRANSPORT_CONFIRMATORY_v2`.

- Status: complete; semantic/theory audit PASS.
- Execution: CPU only, no GPU and no CoppeliaSim.
- Design: 108 paired worlds, 8 methods, 864 runs.
- Factors: 6 scenarios, `N in {4,8,12}`, 6 confirmatory seeds.
- Lifecycle: pilot PASS, immutable freeze, then confirmatory seed-opening event.
- Plant: reduced-order planar rigid payload with fixed post-SP4 contacts,
  bounded planar contact forces and Euler--Lagrange integration.
- Semantics: RAW, SAFE and EXEC are distinct; only EXEC moves the plant; no
  post-integration pose repair; collisions and timeouts remain in the denominator.
- Outcomes: Local CBF had 0.593 safe success and zero collisions; the
  velocity-obstacle proxy had 0.657 safe success with 0.343 collisions;
  Hamiltonian+CBF had 0.426 safe success and zero collisions versus 0.167 safe
  success and 0.833 collisions for Hamiltonian RAW.
- Confirmatory decisions after Holm: H5.1, H5.2 and H5.5 supported; H5.3 and
  H5.4 not supported.

The historical 20,040-run package remains archived as non-canonical context
because post-integration geometric projection was part of its simulator.
