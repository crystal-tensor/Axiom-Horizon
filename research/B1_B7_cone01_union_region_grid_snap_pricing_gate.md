# B1/B7 cone_01 Union-Region Grid-Snap Pricing Gate

- Method: `b1_b7_cone01_union_region_grid_snap_pricing_gate_v0`
- Status: `cone01_union_region_grid_snap_pricing_rejected`
- Model status: `two_cnot_union_census_candidates_do_not_become_grid_priced`
- Workload: `qasmbench_medium_exact/gcm_h6.qasm`
- Source orientation census: `results/B1_B7_cone01_union_region_two_cnot_orientation_census_gate_v0.json`
- Source pricing dominance: `results/B1_B7_cone01_union_region_pricing_dominance_gate_v0.json`

## Result

- Orientation sequences: `['01-01', '01-10', '10-01', '10-10']`
- Grid-snap exact pass / fail: `0` / `4`
- Best grid-snap residual: `0.36435162331693166` at `10-10`
- Worst grid-snap residual: `1.021457442072864` at `10-01`
- Best source off-grid parameters / proxy-T pressure: `13` / `260`
- Current line-1381 proxy-T pressure: `100`
- Grid-snap pricing accepted: `False`
- Accepted occurrence / proxy-T reduction / B7 claim: `0` / `0` / `False`

## Rows

| Sequence | Source off-grid | Grid residual | Ratio to tolerance | Exact after snap |
| --- | ---: | ---: | ---: | --- |
| 01-01 | 15 | 0.656090143721 | 6.5609e+07 | False |
| 01-10 | 13 | 0.577311307934 | 5.77311e+07 | False |
| 10-01 | 14 | 1.02145744207 | 1.02146e+08 | False |
| 10-10 | 13 | 0.364351623317 | 3.64352e+07 | False |

## Claim Boundary

- This is a scoped grid-snap pricing rejection for the T-B1-004bf union-region census candidates.
- It is not a global union-region lower bound and does not accept occurrence removal or B7 ledger credit.
