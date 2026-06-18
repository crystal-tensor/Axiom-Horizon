# B10-T1 Missing-Assumption Theorem Note v0.1

- Status: missing_assumption_note_not_dequantization_theorem
- Method: b10_t1_missing_assumption_note_v0
- Source comparison: b10_t1_b3_b5_denominator_boundary_comparison_v0
- Theorem skeletons: 2
- Missing assumptions: 5
- Proof obligations: 5
- Dequantization theorem proved: False
- BQP separation claimed: False
- Validation errors: []

## Theorem Skeletons

### T1_finite_boundary_no_advantage_claim

- Type: finite_negative_boundary
- Status: supported_as_claim_policy_not_complexity_theorem
- Statement: Under the currently audited finite B3/B5 D5 evidence, no B3 reaction-dynamics, B5 strong-correlation, quantum-advantage, or BQP-separation claim is supported.
- Depends on: A3_state_preparation_and_block_encoding_cost, A4_strong_classical_denominator

### T2_sampling_access_dequantization_candidate

- Type: candidate_theorem_not_proved
- Status: blocked_by_missing_A1_A2_A5
- Statement: If the B3/B5 observable family admits sampling/query access with comparable state-preparation and observable access, then quantum speedup claims must be compared against quantum-inspired or tensor/embedding classical denominators.
- Depends on: A1_asymptotic_family, A2_access_model_equivalence, A5_sampling_access_or_dequantization_bridge

## Missing Assumptions

### A1_asymptotic_family

- Status: missing
- Statement: The current B3/B5 evidence is a finite D5 table, not an asymptotic family with declared scaling of Hamiltonian construction, observable count, error, and condition parameters.
- Why needed: A theorem needs a family parameter and scaling law; finite denominator pressure is not a theorem.
- Current evidence: B10 D5 B5 instances = 9; B10 D5 B3 FCI instances = 4.

### A2_access_model_equivalence

- Status: partially_specified_not_proved
- Statement: Classical and quantum algorithms must receive equivalent explicit, sparse, oracle, or sampling/query access.
- Why needed: A dequantization or separation note collapses if one side receives stronger access.
- Current evidence: B10-T1 source-backed boundaries distinguish explicit I/O, oracle, and sampling-access regimes.

### A3_state_preparation_and_block_encoding_cost

- Status: missing_for_positive_quantum_route
- Statement: Any candidate quantum response kernel must charge state preparation, block encoding, measurement, and optimizer-loop costs.
- Why needed: B3 loses after optimizer-loop accounting; B5 has no honestly costed quantum response kernel yet.
- Current evidence: B3 max optimizer-loop shots lower bound is 475043013690000; B5 positive-claim-ready is false.

### A4_strong_classical_denominator

- Status: partially_satisfied_for_finite_instances
- Statement: The theorem note must compare against selected-CI/FCI, DMRG/MPS, embedding, or sampling-access baselines appropriate to each regime.
- Why needed: The current evidence is denominator pressure, not a universal lower bound.
- Current evidence: B3 selected-CI larger-basis denominator wins = 0; B5 variational MPS/ALS rows beating seeded pressure = 0.

### A5_sampling_access_or_dequantization_bridge

- Status: missing
- Statement: To become a dequantization theorem, the note must state whether B3/B5 observables admit sampling/query access or another classical simulation contract comparable to the quantum input model.
- Why needed: Without an access bridge, the result is only a negative boundary and not a dequantization theorem.
- Current evidence: No B3/B5 sampling-access theorem or oracle-equivalence lemma exists in the portfolio.

## Proof Obligations

- Define an asymptotic B3/B5 observable family rather than a finite table.
- Specify explicit, oracle, and sampling/query access contracts for both quantum and classical algorithms.
- Show whether B3/B5 state-preparation and observable access can be built without hiding linear or worse costs.
- State the best classical denominator family under the same access contract.
- Prove or refute that the quantum route improves the denominator after measurement and optimizer-loop costs.

## Claim Boundary

- dequantization_theorem_proved: False
- sampling_access_theorem_proved: False
- bqp_separation_claimed: False
- quantum_advantage_claimed: False
- what_is_supported: The current finite B3/B5 denominator evidence is strong enough to reject positive B3/B5/BQP claims under the audited route cards, and to define missing assumptions for a future theorem note.
- what_is_not_supported: This is not a dequantization theorem, not a sampling-access theorem, not a BQP separation, and not a quantum advantage claim.
