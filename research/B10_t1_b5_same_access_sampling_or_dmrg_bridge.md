# B10-T1 B5 Same-Access Sampling-or-DMRG Bridge v0.1

- Status: b5_same_access_sampling_oracle_not_constructed_dmrg_required
- Method: b10_t1_b5_same_access_sampling_or_dmrg_bridge_v0
- Source access contract: b10_t1_asymptotic_access_contract_v0
- Denominator ladder rows: 4
- Sampling requirements: 5
- Blocking sampling requirements: 5
- Sampling oracle constructed: False
- Production DMRG available: False
- Same-access positive route ready: False
- Validation errors: []

## Denominator Ladder

| id | access mode | status | mean error | max error | resource proxy | boundary |
|---|---|---|---:|---:|---:|---|
| D1_explicit_d5_cg_response | explicit | same_input_denominator_instantiated | n/a | 9.78806e-09 | 1014300 | Exact small D5 denominator, not a scalable response solution. |
| D2_non_oracle_embedding | explicit_predeclared_classical_denominator | non_oracle_denominator_instantiated | 0.0509835 | 0.123081 | 36 | Predeclared embedding denominator, not quantum response. |
| D3_exact_state_seeded_mps_pressure | mps_pressure_reference_not_deployable | strong_pressure_reference_not_production_dmrg | 0.000441626 | 0.0016954 | 16 | Exact-state seeded MPS pressure, not variational DMRG. |
| D4_variational_mps_als_prototype | variational_mps_prototype | nonproduction_dmrg_prototype | 0.0180555 | 0.039072 | 4 | One-site MPS/ALS prototype, not production DMRG. |

## Sampling Oracle Requirements

### S1_response_observable_sampler

- Requirement: Construct samples whose expectation estimates the same density-response observable and eta/tolerance as the D5 table.
- Current status: missing
- Blocks sampling bridge: True

### S2_preparation_or_mixing_cost

- Requirement: Charge preparation, thermalization, tensor sampling, or quantum state-preparation cost under the same input model.
- Current status: missing
- Blocks sampling bridge: True

### S3_variance_and_confidence_certificate

- Requirement: Provide variance, confidence, and failure-probability accounting for the response estimator.
- Current status: missing
- Blocks sampling bridge: True

### S4_same_access_classical_denominator

- Requirement: Compare against explicit, embedding, MPS/DMRG, or sampling-access classical denominators receiving no weaker access.
- Current status: partially_satisfied_by_finite_denominators
- Blocks sampling bridge: True

### S5_positive_kernel_after_full_costs

- Requirement: Show a candidate quantum or sampling response kernel beats the best same-access denominator after full costs.
- Current status: refuted_for_current_portfolio_evidence
- Blocks sampling bridge: True

## Bridge Decisions

### explicit

- Decision: classical_denominator_available
- Reason: D5 CG response and non-oracle embedding denominators are explicit-input artifacts.

### sampling_or_query_access

- Decision: not_constructed
- Reason: No sampler, variance certificate, or preparation/mixing cost exists for the B5 response observable.

### mps_dmrg_denominator

- Decision: production_dmrg_required_next
- Reason: Exact-state-seeded MPS is strong pressure but not deployable; variational MPS/ALS is nonproduction and loses to seeded pressure.

### quantum_response_kernel

- Decision: not_positive_ready
- Reason: No state-preparation, measurement, optimizer-loop, or response-kernel costed comparison beats the same-access denominator ladder.

## Claim Boundary

- sampling_oracle_constructed: False
- production_dmrg_available: False
- same_access_positive_route_ready: False
- general_dequantization_theorem_proved: False
- sampling_access_theorem_proved: False
- bqp_separation_claimed: False
- quantum_advantage_claimed: False
- what_is_supported: For the current B5 Hubbard response portfolio, explicit denominators exist and exact-state-seeded MPS is a strong pressure reference. However, no comparable sampling/query oracle is constructed and the available variational MPS/ALS reference is not production DMRG.
- what_is_not_supported: This is not a production DMRG result, not a same-access sampling theorem, not a quantum response win, not a dequantization theorem, and not a BQP separation.
