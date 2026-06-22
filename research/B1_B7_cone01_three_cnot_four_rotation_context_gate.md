# B1/B7 Cone_01 Three-CNOT Four-Rotation Context Gate

Status: `cone01_three_cnot_four_rotation_context_not_accepted`

This artifact consumes T-B1-004bs and tests whether the 18 off-pi/4 local-U3 parameters in the best exact 3-CNOT priced candidate can be absorbed by signed sums of exactly four nearby same-support context rotations in the native optimized `gcm_h6` QASM.

## Summary

- Selected sequence: `10-10-01`
- Selected off-grid parameters / proxy-T pressure: `18` / `360`
- Source window: `[1369, 1379]`
- Context radius: `+/-64` lines
- Context rotation arguments reviewed: `44`
- Parameters tested: `18`
- Signed width-4 combinations per parameter: `2172016`
- Total signed combination tests: `39096288`
- Width-4 exact absorption parameters: `0`
- Min / max best width-4 grid error: `6.557999011454e-04` / `2.777971977898e-02`
- Accepted replay / occurrence / proxy-T reduction: `0` / `0` / `0`
- Validation errors: `0`

## Parameter Rows

| Param index | Value/pi | Best width-4 error | Best lines | Accepted |
|---:|---:|---:|---|---|
| 2 | -0.465712363752 | 5.785812e-03 | [1311, 1352, 1378, 1381] | False |
| 3 | 0.484317257958 | 6.414673e-03 | [1311, 1349, 1378, 1381] | False |
| 4 | -0.814501764722 | 6.967977e-03 | [1327, 1349, 1352, 1378] | False |
| 5 | -0.844984590994 | 1.571224e-02 | [1352, 1378, 1381, 1424] | False |
| 7 | -0.367945756891 | 5.680172e-03 | [1311, 1318, 1327, 1378] | False |
| 8 | 0.632054243109 | 5.680172e-03 | [1311, 1318, 1327, 1378] | False |
| 9 | -0.750743960797 | 2.337222e-03 | [1311, 1318, 1322, 1327] | False |
| 10 | 0.618913741868 | 8.721186e-03 | [1311, 1318, 1327, 1378] | False |
| 11 | 0.509154655999 | 2.276965e-03 | [1311, 1352, 1378, 1424] | False |
| 13 | -0.999791252408 | 6.557999e-04 | [1311, 1318, 1322, 1327] | False |
| 15 | -0.704988646181 | 2.777972e-02 | [1327, 1349, 1351, 1352] | False |
| 16 | -0.318066903839 | 1.103203e-02 | [1349, 1352, 1378, 1381] | False |
| 17 | -0.131454105108 | 7.565561e-03 | [1327, 1349, 1351, 1378] | False |
| 19 | 0.166037819118 | 1.242122e-02 | [1311, 1318, 1352, 1378] | False |
| 20 | -0.299883292226 | 1.247407e-02 | [1311, 1322, 1349, 1352] | False |
| 21 | -0.837381112213 | 8.174797e-03 | [1352, 1378, 1381, 1424] | False |
| 22 | 0.674031978995 | 1.269318e-02 | [1327, 1349, 1352, 1378] | False |
| 23 | -0.662316278828 | 7.224122e-03 | [1352, 1378, 1381, 1424] | False |

## Claim Boundary

This closes only a bounded exactly-four-rotation context-combination route for the direct 3-CNOT candidate. It does not rule out five-or-more-rotation symbolic absorption, commutation-aware rewriting, broader symbolic synthesis, or full-circuit replay. The B7 ledger remains unchanged at zero accepted occurrence removals and zero accepted proxy-T reduction.

## Next Required Gate

The next route must either build a stronger symbolic/full-circuit replay certificate, find a different scaffold that beats the current 5-parameter / 100-proxy-T line-1381 boundary, or abandon this direct 3-CNOT route for another occurrence-removing scaffold with honest B7 resource accounting.
