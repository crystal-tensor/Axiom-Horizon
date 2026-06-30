# B7 B2 Calibrated Dependency Credit Gate v0.1

Status: **b2_calibrated_dependency_credit_rejected_missing_hardware_evidence**

## Summary

- Method: b7_b2_calibrated_dependency_credit_gate_v0
- Model status: b7_dependency_bridge_structural_only_b2_claim_credit_blocked
- Source B7 bridge: b1_b2_dependency_schedule_bridge_v0 / dependency_schedule_bridge_not_physical_layout
- Source B7 comparisons: 6
- Structural min / mean STV reduction: 1.1948051948051948 / 1.353572610789181
- Selected B2 p / target / distance / STV: 0.001 / 0.01 / 3 / 78
- Selected B2 Wilson 95 high: 0.0012788956648046956
- B2 contract status: calibrated_evidence_contract_open_missing_hardware_data
- B2 contract failed ids: K4, K5, K6
- Calibrated flag data used: False
- Real hardware trace used: False
- Holdout baseline / injected / delta: 16 / 16 / 0
- Requirements passed / failed: 4 / 4
- Blocking failed ids: D4, D5, D6, D8
- B2 calibrated dependency credit allowed: False
- B7 claim-credit STV reduction: None
- Validation errors: []

## Requirements

| gate | passed | blocks credit | label | acceptance rule |
|---|---:|---:|---|---|
| D1 | True | False | B7 dependency bridge is present and structural | Use only the structural B1/B2 bridge as the dependency source. |
| D2 | True | False | Selected B2 target-volume row is replayable in the B2 baseline table | The B7 bridge must point to an explicit B2 target-volume row. |
| D3 | True | False | B2 calibrated-evidence contract is valid | Consume the validated B2 calibrated-evidence contract. |
| D4 | False | True | Calibrated leakage/flag data are present | Submit calibrated leakage/flag rows before B2 credit enters B7. |
| D5 | False | True | Real or independently calibrated hardware traces are replayed | Replay real or independently calibrated traces through the same B2 decoder path. |
| D6 | False | True | Strict holdout improvement is shown under the calibrated injection | Show fewer holdout logical failures while preserving non-regression. |
| D7 | True | False | Forbidden production, threshold, hardware, and advantage claims remain absent | Keep B2 claim boundaries strict while the dependency gate is blocked. |
| D8 | False | True | B7 may count B2 calibrated-dependency credit | Allow B2-derived B7 credit only after D4-D7 all pass. |

## Claim Boundary

- b7_dependency_gate_built: True
- b7_structural_planning_bridge_supported: True
- b2_calibrated_credit_allowed: False
- b7_resource_reduction_claimed_from_b2_calibration: False
- physical_layout_claimed: False
- low_overhead_qec_claimed: False
- threshold_claimed: False
- hardware_result_claimed: False
- quantum_advantage_claimed: False
- what_is_supported: The existing B7 B1/B2 dependency bridge is preserved as a structural planning input, and B7 now has an explicit claim-credit gate tied to B2 calibrated flag data, real hardware trace replay, and holdout improvement.
- what_is_not_supported: No B2-derived calibrated resource credit, physical layout result, low-overhead QEC claim, threshold claim, hardware result, or quantum advantage claim is supported until D4-D6 are closed.

## Next Gate

B7 can keep using the B1/B2 bridge as a planning input, but it must
not count B2-derived calibrated resource credit until B2 closes D4-D6:
calibrated leakage/flag rows, real or independently calibrated trace
replay, and strict holdout improvement without regression.
