# B6/B5 Observable Row Intake Template Gate

Status: **observable_row_intake_template_open_missing_dft_b5_rows**

## Summary

- Method: `b6_observable_row_intake_template_gate_v0`
- Model status: `top_post_materials_mapped_to_observable_row_templates_no_rows_submitted`
- Intake requirements passed/failed: 6 / 2
- Failed intake requirement IDs: ['T6', 'T7']
- Template rows: 12
- DFT/B5 required key counts: 11 / 11
- Template table hash: `9585c5c697665c92759906e0060738d11d6710f2efbab9e1fef3e264a9a8c1ff`
- Submitted DFT/B5 rows: 0 / 0
- Accepted DFT/B5 rows: 0 / 0

## Row Templates

| Rank | Material | Family | DFT submitted | B5 submitted | Template hash |
|---:|---|---|---|---|---|
| 1 | monolayer_FeSe_STO_2012 | iron_chalcogenide | False | False | `6509e5e23825f69e18d60cf78f678a2d312c8b107c5983c28d6282e85ec8bf81` |
| 2 | FeSe_pressure_2009 | iron_chalcogenide | False | False | `9bb5470573beec89332152b152fb9b170d674f00bf82e9d8325a9f55d6a87d7b` |
| 3 | LaH10_2019 | hydride | False | False | `1e33b2ed9ed81ec0dd6e72ad79f4b3bc5276ae7dfbefca874d4d3756cfb27486` |
| 4 | YH6_2021 | hydride | False | False | `2da10acb6ec6795b01c9ebe841fde6c369c5f602b87a753c0e5f2eb687ece783` |
| 5 | H3S_2015 | hydride | False | False | `c3766daf231dd88793cb9c814cbb0bdf0a30913432b9791983de9836969547b2` |
| 6 | La3Ni2O7_pressure_2023 | nickelate | False | False | `e4b83d79c06be19ecf65ba5ee43260b200661605b9c1b350423c4d6884acd2fd` |
| 7 | CaH6_2022 | hydride | False | False | `503ef3f00af0acebc20ea11fc7f23e5a89666765475215c770d9519c635b459e` |
| 8 | NdNiO2_Sr_2019 | nickelate | False | False | `57d59d534729a1122eebe4ae3daf5f78f439139c1898fde34f23bd4abcffb7ae` |
| 9 | ZnFe2O4_neg | spinel_oxide | False | False | `fe0d496250664044f9dc6d7281d86c653582691fae4f2e4fd9b162b569be993c` |
| 10 | Y2Ti2O7_neg | pyrochlore | False | False | `824a57f034bd99e591f11f1da418848c58eda2845b128dee15e6e78eb0f8ea9d` |
| 11 | WSe2_neg | transition_metal_dichalcogenide | False | False | `db1799511393af5a5f40a7a90055be1b7e33c932fb57258f4bec80f03b191fc9` |
| 12 | Sr3Ru2O7_neg | ruthenate | False | False | `d8ba6af328c7875415a29a9f12ca6c93ee05401f58502844ca10c627056da6c3` |

## Requirement Results

- T1 [PASS]: Observable contract is open only on O5/O6
- T2 [PASS]: Backend replay source is stable and still missing observables
- T3 [PASS]: Twelve top-post replay materials are converted into row templates
- T4 [PASS]: DFT and B5 observable schemas are preserved
- T5 [PASS]: Source, formula, and replay hashes are preserved
- T6 [FAIL]: Submitted DFT observable rows exist
- T7 [FAIL]: Submitted B5-computed observable rows exist
- T8 [PASS]: Forbidden discovery, mechanism, and solution claims remain false

## Claim Boundary

- Supported: The top-post B6 replay materials are converted into row-level DFT and B5 observable intake templates with preserved replay hashes.
- Not supported: No DFT rows, B5 computed-observable rows, material discovery, mechanism solution, or B6 solution claim is established.
- Next gate: Submit DFT and B5 observable rows for the templated material_id set while preserving source_table_hash, replay_formula_hash, and replay_table_hash.
- material_discovery_claimed: False
- mechanism_solved: False
- solution_claimed: False

## Validation

- validation_error_count: 0
