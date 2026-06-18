#!/usr/bin/env python3
"""Build a B10-T1 missing-assumption theorem-note skeleton from B3/B5 pressure."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


METHOD = "b10_t1_missing_assumption_note_v0"
STATUS = "missing_assumption_note_not_dequantization_theorem"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_report(results_dir: Path) -> dict[str, Any]:
    comparison = read_json(results_dir / "B10_t1_b3_b5_denominator_boundary_comparison_v0.json")
    source_summary = comparison["summary"]
    source_claims = comparison["claim_boundary"]

    missing_assumptions = [
        {
            "id": "A1_asymptotic_family",
            "statement": (
                "The current B3/B5 evidence is a finite D5 table, not an asymptotic family with "
                "declared scaling of Hamiltonian construction, observable count, error, and condition parameters."
            ),
            "why_needed": "A theorem needs a family parameter and scaling law; finite denominator pressure is not a theorem.",
            "current_evidence": "B10 D5 B5 instances = 9; B10 D5 B3 FCI instances = 4.",
            "status": "missing",
        },
        {
            "id": "A2_access_model_equivalence",
            "statement": (
                "Classical and quantum algorithms must receive equivalent explicit, sparse, oracle, or sampling/query access."
            ),
            "why_needed": "A dequantization or separation note collapses if one side receives stronger access.",
            "current_evidence": "B10-T1 source-backed boundaries distinguish explicit I/O, oracle, and sampling-access regimes.",
            "status": "partially_specified_not_proved",
        },
        {
            "id": "A3_state_preparation_and_block_encoding_cost",
            "statement": (
                "Any candidate quantum response kernel must charge state preparation, block encoding, measurement, and optimizer-loop costs."
            ),
            "why_needed": "B3 loses after optimizer-loop accounting; B5 has no honestly costed quantum response kernel yet.",
            "current_evidence": (
                "B3 max optimizer-loop shots lower bound is "
                f"{source_summary['b3_max_optimizer_loop_total_shots_lower_bound']}; "
                "B5 positive-claim-ready is false."
            ),
            "status": "missing_for_positive_quantum_route",
        },
        {
            "id": "A4_strong_classical_denominator",
            "statement": (
                "The theorem note must compare against selected-CI/FCI, DMRG/MPS, embedding, or sampling-access baselines appropriate to each regime."
            ),
            "why_needed": "The current evidence is denominator pressure, not a universal lower bound.",
            "current_evidence": (
                "B3 selected-CI larger-basis denominator wins = "
                f"{source_summary['b3_selected_ci_larger_basis_denominator_beaten_count']}; "
                "B5 variational MPS/ALS rows beating seeded pressure = "
                f"{source_summary['b5_variational_mps_rows_beating_seeded_mps_pressure_reference']}."
            ),
            "status": "partially_satisfied_for_finite_instances",
        },
        {
            "id": "A5_sampling_access_or_dequantization_bridge",
            "statement": (
                "To become a dequantization theorem, the note must state whether B3/B5 observables admit sampling/query access "
                "or another classical simulation contract comparable to the quantum input model."
            ),
            "why_needed": "Without an access bridge, the result is only a negative boundary and not a dequantization theorem.",
            "current_evidence": "No B3/B5 sampling-access theorem or oracle-equivalence lemma exists in the portfolio.",
            "status": "missing",
        },
    ]

    theorem_skeletons = [
        {
            "id": "T1_finite_boundary_no_advantage_claim",
            "claim_type": "finite_negative_boundary",
            "informal_statement": (
                "Under the currently audited finite B3/B5 D5 evidence, no B3 reaction-dynamics, B5 strong-correlation, "
                "quantum-advantage, or BQP-separation claim is supported."
            ),
            "status": "supported_as_claim_policy_not_complexity_theorem",
            "depends_on": ["A3_state_preparation_and_block_encoding_cost", "A4_strong_classical_denominator"],
        },
        {
            "id": "T2_sampling_access_dequantization_candidate",
            "claim_type": "candidate_theorem_not_proved",
            "informal_statement": (
                "If the B3/B5 observable family admits sampling/query access with comparable state-preparation and observable access, "
                "then quantum speedup claims must be compared against quantum-inspired or tensor/embedding classical denominators."
            ),
            "status": "blocked_by_missing_A1_A2_A5",
            "depends_on": ["A1_asymptotic_family", "A2_access_model_equivalence", "A5_sampling_access_or_dequantization_bridge"],
        },
    ]

    proof_obligations = [
        "Define an asymptotic B3/B5 observable family rather than a finite table.",
        "Specify explicit, oracle, and sampling/query access contracts for both quantum and classical algorithms.",
        "Show whether B3/B5 state-preparation and observable access can be built without hiding linear or worse costs.",
        "State the best classical denominator family under the same access contract.",
        "Prove or refute that the quantum route improves the denominator after measurement and optimizer-loop costs.",
    ]

    validation_errors = []
    if source_summary.get("b3_selected_ci_larger_basis_denominator_beaten_count") != 0:
        validation_errors.append("B3 should not be treated as a negative boundary if denominator wins are nonzero")
    if source_summary.get("b5_positive_claim_ready") is not False:
        validation_errors.append("B5 should not be positive-ready in this missing-assumption note")
    if source_summary.get("bqp_separation_claimed") is not False:
        validation_errors.append("Source comparison must not claim BQP separation")
    if source_claims.get("quantum_advantage_claimed") is not False:
        validation_errors.append("Source comparison must not claim quantum advantage")
    if not any(row["status"] == "missing" for row in missing_assumptions):
        validation_errors.append("Missing-assumption note must expose at least one missing assumption")

    return {
        "benchmark_id": "B10",
        "problem_id": 11,
        "title": "B10-T1 Missing-Assumption Theorem Note",
        "version": "0.1",
        "status": STATUS,
        "method": METHOD,
        "source_target_id": "B10-T1",
        "dependency_benchmarks": ["B3", "B5", "B10"],
        "source_comparison_method": comparison["method"],
        "source_comparison_status": comparison["status"],
        "summary": {
            "theorem_skeleton_count": len(theorem_skeletons),
            "missing_assumption_count": len(missing_assumptions),
            "proof_obligation_count": len(proof_obligations),
            "source_route_count": source_summary["route_count"],
            "source_b3_demoted": source_summary["b3_demoted"],
            "source_b5_positive_claim_ready": source_summary["b5_positive_claim_ready"],
            "dequantization_theorem_proved": False,
            "sampling_access_theorem_proved": False,
            "bqp_separation_claimed": False,
            "quantum_advantage_claimed": False,
            "validation_error_count": len(validation_errors),
        },
        "theorem_skeletons": theorem_skeletons,
        "missing_assumptions": missing_assumptions,
        "proof_obligations": proof_obligations,
        "claim_boundary": {
            "dequantization_theorem_proved": False,
            "sampling_access_theorem_proved": False,
            "bqp_separation_claimed": False,
            "quantum_advantage_claimed": False,
            "what_is_supported": (
                "The current finite B3/B5 denominator evidence is strong enough to reject positive B3/B5/BQP claims "
                "under the audited route cards, and to define missing assumptions for a future theorem note."
            ),
            "what_is_not_supported": (
                "This is not a dequantization theorem, not a sampling-access theorem, not a BQP separation, "
                "and not a quantum advantage claim."
            ),
        },
        "next_required_artifacts": [
            "Define an asymptotic B3/B5 observable family with explicit access contracts.",
            "Prove or refute sampling/query access for the chosen B3/B5 observables.",
            "Upgrade B5 to production DMRG/MPS or an honestly costed quantum response kernel.",
            "Keep B3 demoted unless a multi-parameter or stronger measurement rescue beats denominators.",
        ],
        "validation_errors": validation_errors,
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# B10-T1 Missing-Assumption Theorem Note v0.1",
        "",
        f"- Status: {report['status']}",
        f"- Method: {report['method']}",
        f"- Source comparison: {report['source_comparison_method']}",
        f"- Theorem skeletons: {report['summary']['theorem_skeleton_count']}",
        f"- Missing assumptions: {report['summary']['missing_assumption_count']}",
        f"- Proof obligations: {report['summary']['proof_obligation_count']}",
        f"- Dequantization theorem proved: {report['summary']['dequantization_theorem_proved']}",
        f"- BQP separation claimed: {report['summary']['bqp_separation_claimed']}",
        f"- Validation errors: {report['validation_errors']}",
        "",
        "## Theorem Skeletons",
        "",
    ]
    for row in report["theorem_skeletons"]:
        lines.extend(
            [
                f"### {row['id']}",
                "",
                f"- Type: {row['claim_type']}",
                f"- Status: {row['status']}",
                f"- Statement: {row['informal_statement']}",
                f"- Depends on: {', '.join(row['depends_on'])}",
                "",
            ]
        )
    lines.extend(["## Missing Assumptions", ""])
    for row in report["missing_assumptions"]:
        lines.extend(
            [
                f"### {row['id']}",
                "",
                f"- Status: {row['status']}",
                f"- Statement: {row['statement']}",
                f"- Why needed: {row['why_needed']}",
                f"- Current evidence: {row['current_evidence']}",
                "",
            ]
        )
    lines.extend(["## Proof Obligations", ""])
    for item in report["proof_obligations"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Claim Boundary", ""])
    for key, value in report["claim_boundary"].items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B10_t1_missing_assumption_note_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B10_t1_missing_assumption_note.md"),
    )
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    report = build_report(args.results_dir)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(report, indent=2 if args.pretty else None, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_output.write_text(markdown(report), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "method": report["method"],
                **report["summary"],
                "validation_errors": report["validation_errors"],
            },
            indent=2 if args.pretty else None,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
