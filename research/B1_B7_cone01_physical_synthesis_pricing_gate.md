# B1/B7 cone_01 Physical Synthesis Pricing Gate

- Gate: T-B1-004cs / T-B7-011
- Method: `b1_b7_cone01_physical_synthesis_pricing_gate_v0`
- Status: `cone01_physical_synthesis_pricing_rejects_line1381_b7_credit`
- Model status: `precision_aware_synthesis_cost_exceeds_selected_cnot_delta_credit`
- Workload: `qasmbench_medium_exact/gcm_h6.qasm`

## Inputs

- Route triage: `results/B1_B7_cone01_route_triage_decision_gate_v0.json`
- Local-U3 pricing boundary: `results/B1_B7_cone01_line1381_local_u3_pricing_gate_v0.json`
- All-grid endpoint pressure: `results/B1_B7_cone01_line1381_leave_five_out_parameter_gate_v0.json`

## Result

- Line-1381 off-grid local-U3 parameters: `5`
- Aggregate synthesis error budget: `1e-08`
- Per-parameter error budget: `2e-09`
- Single-parameter T-count bound: `97`
- Total physical synthesis T-count bound: `485`
- Selected 6-CNOT delta proxy credit: `120`
- Cost minus credit: `365`
- Physical synthesis pricing accepted: `False`
- Accepted occurrence / proxy-T reduction: `0` / `0`

## Claim Boundary

- This is a conservative pricing guardrail, not a synthesized replacement circuit.
- It rejects B7 credit for the current line-1381 route under the physical synthesis pricing model.
- It leaves full-circuit symbolic equivalence, line-1378 recovery, and alternate scaffolds open.
