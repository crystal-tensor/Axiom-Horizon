# B1/B7 Cone_01 Theta-Sharing Physical Cost-Model Gate

Status: `cone01_theta_sharing_cost_model_not_accepted`

This artifact asks whether the repeated-theta cache signal from T-B1-004f can already be promoted into a physical B7 cost model. The answer is no. A shared synthesis object proposal now exists for the four theta groups, but the current evidence still lacks replay certificates, layout, factory amortization, error budget, independent baseline, and refreshed B7 ledger.

It is not a rewrite certificate, not a resource-saving claim, and not a physical cost-model acceptance.

## Summary

- Candidate windows: `35`
- Distinct theta groups: `4`
- Duplicate theta occurrences: `31`
- Optimistic cache proxy-T signal: `620`
- Target proxy-T reduction: `600`
- Optimistic cache signal present: `True`
- Shared synthesis object proposals: `4`
- Shared object existence gate passed: `True`
- Acceptance gates passed / total: `1` / `8`
- Cost model accepted: `False`
- B7 ledger proxy-T reduction after cost model: `0`
- Additional occurrence certificates required: `30`
- Additional cost-model gates required: `7`
- Validation errors: `0`

## Acceptance Gates

| gate | requirement | current evidence | required evidence | passed |
|---|---|---:|---:|---|
| CM-01 | At least 30 replayable occurrence-removing semantic certificates. | `0` | `30` | `False` |
| CM-02 | A shared synthesis object that replaces repeated theta occurrences, not only a classical template label. | `4` | `4` | `True` |
| CM-03 | A replay verifier for the shared-theta object across all affected windows. | `False` | `True` | `False` |
| CM-04 | An explicit layout/routing model showing where the shared object lives and how windows consume it. | `False` | `True` | `False` |
| CM-05 | A factory-amortization model proving lower T-factory pressure under the shared object. | `False` | `True` | `False` |
| CM-06 | A synthesis-error and correlation budget for shared theta reuse. | `False` | `True` | `False` |
| CM-07 | An independent baseline showing cache-only accounting is not double-counting occurrence cost. | `False` | `True` | `False` |
| CM-08 | A refreshed B7 FT ledger that accepts the model and improves the gcm_h6 min row. | `False` | `True` | `False` |

## Interpretation

The repeated-theta structure is valuable because it identifies where a future physical-sharing proposal would have leverage. The shared object proposal closes the object-existence gap, but it is not enough by itself. A future PR must satisfy the remaining gates, or bypass the cost-model route by producing 30 occurrence-removing certificates.
