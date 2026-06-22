# B1/B7 cone_01 OpenQASM 3 Structural Roundtrip Gate

Status: `cone01_openqasm3_structural_roundtrip_matches_legacy_candidate`

This artifact consumes T-B1-004bv and compares the legacy OpenQASM 2 candidate against the OpenQASM 3 artifact after dialect normalization.

## Summary

- OpenQASM 2 candidate: `results/B1_B7_cone01_qasm2_candidate_rewrite_gate/gcm_h6_line268_line1381_candidate.qasm`
- OpenQASM 3 candidate: `results/B1_B7_cone01_openqasm3_candidate_export_gate/gcm_h6_line268_line1381_candidate_openqasm3.qasm`
- Normalized instruction counts, QASM2 / QASM3: `1878` / `1878`
- Normalized streams match / mismatch count / length delta: `True` / `0` / `0`
- Operation counts: `{'U': 487, 'rz': 601, 'cx': 789, 'measure': 1}`
- Normalized stream SHA256: `7cd50bea1f5a3c191c5735c0891d3f70f8c07a9cfca9d6e93724e6d49cb36343`
- First / last normalized instruction: `U(pi,-pi/8,-7*pi/8)|q[1]` / `measure|q[4]->c[0]`
- Accepted structural roundtrip artifacts: `1`
- Accepted Qiskit loader parse / replay / local-U3 pricing artifacts: `0` / `0` / `0`
- Accepted occurrence / proxy-T reduction: `0` / `0`
- Validation errors: `0`

## Claim Boundary

The legacy OpenQASM 2 candidate and OpenQASM 3 artifact normalize to the same 1,878-instruction stream with zero structural mismatches.

Unsupported claims:

- The structural roundtrip is not a Qiskit OpenQASM 3 loader parse.
- The structural roundtrip is not a full-circuit semantic replay proof.
- The structural roundtrip does not price or eliminate local-U3 burden.
- The structural roundtrip does not create B7 occurrence, proxy-T, or space-time-volume credit.

## Next Required Gate

Run the same artifact through a reproducible OpenQASM 3 loader or a full semantic replay path, then separately prove or price the remaining local-U3 burden before any B7 resource credit is accepted.
