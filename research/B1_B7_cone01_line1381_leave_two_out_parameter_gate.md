# B1/B7 cone_01 Line-1381 Leave-Two-Out Parameter Gate

- Method: `b1_b7_cone01_line1381_leave_two_out_parameter_gate_v0`
- Status: `cone01_line1381_no_two_parameter_free_removal`
- Model status: `line1381_off_grid_parameter_pairs_are_leave_two_out_required`
- Workload: `qasmbench_medium_exact/gcm_h6.qasm`
- Source five-parameter repair: `results/B1_B7_cone01_five_parameter_line1381_exact_repair_gate_v0.json`
- Source leave-one-out gate: `results/B1_B7_cone01_line1381_leave_one_out_parameter_gate_v0.json`

## Result

- Current line-1381 off-grid parameter indices: `[3, 4, 9, 16, 17]`
- Base five-parameter residual: `6.513210005207597e-13`
- Leave-two-out rows: `10`
- Exact pass / fail: `0` / `10`
- Best leave-two-out residual: `0.13583443746892182` at parameters `[9, 16]`
- Worst leave-two-out residual: `0.41204448255804876` at parameters `[16, 17]`
- Minimum residual ratio to exact tolerance: `13583443.746892182`
- Two-parameter free removal accepted: `False`
- Accepted occurrence / proxy-T reduction / B7 claim: `0` / `0` / `False`

## Leave-Two-Out Rows

| Fixed parameters | Snap errors | Reoptimized indices | Residual | Exact |
| --- | ---: | --- | ---: | --- |
| [3, 4] | [0.142527506515, 0.362110796574] | `[9, 16, 17]` | 0.334482266708 | False |
| [3, 9] | [0.142527506515, 0.267119127289] | `[4, 16, 17]` | 0.304124919729 | False |
| [3, 16] | [0.142527506515, 0.226452509199] | `[4, 9, 17]` | 0.171772041819 | False |
| [3, 17] | [0.142527506515, 0.362110796574] | `[4, 9, 16]` | 0.21672567025 | False |
| [4, 9] | [0.362110796574, 0.267119127289] | `[3, 16, 17]` | 0.293917719745 | False |
| [4, 16] | [0.362110796574, 0.226452509199] | `[3, 9, 17]` | 0.294771583997 | False |
| [4, 17] | [0.362110796574, 0.362110796574] | `[3, 9, 16]` | 0.342353834061 | False |
| [9, 16] | [0.267119127289, 0.226452509199] | `[3, 4, 17]` | 0.135834437469 | False |
| [9, 17] | [0.267119127289, 0.362110796574] | `[3, 4, 16]` | 0.371261745982 | False |
| [16, 17] | [0.226452509199, 0.362110796574] | `[3, 4, 9]` | 0.412044482558 | False |

## Claim Boundary

- This is a scaffold-local leave-two-out pressure gate, not a global minimality theorem.
- The result blocks a cheap two-parameter removal claim for line 1381, but it does not remove, absorb, or symbolically decompose the five-parameter burden.
