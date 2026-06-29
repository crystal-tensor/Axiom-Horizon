# B1/B7 cone_01 OpenQASM 3 Qiskit-Loader Replay Gate

- Method: `b1_b7_cone01_openqasm3_qiskit_loader_replay_gate_v0`
- Status: `cone01_openqasm3_qiskit_loader_replay_passed_default_input_only`
- Model status: `qiskit_loader_openqasm3_replay_matches_source_default_input_without_b7_credit`
- Workload: `qasmbench_medium_exact/gcm_h6.qasm`
- Supported claim: The OpenQASM 3 candidate can be loaded by Qiskit's OpenQASM 3 loader with qiskit-qasm3-import installed, preserves the expected operation counts, and matches the optimized source on the default-input statevector after final measurements are removed.

## Inputs

- Parser-readiness gate: `results/B1_B7_cone01_openqasm3_parser_readiness_gate_v0.json`
- Local semantic replay gate: `results/B1_B7_cone01_openqasm3_local_semantic_replay_gate_v0.json`
- Patch witness packet gate: `results/B1_B7_cone01_openqasm3_patch_witness_packet_gate_v0.json`
- OpenQASM 3 candidate: `results/B1_B7_cone01_openqasm3_candidate_export_gate/gcm_h6_line268_line1381_candidate_openqasm3.qasm`

## Loader Evidence

- Qiskit / qiskit-qasm3-import / openqasm3 versions: 2.4.1 / 0.6.0 / 1.0.1
- Loader attempted / passed: True / True
- Qubits / clbits / depth: 19 / 1 / 1483
- Operation counts: {'cx': 789, 'rz': 601, 'u': 487, 'measure': 1}

## Replay Evidence

- State fidelity / infidelity: 0.9999999999999551 / 4.4853010194856324e-14
- Max amplitude / probability delta: 1.3908205762322243e-13 / 5.551115123125783e-16
- Measured q[4] marginal delta: 5.551115123125783e-16
- Accepted Qiskit-loader parse / replay artifacts: 1 / 1
- Accepted occurrence / proxy-T reduction / B7 claim: 0 / 0 / False

## Claim Boundary

- This is only default-input statevector replay, not arbitrary-input equivalence.
- This is not a symbolic exact full-circuit unitary proof.
- This does not price or eliminate the remaining line-1381 off-grid local-U3 parameters.
- This does not recover the dropped line-1378 overlap delta.
- This does not improve the B7 resource ledger.

## Validation

- Qiskit-loader default-input replay passed: True
- Validation errors: 0
