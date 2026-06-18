# B10-T1 B3/B5 Denominator Boundary Comparison v0.1

- Status: b3_b5_denominator_boundary_comparison_not_bqp_separation
- Method: b10_t1_b3_b5_denominator_boundary_comparison_v0
- Source target: B10-T1
- Routes compared: 4
- B3 denominator wins: 0
- B3 max optimizer-loop shots lower bound: 475043013690000
- B5 non-oracle rows beating oracle boundary field: 4
- B5 seeded MPS rows beating non-oracle embedding: 6
- B5 variational MPS/ALS rows beating seeded MPS pressure: 0
- Validation errors: []

## Route Cards

| route | status | primary metric | value | next gate |
|---|---|---|---:|---|
| B3_one_parameter_ucc_adapt_qwc | negative_boundary | selected_ci_larger_basis_denominator_beaten_count | 0 | Only reopen B3 as a positive route with multi-parameter covariance or stronger-than-QWC measurement. |
| B5_small_cluster_embedding | classical_denominator_improved_not_quantum_win | non_oracle_rows_beating_oracle_boundary_field | 4 | Compare a real quantum response kernel against the non-oracle denominator after full costs. |
| B5_exact_state_seeded_mps_pressure | strong_classical_pressure_reference_not_deployable_dmrg | mps_rows_beating_non_oracle_embedding | 6 | Replace seeded pressure with mature variational DMRG/MPS or an honestly costed quantum kernel. |
| B5_variational_mps_als_prototype | prototype_not_production_dmrg_not_quantum_win | variational_mps_rows_beating_seeded_mps_pressure_reference | 0 | Upgrade to canonical-environment production DMRG/MPS before making a B5 positive claim. |

## Claim Boundary

- bqp_separation_claimed: False
- quantum_advantage_claimed: False
- b3_reaction_dynamics_solution_claimed: False
- b5_strong_correlation_solution_claimed: False
- production_dmrg_claimed: False
- what_is_supported: The current B3 one-parameter UCC/ADAPT route is negative-boundary evidence under selected-CI/FCI and optimizer-loop pressure; B5 has strong classical denominator pressure but no production DMRG or quantum response-kernel win.
- what_is_not_supported: This comparison is not a BQP/classical separation, not a dequantization theorem, not a quantum advantage result, and not a solution of B3 or B5.

## Next Required Artifacts

- T-B3-012 multi-parameter chemistry rescue or stronger-than-QWC measurement
- T-B5-003 production DMRG/MPS response reference
- costed B5 quantum response kernel compared against the D5 table
- B10-T1 dequantization/sampling-access theorem note if both B3 and B5 stay negative
