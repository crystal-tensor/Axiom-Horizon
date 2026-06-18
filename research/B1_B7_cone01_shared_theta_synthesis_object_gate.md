# B1/B7 Cone_01 Shared-Theta Synthesis Object Proposal Gate

Status: `cone01_shared_theta_synthesis_object_proposal`

This artifact converts the four repeated cone_01 theta groups into explicit shared synthesis object proposals. It is an object-existence step only. The objects do not yet have replay verification, physical layout, factory amortization, an error budget, or B7 ledger acceptance.

It is not a rewrite certificate, not a semantic certificate, not a physical resource-saving claim, and not a B7 resource improvement.

## Summary

- Candidate windows: `35`
- Shared synthesis objects: `4`
- Covered occurrences: `35`
- Duplicate theta occurrences: `31`
- Optimistic cache proxy-T reuse: `620`
- Shared object existence gate passed: `True`
- All candidate windows covered: `True`
- Semantic replay verified objects: `0`
- Physical layout assigned objects: `0`
- B7 ledger accepted objects: `0`
- Occurrence-ledger removed occurrences: `0`
- Cost model accepted: `False`
- Validation errors: `0`

## Shared Objects

| object | theta | source occurrences | duplicate occurrences | anchor line | consumers | optimistic proxy-T |
|---|---:|---:|---:|---:|---:|---:|
| `cone01_shared_theta_01` | `0.420540811611` | 16 | 15 | 94 | 15 | 300 |
| `cone01_shared_theta_02` | `0.364857351786` | 10 | 9 | 29 | 9 | 180 |
| `cone01_shared_theta_03` | `0.99803486463` | 6 | 5 | 139 | 5 | 100 |
| `cone01_shared_theta_04` | `2.813468447841` | 3 | 2 | 462 | 2 | 40 |

## Interpretation

This closes one bookkeeping gap in the physical theta-sharing route: the project now has concrete shared object proposals rather than only a theta-group count. The hard gates remain ahead. The next admissible step is a replay verifier for these objects across the covered windows, followed by layout, factory, error-budget, independent-baseline, and refreshed-ledger checks.
