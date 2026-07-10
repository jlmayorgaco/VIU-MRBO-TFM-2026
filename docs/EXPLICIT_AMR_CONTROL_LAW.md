# Explicit AMR Control Law Integration

This note records how the July 2026 closed-form control-law PDFs were incorporated into the executable experiments. The project vocabulary is AMR throughout.

## Control Law

The implemented law is a 9-block local controller:

1. Hand point kinematics:
   `h_i = p_i + a_i e(theta_i)`, `h_dot_i = v_i e(theta_i) + a_i omega_i e_perp(theta_i)`.
2. Battery-scaled game weight:
   `eta_i = eta_nom_i max(E_i, E_min) / E0_i`.
3. Dynamic average consensus for the two scalars needed by the closed-form allocation:
   `H = sum eta_i`, `S = sum eta_i ||r_i||^2`.
4. Rigid contact reconstruction:
   `phi_L = theta_i - theta_grasp_i`, `p_L = h_i - R(phi_L) r_i`.
5. Required wrench with critically damped PD and feedforward:
   `a_cmd = pdd_ref + 2 sqrt(k_p) e_dot + k_p e`,
   `w_req = [M a_cmd, J alpha_cmd]`.
6. Closed-form vGNE force share:
   `f_i* = eta_i/H w_p + eta_i/S perp(R r_i) tau`.
7. Rigid hand-point impedance:
   `hdd_nom = hdd_ref + 2 sqrt(k_h) h_error_dot + k_h h_error + f_i*/m_i`.
8. Closed-form HOCBF safety projection over half-spaces:
   `a_k^T w >= b_k`, with sequential Euclidean projections.
9. Exact unicycle inverse dynamics and uniform saturation:
   `(F_i, tau_i) = sat(Gamma_i^{-1}(w_safe - g_i))`.

## Code Map

| Component | Location |
|---|---|
| Common formulas | `src/viu_mrob_tfm/control/explicit_law.py` |
| Public exports | `src/viu_mrob_tfm/control/__init__.py` |
| SP4 explicit motion method | `explicit_vgne_cbf_motion` in `src/viu_mrob_tfm/sp4/methods.py` |
| SP5 explicit transport methods | `ours_explicit_vgne_cbf_push`, `ours_explicit_vgne_cbf_cargo` in `src/viu_mrob_tfm/sp5/methods.py` |
| SP6 explicit recovery control | `tensor_flow_recovery`, `ours_guarded_wrench_market_recovery` and `reference_resilient_oracle` use explicit required-wrench generation |
| Unit tests | `tests/test_explicit_amr_control_law.py` |

## Experiment Supplements

These runs do not replace the high-power canonical SP5/SP6 evidence. They isolate the explicit control law.

| SP | Config | Results | Runs | Audit |
|---|---|---|---:|---|
| SP4 | `configs/experiments/sp4/SP4_MC_explicit_control_law.yaml` | `results/sp4/SP4_MC_explicit_control_law/` | 432 | 0 failed checks |
| SP5 | `configs/experiments/sp5/SP5_MC_explicit_control_law.yaml` | `results/sp5/SP5_MC_explicit_control_law/` | 432 | 0 failed checks |
| SP6 | `configs/experiments/sp6/SP6_MC_explicit_control_law.yaml` | `results/sp6/SP6_MC_explicit_control_law/` | 360 | 0 failed checks |

## Result Reading

- SP4: the explicit hand-point/CBF method reaches all targets in the supplement (`arrival_success_rate=1.0`) but does not reduce collisions versus direct tracking and does not reduce reference gap versus CBF. This is a useful negative result: the closed-form law needs SP4-specific safety tuning before it can be sold as a superior arrival controller.
- SP5: `ours_explicit_vgne_cbf_cargo` reaches target in 100% of the 48 paired supplement worlds and ranks third overall, behind centralized reference and SOTA VO cargo. It improves target reach versus classic APF and reduces final position error versus SOTA VO cargo under the paired tests. `ours_explicit_vgne_cbf_push` does not reduce wrench residual versus `ours_tensor_game_push`; that hypothesis is explicitly not confirmed.
- SP6: the explicit required-wrench law improves the physical interpretation of recovery control, but the supplement does not prove statistically significant improvement in lost-load rate versus classic greedy or completion versus Smith. It does show family-level differences in score.

Manual method-specific MP4s were added because the automatic selector often chooses the reference method:

- `results/sp4/SP4_MC_explicit_control_law/videos/sp4_crossing_traffic_explicit-vgne-cbf-motion_manual_seed5400.mp4`
- `results/sp5/SP5_MC_explicit_control_law/videos/sp5_overactuated_push_drag_explicit-vgne-cbf-cargo_manual_seed6655.mp4`
- `results/sp6/SP6_MC_explicit_control_law/videos/sp6_robot_dropout_mid_task_ours-guarded-explicit-control_manual_seed7656.mp4`

## Claim Boundary

The law is an executable reduced-order controller for simulation. It is not a hardware validation, full frictional contact model, certified kinodynamic planner, or proof that the proposed method dominates every baseline. Its role in the thesis is to make SP4-SP6 more physically grounded and to provide a clear doctoral bridge toward embedded implementation, CBF certificates and real-contact validation.
