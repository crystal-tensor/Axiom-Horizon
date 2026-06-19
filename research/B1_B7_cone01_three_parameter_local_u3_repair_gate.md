# B1/B7 Cone_01 Three-Parameter Local-U3 Repair Gate

Status: `cone01_three_parameter_local_u3_repair_partial_not_ledger_accepted`

This artifact consumes T-B1-004ai and exhaustively frees exactly three local-U3 parameters for each unresolved reduced-CNOT packet.

## Summary

- Source sparse exact packets: `1`
- Source unresolved packets: `2`
- Three-parameter candidates searched: `1632`
- New three-parameter exact packets: `1`
- Total exact packets after this gate: `2` / `3`
- Remaining unresolved packets: `1`
- Partial CNOT reduction if accepted: `6`
- Remaining unrepaired off-grid replacement parameters: `15`
- Accepted occurrence/proxy-T reduction: `0` / `0`
- Validation errors: `0`

## Packet Rows

| Candidate line | Replacement CX | 2-param residual | Best 3-param residual | Exact 3-param pass | Exact indices | Accepted rewrite |
|---:|---:|---:|---:|---|---|---|
| 1381 | 2 | 2.653547e-01 | 4.986518e-02 | False | None | False |
| 268 | 2 | 3.989908e-01 | 6.398929e-13 | True | [1, 8, 13] | False |

## Claim Boundary

Line 268 now has a bounded packet-level exact repair after freeing three local-U3 parameters, while line 1381 remains unrepaired after all exactly-three-parameter combinations. The project still has only 2/3 bounded packet repairs, no symbolic exact decomposition, no full-circuit replay certificate, and no B7 occurrence/proxy-T saving.

## Next Required Gate

The next route must repair line 1381 with a broader scaffold, prove a scoped obstruction for this reduced-CNOT family, or abandon the reduced-CNOT scaffold for a different occurrence-removing route.
