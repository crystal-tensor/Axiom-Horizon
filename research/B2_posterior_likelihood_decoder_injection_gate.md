# B2 Posterior-Likelihood Decoder Injection Gate v0.1

Status: **posterior_likelihood_injection_interface_negative_boundary**

## Summary

- Method: b2_posterior_likelihood_decoder_injection_gate_v0
- Model status: per_shot_synthetic_flag_likelihood_injection_not_calibrated_decoder
- Source result: results/B2_per_shot_decoder_trace_packet_v0.json
- Source challenge count: 3
- Injection profiles: 3
- Total profile shots: 1728
- Baseline total failures across profiles: 66
- Best profile: mild_flag_weight_shift
- Best profile injected failures: 22
- Best profile failure delta: 0
- Best profile fixed / introduced failures: 0 / 0
- Best profile changed predictions: 0
- Improvement gate passed: False
- All-challenge non-regression gate passed: True
- Route demotion recommended: True
- Calibrated flag data used: False
- Real hardware trace used: False
- Validation errors: []

## Profile Results

| profile | shots | baseline failures | injected failures | delta | fixed | introduced | changed predictions | mean adjusted edges/shot | max decode s/shot |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| mild_flag_weight_shift | 576 | 22 | 22 | 0 | 0 | 0 | 0 | 6.42361 | 0.000324184 |
| nominal_flag_weight_shift | 576 | 22 | 22 | 0 | 0 | 0 | 0 | 6.42361 | 0.000318211 |
| strong_flag_weight_shift | 576 | 22 | 24 | 2 | 0 | 2 | 2 | 6.42361 | 0.00031955 |

## Challenge/Profile Detail

| challenge | profile | shots | baseline failures | injected failures | delta | fixed | introduced | changed |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| b2_trace_01_cb2f08eba4 | mild_flag_weight_shift | 192 | 10 | 10 | 0 | 0 | 0 | 0 |
| b2_trace_01_cb2f08eba4 | nominal_flag_weight_shift | 192 | 10 | 10 | 0 | 0 | 0 | 0 |
| b2_trace_01_cb2f08eba4 | strong_flag_weight_shift | 192 | 10 | 11 | 1 | 0 | 1 | 1 |
| b2_trace_02_c994e6c2e9 | mild_flag_weight_shift | 192 | 5 | 5 | 0 | 0 | 0 | 0 |
| b2_trace_02_c994e6c2e9 | nominal_flag_weight_shift | 192 | 5 | 5 | 0 | 0 | 0 | 0 |
| b2_trace_02_c994e6c2e9 | strong_flag_weight_shift | 192 | 5 | 6 | 1 | 0 | 1 | 1 |
| b2_trace_03_94b4e88303 | mild_flag_weight_shift | 192 | 7 | 7 | 0 | 0 | 0 | 0 |
| b2_trace_03_94b4e88303 | nominal_flag_weight_shift | 192 | 7 | 7 | 0 | 0 | 0 | 0 |
| b2_trace_03_94b4e88303 | strong_flag_weight_shift | 192 | 7 | 7 | 0 | 0 | 0 | 0 |

## Claim Boundary

- posterior_likelihood_injection_interface_built: True
- posterior_likelihood_injection_performed: True
- synthetic_flag_likelihoods_consumed: True
- real_flag_events_claimed: False
- circuit_level_decoder_claimed: False
- production_decoder_claimed: False
- threshold_claimed: False
- new_code_claimed: False
- hardware_result_claimed: False
- calibrated_device_claimed: False
- quantum_advantage_claimed: False
- what_is_supported: The persisted T-B2-009a detector traces can be consumed by a reproducible PyMatching edge-weight injection interface using declared synthetic flag posteriors.
- what_is_not_supported: The injection is not calibrated, not hardware-derived, not a production shot-conditioned decoder, and it does not pass the improvement plus non-regression gate.

## Next Gate

This interface must be replaced or strengthened with detector-to-edge semantics
derived from calibrated leakage events, not synthetic detector flags. B2 should
stay demoted until injected decoding improves strict challenge rows without
introducing new failures and survives all-profile robustness pressure.
