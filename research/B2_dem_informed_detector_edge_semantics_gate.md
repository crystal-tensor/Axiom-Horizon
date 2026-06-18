# B2 DEM-Informed Detector-To-Edge Semantics Gate v0.1

Status: **dem_informed_detector_edge_semantics_negative_boundary**

## Summary

- Method: b2_dem_informed_detector_edge_semantics_gate_v0
- Model status: stim_dem_edge_probability_semantics_with_synthetic_flags_not_calibrated_data
- Source result: results/B2_per_shot_decoder_trace_packet_v0.json
- Source challenge count: 3
- Semantic profiles: 3
- Total profile shots: 1728
- Baseline total failures across profiles: 66
- Best profile: conservative_dem_responsibility
- Best profile injected failures: 22
- Best profile failure delta: 0
- Best profile fixed / introduced failures: 0 / 0
- Best profile changed predictions: 0
- Best profile max adjusted edge probability: 0.254668
- Improvement gate passed: False
- All-challenge non-regression gate passed: True
- Route demotion recommended: True
- Calibrated flag data used: False
- Real hardware trace used: False
- Validation errors: []

## Profile Results

| profile | shots | baseline failures | injected failures | delta | fixed | introduced | changed predictions | mean adjusted edges/shot | max adjusted p(edge) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| aggressive_dem_responsibility | 576 | 22 | 23 | 1 | 0 | 1 | 1 | 6.42361 | 0.55 |
| conservative_dem_responsibility | 576 | 22 | 22 | 0 | 0 | 0 | 0 | 6.42361 | 0.254668 |
| nominal_dem_responsibility | 576 | 22 | 22 | 0 | 0 | 0 | 0 | 6.42361 | 0.394712 |

## Challenge/Profile Detail

| challenge | profile | shots | baseline failures | injected failures | delta | fixed | introduced | changed |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| b2_trace_01_cb2f08eba4 | conservative_dem_responsibility | 192 | 10 | 10 | 0 | 0 | 0 | 0 |
| b2_trace_01_cb2f08eba4 | nominal_dem_responsibility | 192 | 10 | 10 | 0 | 0 | 0 | 0 |
| b2_trace_01_cb2f08eba4 | aggressive_dem_responsibility | 192 | 10 | 10 | 0 | 0 | 0 | 0 |
| b2_trace_02_c994e6c2e9 | conservative_dem_responsibility | 192 | 5 | 5 | 0 | 0 | 0 | 0 |
| b2_trace_02_c994e6c2e9 | nominal_dem_responsibility | 192 | 5 | 5 | 0 | 0 | 0 | 0 |
| b2_trace_02_c994e6c2e9 | aggressive_dem_responsibility | 192 | 5 | 6 | 1 | 0 | 1 | 1 |
| b2_trace_03_94b4e88303 | conservative_dem_responsibility | 192 | 7 | 7 | 0 | 0 | 0 | 0 |
| b2_trace_03_94b4e88303 | nominal_dem_responsibility | 192 | 7 | 7 | 0 | 0 | 0 | 0 |
| b2_trace_03_94b4e88303 | aggressive_dem_responsibility | 192 | 7 | 7 | 0 | 0 | 0 | 0 |

## Claim Boundary

- dem_edge_probability_semantics_built: True
- dem_edge_probability_semantics_performed: True
- synthetic_flag_likelihoods_consumed: True
- real_flag_events_claimed: False
- production_decoder_claimed: False
- threshold_claimed: False
- new_code_claimed: False
- hardware_result_claimed: False
- calibrated_device_claimed: False
- quantum_advantage_claimed: False
- what_is_supported: The B2 injection interface now uses DEM edge probabilities to map flagged detector posteriors onto incident decoder edges instead of a flat neighboring-edge shift.
- what_is_not_supported: The flag events remain synthetic and uncalibrated; this is not a production decoder, threshold result, hardware result, or new code.

## Next Gate

The next gate still requires calibrated leakage/flag observations or a
hardware-like leakage model. This DEM-informed semantic layer is only a
decoder-interface pressure test over synthetic flags.
