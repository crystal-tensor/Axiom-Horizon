# B1/B7 cone_01 Union-Region Two-Free-Parameter Pricing Gate

- Method: `b1_b7_cone01_union_region_two_free_parameter_pricing_gate_v0`
- Status: `cone01_union_region_two_free_parameter_pricing_rejected`
- Model status: `two_free_parameter_union_census_candidates_do_not_recover_exactness`
- Workload: `qasmbench_medium_exact/gcm_h6.qasm`
- Union window: `[1369, 1379]`
- Support qubits: `[4, 8]`
- Orientation sequences: `['01-01', '01-10', '10-01', '10-10']`
- Two-free trials: `612`
- Exact pass / fail: `0` / `612`
- Best two-free residual: `0.1831095797026285`
- Best two-free sequence / parameter pair: `10-10` / `[5, 7]`
- Worst best-sequence residual: `0.46644639853601`
- Two-free proxy-T pressure if accepted: `40`
- Current line-1381 proxy-T pressure: `100`
- Two-free pricing candidate found: `False`
- B7 ledger improvement claimed: `False`

## Claim Boundary

Within the T-B1-004bf union-region two-CNOT census candidates, this gate tests whether exactly two off-grid local-U3 parameters can recover exact replay after snapping all others to the pi/4 grid.

Unsupported claims:
- This is not a global lower bound for the union target.
- A local exact two-free candidate, if present, is not a full-circuit replay certificate.
- This does not accept occurrence removal, proxy-T reduction, or a B7 ledger improvement.

## Sequence Best Rows

- `01-01`: best pair `[10, 17]`, residual `0.31204185933778894`, exact passes `0` / `153`
- `01-10`: best pair `[4, 11]`, residual `0.2878402004195689`, exact passes `0` / `153`
- `10-01`: best pair `[7, 15]`, residual `0.46644639853601`, exact passes `0` / `153`
- `10-10`: best pair `[5, 7]`, residual `0.1831095797026285`, exact passes `0` / `153`
