# B2 Decoder Input Contract Feasibility Gate v0.1

Last updated: 2026-06-18

Status: **decoder_input_contract_failed_calibrated_data_or_decoder_required**

## Summary

- Method: `b2_decoder_input_contract_feasibility_gate_v0`
- Model status: `decoder_input_contract_from_aggregate_rows_not_circuit_level_decoder`
- Contract inputs available/missing: 4 / 6
- Feasibility gates passed/failed: 4 / 5
- Failed critical gates: 5
- Raw / conservative / strict d=5/d=7 survivors: 6 / 3 / 3
- Strict high-purity adjusted survivors: 0
- Robust all-profile adjusted survival: False
- Decoder contract satisfied: False
- Demotion recommended until decoder or calibration: True
- Validation errors: 0

## Decoder Contract Inputs

| Input | Available | Source or blocker |
|---|---:|---|
| stim_detector_error_model | True | upstream Stim/PyMatching false-positive stress |
| aggregate_target_volume_rows | True | results/B2_posterior_weighted_decoder_risk_ledger_v0.json |
| posterior_flag_probabilities | True | results/B2_shot_conditioned_erasure_decoder_boundary_v0.json |
| risk_adjusted_volume_rows | True | results/B2_posterior_weighted_decoder_risk_ledger_v0.json |
| per_shot_syndrome_bitstrings | False | Only aggregate target-comparison rows are retained; per-shot syndrome traces are not present. |
| per_detector_flag_event_ids | False | Flag posterior rows are profile-level rows, not detector/tick-indexed flag events. |
| decoder_likelihood_injection_api | False | No PyMatching/Stim decoder path consumes posterior flag probabilities as edge weights. |
| calibrated_leakage_confusion_matrix | False | Detection efficiency and false-positive rates are profile assumptions, not measured calibration data. |
| holdout_validation_or_hardware_trace | False | No hardware trace, calibrated dataset, or holdout split exists for posterior-weight validation. |
| decoder_runtime_and_threshold_curve | False | No circuit-level shot-conditioned decoder runtime or distance-scaling curve has been measured. |

## Feasibility Gates

| Gate | Critical | Passed | Evidence | Required next step |
|---|---:|---:|---|---|
| G1: Posterior flag probabilities exist | False | True | evaluated_profile_rows=1152; calibration_profile_count=4 | Keep carrying posterior fields into decoder-facing artifacts. |
| G2: Conservative risk-adjusted d=5/d=7 survivors exist | False | True | conservative_adjusted_surviving_d5_d7_rows=3; conservative_max_decoder_adjusted_reduction=1.99364 | Preserve these rows only as candidate rows for a real decoder run. |
| G3: Strict risk-adjusted d=5/d=7 survivors exist | False | True | strict_adjusted_surviving_d5_d7_rows=3; strict_max_decoder_adjusted_reduction=1.79427 | Run a decoder with these rows as challenge cases. |
| G4: Strict high-purity survivor exists | True | False | strict_high_purity_adjusted_survivors=0 | Obtain high-purity flag rows or demote the route under strict calibration assumptions. |
| G5: All-profile robustness exists | True | False | robust_all_profile_adjusted_survival=False; survivor_profiles=['field_detector_0p80', 'high_purity_detector_0p95', 'nominal_lab_detector_0p90'] | Show survival across all declared detector profiles or keep the route profile-sensitive. |
| G6: Per-shot syndrome and flag traces are available | True | False | per_shot_syndrome_bitstrings=False; per_detector_flag_event_ids=False | Persist shot-level syndrome bitstrings and detector/tick-indexed flag events from Stim or hardware. |
| G7: Posterior probabilities are injected into a circuit-level decoder | True | False | decoder_likelihood_injection_api=False; circuit_level_decoder_claimed=False | Implement a PyMatching/Stim decoder path that consumes posterior flag likelihoods as edge weights. |
| G8: Calibrated leakage/flag data are available | True | False | calibrated_leakage_confusion_matrix=False; holdout_validation_or_hardware_trace=False | Collect calibrated leakage/flag data or provide a holdout validation split. |
| G9: Claim boundary remains clean | False | True | new_code_claimed=False; threshold_claimed=False; production_decoder_claimed=False; hardware_result_claimed=False | Continue to block threshold, hardware, and new-code claims until a real decoder passes. |

## Interpretation

The current B2 heralded-erasure route has useful posterior/risk rows, but it still lacks the data shape needed by a circuit-level shot-conditioned decoder.
The route should stay demoted until per-shot syndrome/flag traces, posterior likelihood injection, and calibrated leakage/flag validation exist.

## Claim Boundary

- decoder_input_contract_built: True
- demotion_recommended_until_decoder_or_calibration: True
- circuit_level_decoder_claimed: False
- shot_conditioned_erasure_decoder_claimed: False
- production_decoder_claimed: False
- threshold_claimed: False
- new_code_claimed: False
- hardware_result_claimed: False
- calibrated_device_claimed: False
- what_is_supported: A decoder-facing input contract and feasibility gate over the current posterior/risk rows.
- what_is_not_supported: This is not a circuit-level shot-conditioned decoder, not a production decoder, not calibrated leakage data, not a threshold result, not a hardware result, and not a new-code claim.
- next_gate: Persist per-shot syndrome/flag traces and implement posterior likelihood injection in a decoder, or collect calibrated leakage/flag data.
