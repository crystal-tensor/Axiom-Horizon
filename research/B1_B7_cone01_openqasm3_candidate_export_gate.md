# B1/B7 cone_01 OpenQASM 3 Candidate Export Gate

Status: `cone01_openqasm3_candidate_exported_not_replay_certified`

This artifact consumes the legacy-dialect T-B1-004av candidate and exports an OpenQASM 3.0 candidate artifact for the line-268 plus line-1381 non-overlap patch subset. It is a dialect and portability gate, not a new resource-saving claim.

## Summary

- Source candidate: `results/B1_B7_cone01_qasm2_candidate_rewrite_gate/gcm_h6_line268_line1381_candidate.qasm`
- OpenQASM 3 candidate: `results/B1_B7_cone01_openqasm3_candidate_export_gate/gcm_h6_line268_line1381_candidate_openqasm3.qasm`
- Source / export dialect: `OPENQASM 2.0` / `OPENQASM 3.0`
- Header valid / stdgates include present: `True` / `True`
- Legacy qelib/qreg/creg/u3/measure-arrow remnants: `False` / `False` / `False` / `False`
- Source / OpenQASM 3 operation counts: `{'u3_or_U': 487, 'rz': 601, 'cx': 789, 'measure': 1, 'other_operation': 0}` / `{'u3_or_U': 487, 'rz': 601, 'cx': 789, 'measure': 1, 'other_operation': 0}`
- Operation counts preserved: `True`
- u3 -> U conversions / measurement conversions: `487` / `1`
- Candidate CNOT count / delta: `789` / `6`
- Accepted OpenQASM 3 export artifacts: `1`
- Accepted replay / local-U3 pricing / occurrence / proxy-T reduction: `0` / `0` / `0` / `0`
- Validation errors: `0`

## Claim Boundary

The selected line-268 plus line-1381 candidate now has an OpenQASM 3.0 export artifact with preserved operation counts and valid modern headers.

Unsupported claims:

- The export is not a new full-circuit replay proof.
- The export does not recover the dropped line-1378 overlap delta.
- The export does not price or eliminate the remaining off-grid local-U3 burden.
- The export does not create B7 occurrence, proxy-T, or space-time-volume credit.

## Next Required Gate

The next gate must parse or replay this OpenQASM 3 artifact through a modern toolchain, then connect it to symbolic equivalence or local-U3 pricing before any B7 resource credit is allowed.
