# B1/B7 Cone_01 Line-1381 Context Absorption Gate

Status: `cone01_line1381_context_absorption_not_accepted`

This artifact consumes T-B1-004an and tests whether the five remaining line-1381 local-U3 parameters can be absorbed by exact inventory matches or one-step same-support context cancellation in the native optimized `gcm_h6` QASM.

## Summary

- Target candidate line: `1381`
- Support qubits: `[4, 8]`
- Source window: `1369`-`1379`
- Context radius: `+/-64` lines
- Context rotation arguments reviewed: `44`
- Parameters tested: `5`
- Inventory exact / absolute-angle matched parameters: `0` / `0`
- Same-support context absolute-angle matched parameters: `0`
- One-step context pi/4-grid cancellations accepted: `0`
- Min / max best one-step context grid-cancellation error: `2.746555212048e-03` / `9.773822449712e-02`
- Accepted replay / occurrence / proxy-T reduction: `0` / `0` / `0`
- Validation errors: `0`

## Parameter Rows

| Param index | Value/pi | Inventory abs matches | Context abs matches | Best context grid error | Best context line | Accepted |
|---:|---:|---:|---:|---:|---:|---|
| 3 | 0.454632085623 | 0 | 0 | 2.665955e-02 | 1352 | False |
| 4 | -0.365263446443 | 0 | 0 | 2.746555e-03 | 1378 | False |
| 9 | -0.335026659005 | 0 | 0 | 9.773822e-02 | 1378 | False |
| 16 | 0.177917927571 | 0 | 0 | 5.726545e-02 | 1352 | False |
| 17 | 0.134736553557 | 0 | 0 | 2.746555e-03 | 1381 | False |

## Claim Boundary

This closes only a single-step context-inventory route. It does not rule out multi-rotation absorption, commutation-aware context rewriting, broader symbolic synthesis, or full-circuit replay. The B7 ledger remains unchanged at zero accepted occurrence removals and zero accepted proxy-T reduction.

## Next Required Gate

The next route must either build a multi-rotation/context-aware symbolic absorption search or abandon the local inventory route and construct a full-circuit replay certificate with explicit resource pricing for the five remaining line-1381 parameters.
