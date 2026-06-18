# B2 Hardware-Like Leakage Observation Model Gate v0.1

Status: **hardware_like_leakage_model_negative_boundary**

## Summary

- Method: b2_hardware_like_leakage_model_gate_v0
- Model status: hardware_like_leakage_observation_model_not_calibrated_not_hardware
- Source result: results/B2_per_shot_decoder_trace_packet_v0.json
- Source challenge count: 3
- Observation profiles: 3
- Total profile shots: 1728
- Holdout profile shots: 864
- Baseline total failures across profiles: 66
- Best profile: conservative_hardware_like_leakage
- Best profile injected failures: 22
- Best profile failure delta: 0
- Best profile fixed / introduced failures: 0 / 0
- Best profile changed predictions: 0
- Best profile model flag events: 415
- Best profile max adjusted edge probability: 0.230511
- Best profile holdout injected failures: 16
- Best profile holdout failure delta: 0
- Best profile holdout fixed / introduced failures: 0 / 0
- Holdout improvement gate passed: False
- Holdout non-regression gate passed: True
- Route demotion recommended: True
- Synthetic flag fixture consumed: False
- Calibrated flag data used: False
- Real hardware trace used: False
- Validation errors: []

## Profile Results

| profile | shots | baseline failures | injected failures | delta | fixed | introduced | changed | model flags | holdout injected | holdout delta | holdout introduced |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| conservative_hardware_like_leakage | 576 | 22 | 22 | 0 | 0 | 0 | 0 | 415 | 16 | 0 | 0 |
| nominal_hardware_like_leakage | 576 | 22 | 22 | 0 | 0 | 0 | 0 | 528 | 16 | 0 | 0 |
| stress_hardware_like_leakage | 576 | 22 | 22 | 0 | 0 | 0 | 0 | 727 | 16 | 0 | 0 |

## Challenge/Profile Detail

| challenge | profile | shots | baseline failures | injected failures | delta | fixed | introduced | changed | model flags |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| b2_trace_01_cb2f08eba4 | conservative_hardware_like_leakage | 192 | 10 | 10 | 0 | 0 | 0 | 0 | 128 |
| b2_trace_01_cb2f08eba4 | nominal_hardware_like_leakage | 192 | 10 | 10 | 0 | 0 | 0 | 0 | 177 |
| b2_trace_01_cb2f08eba4 | stress_hardware_like_leakage | 192 | 10 | 10 | 0 | 0 | 0 | 0 | 266 |
| b2_trace_02_c994e6c2e9 | conservative_hardware_like_leakage | 192 | 5 | 5 | 0 | 0 | 0 | 0 | 145 |
| b2_trace_02_c994e6c2e9 | nominal_hardware_like_leakage | 192 | 5 | 5 | 0 | 0 | 0 | 0 | 176 |
| b2_trace_02_c994e6c2e9 | stress_hardware_like_leakage | 192 | 5 | 5 | 0 | 0 | 0 | 0 | 206 |
| b2_trace_03_94b4e88303 | conservative_hardware_like_leakage | 192 | 7 | 7 | 0 | 0 | 0 | 0 | 142 |
| b2_trace_03_94b4e88303 | nominal_hardware_like_leakage | 192 | 7 | 7 | 0 | 0 | 0 | 0 | 175 |
| b2_trace_03_94b4e88303 | stress_hardware_like_leakage | 192 | 7 | 7 | 0 | 0 | 0 | 0 | 255 |

## Claim Boundary

- hardware_like_leakage_model_built: True
- hardware_like_leakage_model_used: True
- detector_bitstrings_consumed: True
- synthetic_flag_fixture_consumed: False
- real_flag_events_claimed: False
- production_decoder_claimed: False
- threshold_claimed: False
- new_code_claimed: False
- hardware_result_claimed: False
- calibrated_device_claimed: False
- quantum_advantage_claimed: False
- what_is_supported: The decoder interface can consume a deterministic hardware-like leakage observation model derived from detector bitstrings and challenge-level leakage/false-positive parameters.
- what_is_not_supported: The model is not fitted to real device observations and does not constitute calibrated leakage data, a hardware trace, a production decoder, a threshold result, or a new code.

## Next Gate

The route remains demoted until the same interface is driven by real
calibrated leakage/flag observations or independently supplied hardware
traces, and until holdout improvement plus all-challenge non-regression
both pass under that stronger evidence.
