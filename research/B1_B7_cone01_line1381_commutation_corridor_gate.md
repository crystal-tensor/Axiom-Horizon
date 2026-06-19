# B1/B7 cone_01 Line-1381 Commutation Corridor Gate

## Summary

- Method: `b1_b7_cone01_line1381_commutation_corridor_gate_v0`
- Status: `cone01_line1381_commutation_corridor_not_accepted`
- Target line / window: 1381 / 1369-1379
- Best context candidates reviewed: 10
- Context references reviewed / unique lines: 32 / 8
- Inside-packet / non-standalone / blocked corridor references: 7 / 13 / 21
- Clear external standalone-Z references: 0
- Candidates with all references corridor-accepted: 0
- Accepted replay / occurrence / proxy-T reduction: 0 / 0 / 0
- Validation errors: 0

## Claim Boundary

The best bounded two-/three-/four-rotation line-1381 context hints do not form a cheap commutation corridor into the target packet under the declared model.

Unsupported claims:

- This is not a symbolic/full-circuit replay proof.
- This is not a global obstruction theorem for line 1381.
- This does not reject non-cheap commutation, resynthesis, or a different scaffold.
- No B7 occurrence or proxy-T ledger reduction is accepted.

## Interpretation

The bounded context hints now fail a replay-adjacent precondition: the referenced rotations are either inside the target packet, embedded inside U3 components, or blocked by support-touching CNOT/non-diagonal structure before they can be moved into the packet under the cheap commutation model. The next useful route is a real symbolic/full-circuit replay scaffold or a different occurrence-removing rewrite, not counting any B7 saving from these hints.
