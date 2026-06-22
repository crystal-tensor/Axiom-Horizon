# B1/B7 cone_01 OpenQASM 3 Multi-Input Replay Gate

Status: `cone01_openqasm3_multi_input_replay_pressure_passed_not_symbolic_certificate`

This artifact consumes T-B1-004bx and broadens the local OpenQASM 3 replay check from the benchmark default input to a deterministic sampled-input suite.

## Summary

- Source QASM: `results/b1_native_t_resource_optimizer/qasmbench_medium_exact/gcm_h6.qasm`
- OpenQASM 3 candidate: `results/B1_B7_cone01_openqasm3_candidate_export_gate/gcm_h6_line268_line1381_candidate_openqasm3.qasm`
- Project-local parser passed / errors: `True` / `0`
- Input cases: `8` total; `6` computational-basis and `2` deterministic product-state inputs
- Source / OpenQASM 3 CNOT count / delta: `795` / `789` / `6`
- Multi-input replay passed: `True`
- Failed input cases: `0`
- Min state fidelity / max infidelity: `0.9999999999999547` / `4.529709940470639e-14`
- Max global-phase-aligned amplitude delta: `1.392888964263601e-13`
- Max probability delta: `1.8214596497756474e-15`
- Accepted OpenQASM 3 multi-input replay / Qiskit loader / symbolic equivalence artifacts: `1` / `0` / `0`
- Accepted replay certificate / local-U3 pricing / occurrence / proxy-T reduction: `0` / `0` / `0` / `0`
- Validation errors: `0`

## Input Cases

| Case | Kind | Fidelity | Max probability delta | Passed |
|---|---|---:|---:|---|
| `zero` | `computational_basis` | `0.9999999999999551` | `5.551115123125783e-16` | `True` |
| `x_q0` | `computational_basis` | `0.9999999999999551` | `5.551115123125783e-16` | `True` |
| `x_q4` | `computational_basis` | `0.9999999999999547` | `4.996003610813204e-16` | `True` |
| `x_q14` | `computational_basis` | `0.9999999999999589` | `4.996003610813204e-16` | `True` |
| `x_q4_q14` | `computational_basis` | `0.9999999999999583` | `7.771561172376096e-16` | `True` |
| `x_q0_q4_q14` | `computational_basis` | `0.9999999999999583` | `7.771561172376096e-16` | `True` |
| `product_seed_17` | `deterministic_product_state` | `0.9999999999999667` | `8.370040771588094e-16` | `True` |
| `product_seed_29` | `deterministic_product_state` | `0.9999999999999594` | `1.8214596497756474e-15` | `True` |

## Claim Boundary

The project-local OpenQASM 3 parser can construct the candidate and match the optimized source across a deterministic sampled-input statevector replay pressure suite.

Unsupported claims:

- This is not a Qiskit OpenQASM 3 loader parse.
- This is not symbolic unitary equivalence or arbitrary-input equivalence.
- This is not an exhaustive input-space replay certificate.
- This does not price or eliminate local-U3 burden.
- This does not create B7 occurrence, proxy-T, or space-time-volume credit.

## Next Required Gate

Move from sampled local OpenQASM 3 replay to loader-backed replay, phase-consistent OpenQASM 3 replay, or symbolic/local-unitary evidence; then separately price or eliminate the remaining local-U3 burden before any B7 resource credit is accepted.
