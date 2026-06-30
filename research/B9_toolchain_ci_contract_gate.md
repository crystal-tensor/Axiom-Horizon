# B9 Lean/Lake CI Contract Gate

Status: **toolchain_ci_contract_workflow_scope_blocked**

T-B9-004e adds a GitHub Actions handoff for the B9 Lean/Lake scaffold. It defines how an external runner should install the pinned Lean toolchain, expose Lake, run `lake update`, check the B9 Lean module, and refresh the B9 proof-environment gates. This is a CI contract, not a recorded proof-assistant success.

## Metrics

- Workflow template: `research/ci/b9-lean-proof-scaffold.yml`
- Active workflow present locally: `False`
- CI contract requirements passed / failed: 7 / 3
- Failed CI contract requirement IDs: `['C2', 'C3', 'C10']`

## Requirements

| ID | Pass | Requirement | Evidence |
| --- | --- | --- | --- |
| C1 | yes | B9 Lean workflow template exists | research/ci/b9-lean-proof-scaffold.yml |
| C2 | no | active B9 Lean workflow is installed | .github/workflows/b9-lean-proof-scaffold.yml |
| C3 | no | active workflow matches the reviewed template | active workflow content must be byte-identical to research/ci template |
| C4 | yes | workflow is scoped to B9 proof files | paths include B9, proof_skeletons, tools, results, and benchmark |
| C5 | yes | workflow installs pinned toolchain from lean-toolchain | toolchain=leanprover/lean4:v4.12.0 |
| C6 | yes | workflow exposes both Lean and Lake version probes | lean --version / lake --version |
| C7 | yes | workflow runs Lake dependency resolution | lake update with mathlib4 dependency |
| C8 | yes | workflow checks the B9 Lean module | B9/ClusterStabilizer/WidthLocality.lean |
| C9 | yes | workflow refreshes B9 proof-environment gates | readiness, contract, and scaffold refresh commands |
| C10 | no | active remote CI run artifact is present | no active workflow or remote CI run artifact is recorded; pushing .github/workflows/b9-lean-proof-scaffold.yml requires a token with workflow scope |

## Claim Boundary

- The CI handoff template exists and is scoped to B9 proof files.
- Installing the reviewed template as `.github/workflows/b9-lean-proof-scaffold.yml` requires a token with `workflow` scope.
- No remote CI run artifact is recorded yet.
- No proof-assistant checked theorem is claimed.
- No Quantum PCP, NLTS, or global gap-amplification theorem is claimed.
