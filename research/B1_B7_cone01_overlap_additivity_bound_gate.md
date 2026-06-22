# B1/B7 cone_01 Overlap Additivity Bound Gate

- Method: `b1_b7_cone01_overlap_additivity_bound_gate_v0`
- Status: `cone01_overlap_additivity_bound_blocks_line1378_delta_recovery`
- Model status: `contained_overlap_window_makes_line1378_delta_nonadditive`
- Workload: `qasmbench_medium_exact/gcm_h6.qasm`
- Source non-overlap subset: `results/B1_B7_cone01_nonoverlap_patch_subset_gate_v0.json`
- Source pricing result: `results/B1_B7_cone01_line1381_local_u3_pricing_gate_v0.json`

## Result

- Line-1378 window: `[1369, 1377]`
- Line-1381 window: `[1369, 1379]`
- Union window: `[1369, 1379]`
- Contained overlap / same support: `True` / `True`
- Union source CNOT count: `5`
- Line-1381 delta / line-1378 delta: `3` / `3`
- Additive pair delta requested: `6`
- Required replacement CNOT count for additive pair delta: `-1`
- Additive recovery impossible by CNOT bound: `True`
- Max additional delta vs line 1381 under nonnegative replacement CNOT: `2`
- Full lost line-1378 delta recoverable by contained merge: `False`
- Accepted occurrence / proxy-T reduction: `0` / `0`

## Claim Boundary

- This is an overlap-accounting negative boundary, not a merged-region synthesis result.
- The next valid route is not additive delta recovery; it must synthesize a new union-region replacement, prove replay, and price remaining local-U3 burden under B7.
