#!/usr/bin/env python3
"""Compare B3/B5 denominator pressure for the B10-T1 boundary track."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


METHOD = "b10_t1_b3_b5_denominator_boundary_comparison_v0"
STATUS = "b3_b5_denominator_boundary_comparison_not_bqp_separation"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_inputs(results_dir: Path) -> dict[str, dict[str, Any]]:
    files = {
        "b3_cross_molecule_pressure": "B3_cross_molecule_ucc_adapt_pressure_v0.json",
        "b5_boundary_field": "B5_boundary_field_embedding_baseline_v0.json",
        "b5_non_oracle": "B5_non_oracle_response_embedding_baseline_v0.json",
        "b5_seeded_mps": "B5_mps_truncation_response_reference_v0.json",
        "b5_variational_mps_als": "B5_variational_mps_als_response_reference_v0.json",
        "b10_d5_b5_denominator": "B10_t1_d5_observable_denominator_table_v0.json",
        "b10_d5_b3_reaction": "B10_t1_d5_b3_reaction_observable_table_v0.json",
        "b10_d5_b3_fci": "B10_t1_d5_b3_fci_reference_table_v0.json",
    }
    return {key: read_json(results_dir / filename) for key, filename in files.items()}


def summary(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("summary", {})


def build_report(results_dir: Path) -> dict[str, Any]:
    inputs = load_inputs(results_dir)
    b3_pressure = summary(inputs["b3_cross_molecule_pressure"])
    b5_boundary = summary(inputs["b5_boundary_field"])
    b5_non_oracle = summary(inputs["b5_non_oracle"])
    b5_seeded = summary(inputs["b5_seeded_mps"])
    b5_variational = summary(inputs["b5_variational_mps_als"])
    b10_b5 = summary(inputs["b10_d5_b5_denominator"])
    b10_b3_reaction = summary(inputs["b10_d5_b3_reaction"])
    b10_b3_fci = summary(inputs["b10_d5_b3_fci"])

    route_cards = [
        {
            "route_id": "B3_one_parameter_ucc_adapt_qwc",
            "dependency_benchmark": "B3",
            "current_status": "negative_boundary",
            "evidence": (
                "Cross-molecule UCC/ADAPT pressure keeps selected-CI larger-basis denominator "
                "wins at zero after optimizer-loop accounting."
            ),
            "primary_metric": "selected_ci_larger_basis_denominator_beaten_count",
            "primary_value": b3_pressure.get("selected_ci_larger_basis_denominator_beaten_count"),
            "blocking_cost": {
                "max_optimizer_loop_total_shots_lower_bound": b3_pressure.get(
                    "max_optimizer_loop_total_shots_lower_bound"
                ),
                "max_optimizer_loop_two_qubit_executions_lower_bound": b3_pressure.get(
                    "max_optimizer_loop_two_qubit_executions_lower_bound"
                ),
            },
            "next_gate": "Only reopen B3 as a positive route with multi-parameter covariance or stronger-than-QWC measurement.",
        },
        {
            "route_id": "B5_small_cluster_embedding",
            "dependency_benchmark": "B5",
            "current_status": "classical_denominator_improved_not_quantum_win",
            "evidence": (
                "Non-oracle cluster/embedding selection beats the prior oracle-tuned boundary-field "
                "denominator in four rows, but remains a classical denominator."
            ),
            "primary_metric": "non_oracle_rows_beating_oracle_boundary_field",
            "primary_value": b5_non_oracle.get("non_oracle_rows_beating_oracle_boundary_field"),
            "mean_relative_response_error": b5_non_oracle.get("selected_mean_relative_response_error"),
            "max_relative_response_error": b5_non_oracle.get("selected_max_relative_response_error"),
            "next_gate": "Compare a real quantum response kernel against the non-oracle denominator after full costs.",
        },
        {
            "route_id": "B5_exact_state_seeded_mps_pressure",
            "dependency_benchmark": "B5",
            "current_status": "strong_classical_pressure_reference_not_deployable_dmrg",
            "evidence": (
                "Exact-state-seeded MPS/Schmidt truncation gives a very strong pressure reference, "
                "but uses exact-state seeding and is not a production tensor solver."
            ),
            "primary_metric": "mps_rows_beating_non_oracle_embedding",
            "primary_value": b5_seeded.get("mps_rows_beating_non_oracle_embedding"),
            "mean_relative_response_error": b5_seeded.get("selected_mean_relative_response_error"),
            "max_relative_response_error": b5_seeded.get("selected_max_relative_response_error"),
            "next_gate": "Replace seeded pressure with mature variational DMRG/MPS or an honestly costed quantum kernel.",
        },
        {
            "route_id": "B5_variational_mps_als_prototype",
            "dependency_benchmark": "B5",
            "current_status": "prototype_not_production_dmrg_not_quantum_win",
            "evidence": (
                "Non-exact-state-seeded MPS/ALS improves over small clusters but beats zero rows of "
                "the exact-state-seeded MPS pressure reference."
            ),
            "primary_metric": "variational_mps_rows_beating_seeded_mps_pressure_reference",
            "primary_value": b5_variational.get("variational_mps_rows_beating_seeded_mps_pressure_reference"),
            "mean_relative_response_error": b5_variational.get("selected_mean_relative_response_error"),
            "max_relative_response_error": b5_variational.get("selected_max_relative_response_error"),
            "next_gate": "Upgrade to canonical-environment production DMRG/MPS before making a B5 positive claim.",
        },
    ]

    validation_errors = []
    if b3_pressure.get("selected_ci_larger_basis_denominator_beaten_count") != 0:
        validation_errors.append("B3 route should not be marked demoted if denominator wins are nonzero")
    if b3_pressure.get("demotion_recommended") is not True:
        validation_errors.append("B3 cross-molecule pressure must recommend demotion for this comparison")
    if b5_variational.get("variational_mps_rows_beating_seeded_mps_pressure_reference") != 0:
        validation_errors.append("B5 variational MPS/ALS should not be marked blocked if it beats seeded pressure")
    if inputs["b5_variational_mps_als"].get("production_dmrg") is not False:
        validation_errors.append("B5 variational MPS/ALS input must not claim production DMRG")
    if inputs["b5_variational_mps_als"].get("explicit_not_quantum_advantage") is not True:
        validation_errors.append("B5 variational MPS/ALS input must explicitly avoid quantum advantage claims")
    if inputs["b10_d5_b5_denominator"].get("explicit_not_bqp_separation") is not True:
        validation_errors.append("B10 D5 B5 denominator must explicitly avoid BQP separation claims")
    if inputs["b10_d5_b3_fci"].get("explicit_not_bqp_separation") is not True:
        validation_errors.append("B10 D5 B3 FCI denominator must explicitly avoid BQP separation claims")

    return {
        "benchmark_id": "B10",
        "problem_id": 11,
        "title": "B10-T1 B3/B5 Denominator Boundary Comparison",
        "version": "0.1",
        "status": STATUS,
        "method": METHOD,
        "source_target_id": "B10-T1",
        "dependency_benchmarks": ["B3", "B5", "B10"],
        "source_methods": {
            "b3_cross_molecule_pressure": inputs["b3_cross_molecule_pressure"].get("method"),
            "b5_boundary_field": inputs["b5_boundary_field"].get("method"),
            "b5_non_oracle": inputs["b5_non_oracle"].get("method"),
            "b5_seeded_mps": inputs["b5_seeded_mps"].get("method"),
            "b5_variational_mps_als": inputs["b5_variational_mps_als"].get("method"),
            "b10_d5_b5_denominator": inputs["b10_d5_b5_denominator"].get("method"),
            "b10_d5_b3_reaction": inputs["b10_d5_b3_reaction"].get("method"),
            "b10_d5_b3_fci": inputs["b10_d5_b3_fci"].get("method"),
        },
        "summary": {
            "route_count": len(route_cards),
            "negative_boundary_route_count": sum(1 for row in route_cards if row["current_status"] == "negative_boundary"),
            "b3_selected_ci_larger_basis_denominator_beaten_count": b3_pressure.get(
                "selected_ci_larger_basis_denominator_beaten_count"
            ),
            "b3_max_optimizer_loop_total_shots_lower_bound": b3_pressure.get(
                "max_optimizer_loop_total_shots_lower_bound"
            ),
            "b3_max_optimizer_loop_two_qubit_executions_lower_bound": b3_pressure.get(
                "max_optimizer_loop_two_qubit_executions_lower_bound"
            ),
            "b5_non_oracle_rows_beating_oracle_boundary_field": b5_non_oracle.get(
                "non_oracle_rows_beating_oracle_boundary_field"
            ),
            "b5_seeded_mps_rows_beating_non_oracle_embedding": b5_seeded.get(
                "mps_rows_beating_non_oracle_embedding"
            ),
            "b5_variational_mps_rows_beating_seeded_mps_pressure_reference": b5_variational.get(
                "variational_mps_rows_beating_seeded_mps_pressure_reference"
            ),
            "b10_d5_b5_instance_count": b10_b5.get("instance_count"),
            "b10_d5_b5_max_hilbert_dimension": b10_b5.get("max_hilbert_dimension"),
            "b10_d5_b3_reaction_instance_count": b10_b3_reaction.get("instance_count"),
            "b10_d5_b3_fci_instance_count": b10_b3_fci.get("instance_count"),
            "b10_d5_b3_fci_max_abs_fci_derivative_shift_vs_rhf": b10_b3_fci.get(
                "max_abs_fci_derivative_shift_vs_rhf"
            ),
            "b3_demoted": True,
            "b5_positive_claim_ready": False,
            "bqp_separation_claimed": False,
            "quantum_advantage_claimed": False,
            "validation_error_count": len(validation_errors),
        },
        "route_cards": route_cards,
        "claim_boundary": {
            "bqp_separation_claimed": False,
            "quantum_advantage_claimed": False,
            "b3_reaction_dynamics_solution_claimed": False,
            "b5_strong_correlation_solution_claimed": False,
            "production_dmrg_claimed": False,
            "what_is_supported": (
                "The current B3 one-parameter UCC/ADAPT route is negative-boundary evidence under "
                "selected-CI/FCI and optimizer-loop pressure; B5 has strong classical denominator "
                "pressure but no production DMRG or quantum response-kernel win."
            ),
            "what_is_not_supported": (
                "This comparison is not a BQP/classical separation, not a dequantization theorem, "
                "not a quantum advantage result, and not a solution of B3 or B5."
            ),
        },
        "next_required_artifacts": [
            "T-B3-012 multi-parameter chemistry rescue or stronger-than-QWC measurement",
            "T-B5-003 production DMRG/MPS response reference",
            "costed B5 quantum response kernel compared against the D5 table",
            "B10-T1 dequantization/sampling-access theorem note if both B3 and B5 stay negative",
        ],
        "validation_errors": validation_errors,
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# B10-T1 B3/B5 Denominator Boundary Comparison v0.1",
        "",
        f"- Status: {report['status']}",
        f"- Method: {report['method']}",
        f"- Source target: {report['source_target_id']}",
        f"- Routes compared: {report['summary']['route_count']}",
        f"- B3 denominator wins: {report['summary']['b3_selected_ci_larger_basis_denominator_beaten_count']}",
        f"- B3 max optimizer-loop shots lower bound: {report['summary']['b3_max_optimizer_loop_total_shots_lower_bound']}",
        f"- B5 non-oracle rows beating oracle boundary field: {report['summary']['b5_non_oracle_rows_beating_oracle_boundary_field']}",
        f"- B5 seeded MPS rows beating non-oracle embedding: {report['summary']['b5_seeded_mps_rows_beating_non_oracle_embedding']}",
        f"- B5 variational MPS/ALS rows beating seeded MPS pressure: {report['summary']['b5_variational_mps_rows_beating_seeded_mps_pressure_reference']}",
        f"- Validation errors: {report['validation_errors']}",
        "",
        "## Route Cards",
        "",
        "| route | status | primary metric | value | next gate |",
        "|---|---|---|---:|---|",
    ]
    for row in report["route_cards"]:
        lines.append(
            f"| {row['route_id']} | {row['current_status']} | {row['primary_metric']} | "
            f"{row['primary_value']} | {row['next_gate']} |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
        ]
    )
    for key, value in report["claim_boundary"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Next Required Artifacts", ""])
    for item in report["next_required_artifacts"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B10_t1_b3_b5_denominator_boundary_comparison_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B10_t1_b3_b5_denominator_boundary_comparison.md"),
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
