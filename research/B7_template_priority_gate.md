# B7 Template Priority Gate v0.1

Status: **template_priority_gate_no_single_one_angle_template_clears_gcm_h6**

This gate ranks the retained nonlocal templates against the gcm_h6 1.20x
resource threshold. It is not a new rewrite, not a symbolic proof, not a
physical layout result, and not a global lower bound.

## Summary

- Source scan: `results/B7_nonlocal_template_block_scan_v0.json`
- Templates evaluated: 12
- gcm_h6 1.20x one-sided target: 30 removed arbitrary occurrences / 600 proxy-T ledger units
- Single-template one-angle clear count: 0
- Best template: `w8_21` with 20 nonoverlap occurrences
- Best-template required removals per occurrence: 2
- Best-template one-angle shortfall: 10 arbitrary occurrences
- Prior `w8_21` optimizer runs: 43480
- Prior `w8_21` exact rewrite found: False
- All-variant 1.20x cleared by gcm_h6-only removals: False

## Template Priority Table

| Template | Width | Occurrences | Arbitrary/occ | One-angle clears? | Required arbitrary/occ | Physical covered | Certificate? |
|---|---:|---:|---:|---|---:|---:|---|
| w8_21 | 8 | 20 | 5 | False | 2 | 100 | False |
| w64_2396 | 64 | 7 | 10 | False | 5 | 70 | False |
| w32_1701 | 32 | 10 | 7 | False | 3 | 70 | False |
| w16_790 | 16 | 11 | 6 | False | 3 | 66 | False |
| w48_2317 | 48 | 8 | 8 | False | 4 | 64 | False |
| w64_2389 | 64 | 7 | 9 | False | 5 | 63 | False |
| w64_2390 | 64 | 7 | 9 | False | 5 | 63 | False |
| w64_2391 | 64 | 7 | 9 | False | 5 | 63 | False |
| w64_2393 | 64 | 7 | 9 | False | 5 | 63 | False |
| w64_2394 | 64 | 7 | 9 | False | 5 | 63 | False |
| w64_2395 | 64 | 7 | 9 | False | 5 | 63 | False |
| w64_2397 | 64 | 7 | 9 | False | 5 | 63 | False |

## Claim Boundary

- No new occurrence-removing rewrite is claimed.
- No physical resource reduction is claimed.
- No global KAK or two-qubit lower bound is claimed.
- The all-variant portfolio 1.20x gate remains false.

## Next Gate

For `T-B7-010`, a useful PR must provide one of three things:

1. a symbolic KAK/Clifford-scaffold proof for `w8_21`,
2. a certified occurrence-removing rewrite for `gcm_h6` that removes at least the required per-occurrence arbitrary rotations, or
3. a B1 T-resource improvement that moves the B7 min row without counting repeated templates as savings.
