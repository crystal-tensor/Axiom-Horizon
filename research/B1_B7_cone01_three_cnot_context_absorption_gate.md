# B1/B7 cone_01 Three-CNOT Context-Absorption Gate

- Method: `b1_b7_cone01_three_cnot_context_absorption_gate_v0`
- Status: `cone01_three_cnot_context_absorption_not_accepted`
- Model status: `best_three_cnot_candidate_has_no_single_step_context_absorption`
- Workload: `qasmbench_medium_exact/gcm_h6.qasm`
- Source pricing result: `results/B1_B7_cone01_union_region_three_cnot_pricing_screen_gate_v0.json`
- Selected 3-CNOT sequence: `10-10-01`
- Selected off-grid parameters / proxy-T pressure: `18` / `360`
- Current line-1381 boundary: `5` / `100`
- Inventory rotation arguments: `2049`
- Same-support context rotation arguments: `44`
- Inventory exact / abs-match parameter counts: `0` / `0`
- Same-support / context abs-match parameter counts: `0` / `0`
- One-step context grid-cancellation exact parameter count: `0`
- Best one-step grid-cancellation error range: `0.000655799901145393` - `0.0945879123733615`
- B7 ledger improvement claimed: `False`

## Claim Boundary

For the best-priced exact 3-CNOT union-region candidate, this gate checks whether any off-pi/4 local-U3 parameter has exact/absolute inventory matches, same-support context matches, or one-step same-support context cancellation back to the pi/4 grid.

Unsupported claims:
- This is not a symbolic multi-rotation absorption theorem.
- This is not a full-circuit replay or QASM patch certificate.
- This does not accept the 3-CNOT route as lower cost than the current line-1381 boundary.
- This does not accept occurrence removal, proxy-T reduction, or B7 ledger improvement.

## Parameter Rows

- parameter `2`: distance-to-grid `0.107717786144792`, inventory abs `0`, context abs `0`, best one-step grid error `0.061469272120072915`
- parameter `3`: distance-to-grid `0.049268787187301655`, inventory abs `0`, context abs `0`, best one-step grid error `0.049268787187301655`
- parameter `4`: distance-to-grid `0.20263827019273517`, inventory abs `0`, context abs `0`, best one-step grid error `0.03345121192787026`
- parameter `5`: distance-to-grid `0.29840289327092995`, inventory abs `0`, context abs `0`, best one-step grid error `0.06645445851534726`
- parameter `7`: distance-to-grid `0.37053752337036894`, inventory abs `0`, context abs `0`, best one-step grid error `0.005680171584091287`
- parameter `8`: distance-to-grid `0.37053752337036716`, inventory abs `0`, context abs `0`, best one-step grid error `0.005680171584089955`
- parameter `9`: distance-to-grid `0.002337221774992404`, inventory abs `0`, context abs `0`, best one-step grid error `0.00233722177499196`
- parameter `10`: distance-to-grid `0.3735785378635299`, inventory abs `0`, context abs `0`, best one-step grid error `0.008721186077252696`
- parameter `11`: distance-to-grid `0.0287602000315772`, inventory abs `0`, context abs `0`, best one-step grid error `0.0287602000315772`
- parameter `13`: distance-to-grid `0.0006557999011458371`, inventory abs `0`, context abs `0`, best one-step grid error `0.000655799901145393`
- parameter `15`: distance-to-grid `0.14140733848588738`, inventory abs `0`, context abs `0`, best one-step grid error `0.02777971977897753`
- parameter `16`: distance-to-grid `0.21383848505309366`, inventory abs `0`, context abs `0`, best one-step grid error `0.044651426788228754`
- parameter `17`: distance-to-grid `0.3724229125058178`, inventory abs `0`, context abs `0`, best one-step grid error `0.0075655607195406205`
- parameter `19`: distance-to-grid `0.2637749706382264`, inventory abs `0`, context abs `0`, best one-step grid error `0.0945879123733615`
- parameter `20`: distance-to-grid `0.1567129843945816`, inventory abs `0`, context abs `0`, best one-step grid error `0.01247407387028332`
- parameter `21`: distance-to-grid `0.2745158601919413`, inventory abs `0`, context abs `0`, best one-step grid error `0.09034149159433591`
- parameter `22`: distance-to-grid `0.23866057669699803`, inventory abs `0`, context abs `0`, best one-step grid error `0.06947351843213312`
- parameter `23`: distance-to-grid `0.27546653427260637`, inventory abs `0`, context abs `0`, best one-step grid error `0.08939081751367084`
