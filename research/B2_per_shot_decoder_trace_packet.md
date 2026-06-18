# B2 Per-Shot Decoder Trace Packet v0.1

Status: **per_shot_trace_packet_available_decoder_injection_still_missing**

## Summary

- Method: b2_per_shot_decoder_trace_packet_v0
- Model status: stim_sampled_detector_bitstrings_with_synthetic_flag_events_not_posterior_decoder
- Source result: results/B2_posterior_weighted_decoder_risk_ledger_v0.json
- Challenge count: 3
- Shots per challenge: 192
- Total shot traces: 576
- Total logical failures: 22
- Max detector count: 120
- Total synthetic flag events: 482
- Mean synthetic flag events per shot: 0.836806
- Max decoder runtime seconds per shot: 3.08963e-06
- Per-shot detector bitstrings persisted: True
- Synthetic detector/tick flag events persisted: True
- Posterior likelihood decoder injection performed: False
- Real hardware or calibrated flag events: False
- Validation errors: []

## Challenge Packets

| challenge | profile | basis | p | leakage | fp | d | shots | failures | detectors | synthetic flags | Wilson high |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| b2_trace_01_cb2f08eba4 | nominal_lab_detector_0p90 | x | 0.003 | 0.01 | 0.001 | 5 | 192 | 10 | 120 | 232 | 0.0932061 |
| b2_trace_02_c994e6c2e9 | nominal_lab_detector_0p90 | x | 0.005 | 0.005 | 0.001 | 5 | 192 | 5 | 120 | 138 | 0.0595041 |
| b2_trace_03_94b4e88303 | high_purity_detector_0p95 | x | 0.005 | 0.005 | 0.001 | 5 | 192 | 7 | 120 | 112 | 0.0733318 |

## Contract Delta

- per_shot_syndrome_bitstrings: available_for_sampled_stim_challenge_rows
- detector_tick_indexed_flag_events: synthetic_proxy_available_not_calibrated_or_hardware
- posterior_likelihood_injection_api: missing
- calibrated_leakage_confusion_matrix: missing

## Claim Boundary

- per_shot_trace_packet_built: True
- stim_detector_bitstrings_sampled: True
- synthetic_flag_events_built: True
- real_flag_events_claimed: False
- circuit_level_decoder_claimed: False
- posterior_likelihood_decoder_claimed: False
- production_decoder_claimed: False
- threshold_claimed: False
- new_code_claimed: False
- hardware_result_claimed: False
- calibrated_device_claimed: False
- what_is_supported: The current B2 route now has replayable per-shot detector bitstrings, observables, baseline PyMatching predictions, and synthetic detector/tick flag events for selected strict challenge rows.
- what_is_not_supported: This is not posterior likelihood injection, not a production decoder, not calibrated leakage evidence, not a hardware result, and not a threshold or new-code claim.

## Next Gate

Use these per-shot detector traces as the input fixture for a posterior-likelihood
decoder injection experiment. The B2 route remains demoted until the decoder
consumes calibrated or explicitly modeled flag likelihoods and improves strict
high-purity and all-profile robustness gates.
