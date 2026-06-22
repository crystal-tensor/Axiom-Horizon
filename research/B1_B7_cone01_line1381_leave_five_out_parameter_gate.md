# B1/B7 cone_01 Line-1381 Leave-Five-Out Parameter Gate

- Method: `b1_b7_cone01_line1381_leave_five_out_parameter_gate_v0`
- Status: `cone01_line1381_no_all_grid_parameter_free_removal`
- Model status: `line1381_off_grid_parameter_set_is_not_all_grid_snappable`
- Workload: `qasmbench_medium_exact/gcm_h6.qasm`
- Source five-parameter repair: `results/B1_B7_cone01_five_parameter_line1381_exact_repair_gate_v0.json`
- Source leave-four-out gate: `results/B1_B7_cone01_line1381_leave_four_out_parameter_gate_v0.json`

## Result

- Current line-1381 off-grid parameter indices: `[3, 4, 9, 16, 17]`
- Base five-parameter residual: `6.513210005207597e-13`
- Leave-five-out rows: `1`
- Exact pass / fail: `0` / `1`
- All-grid residual: `0.8415210419190079`
- Residual ratio to exact tolerance: `84152104.19190079`
- Five-parameter free removal accepted: `False`
- Accepted occurrence / proxy-T reduction / B7 claim: `0` / `0` / `False`

## Leave-Five-Out Row

| Fixed parameters | Snap errors | Reoptimized indices | Residual | Exact |
| --- | ---: | --- | ---: | --- |
| [3, 4, 9, 16, 17] | [0.142527506515, 0.362110796574, 0.267119127289, 0.226452509199, 0.362110796574] | `[]` | 0.841521041919 | False |

## Claim Boundary

- This is a scaffold-local all-grid endpoint pressure gate, not a global minimality theorem.
- The result blocks a cheap all-parameter grid-snap claim for line 1381, but it does not remove, absorb, or symbolically decompose the five-parameter burden.
