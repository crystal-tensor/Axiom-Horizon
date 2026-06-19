# B1/B7 Cone 01 Invariant-Flat Residual Gate

Status: `cone01_invariant_flat_residual_obligation_not_rewrite_certificate`

This artifact isolates the `cone_01` windows that were not blocked by the local-equivalence invariant diagnostic. It is a residual work packet, not a rewrite certificate and not a B7 resource claim.

## Summary

- Candidate windows: `35`
- Local-equivalence sensitive windows: `24`
- Invariant-flat windows: `11`
- Distinct flat theta groups: `3`
- Distinct normalized flat patterns: `3`
- All flat windows share one partner: `True`
- B7 required occurrence removals: `30`
- Max occurrence removal if all flat windows are solved: `11`
- Max proxy-T reduction if all flat windows are solved: `220`
- Missing occurrences after all flat windows are solved: `19`
- Missing proxy-T after all flat windows are solved: `380`

## Pattern Groups

| Pattern | Occurrences | Theta | Lines | Target qubits | Normalized window |
|---|---:|---|---|---|---|
| flat_pattern_01 | 8 | `0.42054081161117118` | [94, 252, 345, 1254, 1310, 1366, 1422, 1543] | [1, 2, 8, 10, 13] | `cx q[partner],q[target]; rz(pi/2) q[target]; ry(0.42054081161117118) q[target]; rz(pi) q[target]; cx q[partner],q[target];` |
| flat_pattern_02 | 2 | `0.99803486463018953` | [155, 1602] | [10, 15] | `cx q[partner],q[target]; ry(0.99803486463018953) q[target]; rz(pi/2) q[target]; cx q[partner],q[target];` |
| flat_pattern_03 | 1 | `2.8134684478406053` | [477] | [5] | `cx q[partner],q[target]; rz(pi) q[target]; ry(2.8134684478406053) q[target]; rz(-pi/2) q[target]; cx q[partner],q[target];` |

## Claim Boundary

- No occurrence-removing rewrite is claimed.
- No KAK theorem or semantic equivalence theorem is claimed.
- No B7 ledger improvement is counted.
- Solving all 11 invariant-flat windows would still leave 19 occurrences / 380 proxy-T units missing for the current one-sided 1.20x `gcm_h6` target.

Validation error count: `0`
