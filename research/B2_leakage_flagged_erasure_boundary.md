# B2 Leakage-Flagged Erasure Boundary v0.1

- Status: leakage_flagged_erasure_boundary_proxy_not_new_code_claim
- Method: b2_leakage_flagged_erasure_boundary_v0
- Model status: analytic_leakage_proxy_not_circuit_level_decoder
- Configurations: 480
- Baseline met count: 264
- Candidate met count: 335
- Improved target-volume rows: 42
- Improved rows with candidate distance 5 or 7: 33
- High-efficiency distance-5/7 improvements: 19
- Maximum volume reduction: 23.904170363797693
- Mean volume reduction on improved rows: 4.836897786181641
- Minimum detection efficiency with improvement: 0.5
- Validation errors: []

## Interpretation

In this analytic proxy, flagged leakage-to-erasure information can lower the distance and target-volume proxy for some d=5/d=7 candidate rows under the same surface-code threshold-law denominator.

This is not a new code, threshold estimate, circuit-level decoder result, hardware-calibrated leakage model, or solved low-overhead QEC claim.

The screen does not reduce syndrome rounds. The only volume pressure comes from a
higher flagging overhead and from distance changes induced by the leakage model.

## Top Improved Rows

| p | leakage | detection | target | baseline d | candidate d | baseline volume | candidate volume | reduction |
|---|---|---|---|---|---|---|---|---|
| 0.003 | 0.20 | 0.75 | 0.01 | 15 | 5 | 6735.00 | 281.75 | 23.904 |
| 0.003 | 0.20 | 0.90 | 0.01 | 15 | 5 | 6735.00 | 281.75 | 23.904 |
| 0.003 | 0.20 | 0.97 | 0.01 | 15 | 5 | 6735.00 | 281.75 | 23.904 |
| 0.003 | 0.20 | 0.50 | 0.01 | 15 | 7 | 6735.00 | 780.85 | 8.625 |
| 0.005 | 0.06 | 0.90 | 0.01 | 13 | 7 | 4381.00 | 780.85 | 5.611 |
| 0.005 | 0.06 | 0.97 | 0.01 | 13 | 7 | 4381.00 | 780.85 | 5.611 |
| 0.003 | 0.15 | 0.75 | 0.01 | 9 | 5 | 1449.00 | 281.75 | 5.143 |
| 0.003 | 0.15 | 0.90 | 0.01 | 9 | 5 | 1449.00 | 281.75 | 5.143 |
| 0.003 | 0.15 | 0.97 | 0.01 | 9 | 5 | 1449.00 | 281.75 | 5.143 |
| 0.005 | 0.10 | 0.50 | 0.05 | 9 | 5 | 1449.00 | 281.75 | 5.143 |
| 0.005 | 0.10 | 0.75 | 0.05 | 9 | 5 | 1449.00 | 281.75 | 5.143 |
| 0.005 | 0.10 | 0.90 | 0.05 | 9 | 5 | 1449.00 | 281.75 | 5.143 |
| 0.005 | 0.10 | 0.97 | 0.05 | 9 | 5 | 1449.00 | 281.75 | 5.143 |
| 0.007 | 0.03 | 0.50 | 0.05 | 9 | 5 | 1449.00 | 281.75 | 5.143 |
| 0.007 | 0.03 | 0.75 | 0.05 | 9 | 5 | 1449.00 | 281.75 | 5.143 |
| 0.007 | 0.03 | 0.90 | 0.05 | 9 | 5 | 1449.00 | 281.75 | 5.143 |

## Next Gate

Replace this analytic proxy with a circuit-level leakage/erasure decoder experiment
or a calibrated leakage model. A stronger baseline should kill the result if the
flagging overhead, decoder assumptions, or leakage correlations erase the d=5/d=7
distance pressure seen here.
