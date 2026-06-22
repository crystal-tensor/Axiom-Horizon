# B1/B7 cone_01 QASM2 Candidate Rewrite Gate

## Summary

- Method: `b1_b7_cone01_qasm2_candidate_rewrite_gate_v0`
- Status: `cone01_qasm2_candidate_rewrite_emitted_not_replay_certified`
- Candidate QASM: `results/B1_B7_cone01_qasm2_candidate_rewrite_gate/gcm_h6_line268_line1381_candidate.qasm`
- Source / candidate dialect: `OPENQASM 2.0` / `OPENQASM 2.0`
- Selected lines / dropped overlap lines: `[268, 1381]` / `[1378]`
- Source / candidate CNOT count: `795` / `789`
- Candidate CNOT delta: `6`
- QASM2 bridge patch count: `2`
- Accepted full-circuit patch / replay / occurrence / proxy-T reduction: `0` / `0` / `0` / `0`
- Validation errors: `0`

## Replacement Rows

| Line | Source window | Source lines | Replacement lines | Source CNOT | Replacement CNOT | Candidate delta |
|---:|---|---:|---:|---:|---:|---:|
| 268 | 256-267 | 12 | 9 | 5 | 2 | 3 |
| 1381 | 1369-1379 | 11 | 9 | 5 | 2 | 3 |

## Claim Boundary

A QASM2 candidate rewrite file now exists for the selected non-overlap bounded patch subset at line 268 and line 1381.

Unsupported claims:

- The candidate rewrite is not yet a full-circuit replay certificate.
- The candidate rewrite does not recover the dropped line-1378 overlap delta.
- The candidate rewrite does not yet accept a B7 occurrence or proxy-T reduction.
- The remaining line-1381 off-grid local-U3 parameters are not priced or eliminated.

## Interpretation

This moves the B1/B7 branch from standalone bounded snippets into a replay-consumable QASM2 candidate file. The candidate has the expected 6-CNOT structural delta from line 268 plus line 1381, but it remains unaccepted until whole-circuit replay and B7 resource pricing pass.
