# B1/B7 Cone 01 Dressing Absorption Gate

Status: `cone01_dressing_absorption_negative_gate`

This artifact tests the next obligation after the numerical local-dressing search: whether the off-grid local dressing can be exactified to the pi/4 grid, shared across the three packets, or counted as an absorption certificate. It is a negative resource-accounting gate.

## Summary

- Pattern groups: `3`
- Covered invariant-flat occurrences: `11`
- Source local-dressing exact passes: `3`
- Pi/4 projection exact passes: `0`
- Unique pi/4 grid signatures: `3`
- Total off-grid local dressing parameters: `26`
- Total near-grid local dressing parameters: `2`
- Single-parameter snap exact passes: `0`
- Accepted occurrence removal: `0`
- Missing occurrences after this gate: `30`

## Pattern Results

| Pattern | Occurrences | Grid | Source residual | Pi/4 projected residual | Off-grid params | Near-grid params | Best single snap residual | Accepted removal |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| flat_pattern_01 | 8 | `-7*pi/4` | `3.52178773379e-16` | `0.307153057534` | `9` | `0` | `0.0361874700951` | `0` |
| flat_pattern_02 | 2 | `-7*pi/4` | `4.71027737605e-16` | `0.300042625997` | `9` | `1` | `0.0092979710166` | `0` |
| flat_pattern_03 | 1 | `-4*pi/4` | `3.92032153735e-16` | `0.84155259636` | `8` | `1` | `0.00594448159448` | `0` |

## Claim Boundary

- The three numerical dressings are not accepted as resource savings after pi/4-grid exactification checks.
- The three patterns have three distinct grid signatures, so this gate does not find a shared exact dressing object.
- Single-parameter snapping does not produce an exact-pass certificate.
- No absorption certificate, exactification certificate, semantic rewrite, resource saving, or B7 ledger improvement is claimed.

Validation error count: `0`
