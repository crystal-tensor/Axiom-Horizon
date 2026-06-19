# B4/B8 Verifier-Private Predicate Gate v0.1

Last updated: 2026-06-19

Status: **verifier_private_predicate_pressure_not_protocol_soundness**

## Summary

- Source support-spoofer result: `results/B4_B8_nonstabilizer_support_spoofer_gate_v0.json`
- Circuits attacked: 36
- Spoofer families: 4
- Attack rows: 144
- Private predicate bits: 4
- Max public support-only acceptance: 1.000000
- Max hidden private-predicate acceptance: 0.062500
- One private bit leaked acceptance: 0.125000
- Full private predicate leaked acceptance: 1.000000
- Suppression factor: 16.0x
- Acceptance gates passed / failed: 5 / 3

## Interpretation

The previous support-aware attack showed that a verifier checking only public support membership can be passed with acceptance 1.0. This gate adds four late-bound verifier-private predicate bits. Under the no-leakage analytic model, the same support-aware spoofers must guess those bits, reducing acceptance to 1/16.

The result is intentionally limited. If the private predicate fully leaks, acceptance returns to 1.0; with one predicate bit leaked, acceptance rises to 1/8. Therefore this is a verifier-burden gate and leakage boundary, not a soundness proof.

## Acceptance Gates

- PASS: `source_support_spoofer_loaded` - The gate consumes the support-aware spoofer boundary.
- PASS: `private_predicate_commitments_present` - Every attacked public transcript gets late-bound private predicate commitments.
- PASS: `support_spoofer_suppressed_when_private_predicate_hidden` - Without the private predicate, support-aware spoofers must guess predicate bits.
- PASS: `leakage_boundary_explicit` - If predicate material leaks, the private-predicate protection degrades.
- FAIL: `hardware_or_backend_execution_present` - No real backend properties or hardware execution are used.
- FAIL: `cryptographic_soundness_proved` - This is an analytic pressure gate, not a cryptographic proof.
- FAIL: `protocol_soundness_proved` - The result adds a verifier-private burden but does not prove protocol soundness.
- PASS: `no_forbidden_claims` - The report keeps hardware, hardness, soundness, advantage, and BQP claims false.

## Claim Boundary

- Not hardware execution.
- Not cryptographic or protocol soundness.
- Not sampling hardness.
- Not quantum advantage.
- Not BQP separation.

## Validation

- Validation errors: 0
