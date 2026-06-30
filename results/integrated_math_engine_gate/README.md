# Integrated mathematical engine gate G4

This gate validates algebraic links between contour geometry, wrench
signatures, economic phase assignment, congestion tolls, battery penalties,
and port-Hamiltonian energy balance.

| Check | Observed | Threshold | Pass |
|---|---:|---:|---|
| circle_radial_torque_null | 0 | 1e-08 | True |
| square_superellipse_torque_nonzero | 0.524023 | 0.25 | True |
| rectangle_superellipse_torque_nonzero | 1.08558 | 0.65 | True |
| market_force_vs_torque_phase_separation | 1.01665 | 0.35 | True |
| rectangle_congestion_toll_phase_shift | 3.14159 | 0.2 | True |
| square_congestion_toll_phase_shift | 1.5708 | 0.2 | True |
| battery_market_penalty_orders_payoff | 0.75 | 0.5 | True |
| port_hamiltonian_power_balance | 2.22045e-16 | 1e-09 | True |
| port_hamiltonian_zero_input_passivity | 0 | 1e-09 | True |

Key selections:
- Rectangle force phase: `0` rad
- Rectangle torque phase: `1.01665` rad
- Rectangle congested torque phase: `4.15825` rad
- High-battery payoff: `1.03558`
- Low-battery payoff: `0.285584`
