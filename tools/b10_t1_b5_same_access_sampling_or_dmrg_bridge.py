#!/usr/bin/env python3
"""Build a B10-T1 B5 same-access sampling-or-DMRG bridge note."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


METHOD = "b10_t1_b5_same_access_sampling_or_dmrg_bridge_v0"
STATUS = "b5_same_access_sampling_oracle_not_constructed_dmrg_required"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_report(results_dir: Path) -> dict[str, Any]:
    access = read_json(results_dir / "B10_t1_asymptotic_access_contract_v0.json")
    d5_table = read_json(results_dir / "B10_t1_d5_observable_denominator_table_v0.json")
    non_oracle = read_json(results_dir / "B5_non_oracle_response_embedding_baseline_v0.json")
    seeded_mps = read_json(results_dir / "B5_mps_truncation_response_reference_v0.json")
    var_mps = read_json(results_dir / "B5_variational_mps_als_response_reference_v0.json")

    d5_summary = d5_table["summary"]
    non_oracle_summary = non_oracle["summary"]
    seeded_summary = seeded_mps["summary"]
    var_summary = var_mps["summary"]

    denominator_ladder = [
        {
            "id": "D1_explicit_d5_cg_response",
            "access_mode": "explicit",
            "status": "same_input_denominator_instantiated",
            "mean_relative_response_error": None,
            "max_relative_response_error": d5_summary["max_relative_residual"],
            "resource_proxy": d5_summary["max_matvec_equivalent_ops"],
            "claim_boundary": "Exact small D5 denominator, not a scalable response solution.",
        },
        {
            "id": "D2_non_oracle_embedding",
            "access_mode": "explicit_predeclared_classical_denominator",
            "status": "non_oracle_denominator_instantiated",
            "mean_relative_response_error": non_oracle_summary["selected_mean_relative_response_error"],
            "max_relative_response_error": non_oracle_summary["selected_max_relative_response_error"],
            "resource_proxy": non_oracle_summary["max_selected_cluster_hilbert_dimension"],
            "claim_boundary": "Predeclared embedding denominator, not quantum response.",
        },
        {
            "id": "D3_exact_state_seeded_mps_pressure",
            "access_mode": "mps_pressure_reference_not_deployable",
            "status": "strong_pressure_reference_not_production_dmrg",
            "mean_relative_response_error": seeded_summary["selected_mean_relative_response_error"],
            "max_relative_response_error": seeded_summary["selected_max_relative_response_error"],
            "resource_proxy": seeded_summary["selected_bond_dimension"],
            "claim_boundary": "Exact-state seeded MPS pressure, not variational DMRG.",
        },
        {
            "id": "D4_variational_mps_als_prototype",
            "access_mode": "variational_mps_prototype",
            "status": "nonproduction_dmrg_prototype",
            "mean_relative_response_error": var_summary["selected_mean_relative_response_error"],
            "max_relative_response_error": var_summary["selected_max_relative_response_error"],
            "resource_proxy": max(var_summary["selected_bond_dimensions"]),
            "claim_boundary": "One-site MPS/ALS prototype, not production DMRG.",
        },
    ]

    sampling_oracle_requirements = [
        {
            "id": "S1_response_observable_sampler",
            "requirement": "Construct samples whose expectation estimates the same density-response observable and eta/tolerance as the D5 table.",
            "current_status": "missing",
            "blocks_sampling_bridge": True,
        },
        {
            "id": "S2_preparation_or_mixing_cost",
            "requirement": "Charge preparation, thermalization, tensor sampling, or quantum state-preparation cost under the same input model.",
            "current_status": "missing",
            "blocks_sampling_bridge": True,
        },
        {
            "id": "S3_variance_and_confidence_certificate",
            "requirement": "Provide variance, confidence, and failure-probability accounting for the response estimator.",
            "current_status": "missing",
            "blocks_sampling_bridge": True,
        },
        {
            "id": "S4_same_access_classical_denominator",
            "requirement": "Compare against explicit, embedding, MPS/DMRG, or sampling-access classical denominators receiving no weaker access.",
            "current_status": "partially_satisfied_by_finite_denominators",
            "blocks_sampling_bridge": True,
        },
        {
            "id": "S5_positive_kernel_after_full_costs",
            "requirement": "Show a candidate quantum or sampling response kernel beats the best same-access denominator after full costs.",
            "current_status": "refuted_for_current_portfolio_evidence",
            "blocks_sampling_bridge": True,
        },
    ]

    bridge_decisions = [
        {
            "access_mode": "explicit",
            "decision": "classical_denominator_available",
            "reason": "D5 CG response and non-oracle embedding denominators are explicit-input artifacts.",
        },
        {
            "access_mode": "sampling_or_query_access",
            "decision": "not_constructed",
            "reason": "No sampler, variance certificate, or preparation/mixing cost exists for the B5 response observable.",
        },
        {
            "access_mode": "mps_dmrg_denominator",
            "decision": "production_dmrg_required_next",
            "reason": "Exact-state-seeded MPS is strong pressure but not deployable; variational MPS/ALS is nonproduction and loses to seeded pressure.",
        },
        {
            "access_mode": "quantum_response_kernel",
            "decision": "not_positive_ready",
            "reason": "No state-preparation, measurement, optimizer-loop, or response-kernel costed comparison beats the same-access denominator ladder.",
        },
    ]

    validation_errors = []
    access_summary = access["summary"]
    if access_summary.get("sampling_access_bridge_refuted_for_current_evidence") is not True:
        validation_errors.append("source access contract must refute current sampling bridge")
    if seeded_summary.get("mps_rows_beating_non_oracle_embedding", 0) <= 0:
        validation_errors.append("seeded MPS pressure must beat non-oracle embedding on at least one row")
    if var_summary.get("variational_mps_rows_beating_seeded_mps_pressure_reference") != 0:
        validation_errors.append("variational MPS/ALS must not beat seeded pressure in this bridge note")
    if var_summary.get("production_dmrg") is not False:
        validation_errors.append("variational MPS/ALS source must not be production DMRG")
    if non_oracle_summary.get("quantum_response_win_claimed") is not False:
        validation_errors.append("non-oracle embedding must not claim quantum response win")
    if not all(row["blocks_sampling_bridge"] for row in sampling_oracle_requirements):
        validation_errors.append("all sampling requirements should currently block the sampling bridge")

    sampling_oracle_constructed = False
    production_dmrg_available = bool(var_summary.get("production_dmrg"))
    same_access_positive_route_ready = (
        sampling_oracle_constructed
        and production_dmrg_available
        and var_summary.get("variational_mps_rows_beating_seeded_mps_pressure_reference", 1) > 0
    )

    return {
        "benchmark_id": "B10",
        "problem_id": 11,
        "title": "B10-T1 B5 Same-Access Sampling-or-DMRG Bridge",
        "version": "0.1",
        "status": STATUS,
        "method": METHOD,
        "source_target_id": "B10-T1",
        "dependency_benchmarks": ["B5", "B10"],
        "source_access_contract_method": access["method"],
        "source_d5_denominator_method": d5_table["method"],
        "source_non_oracle_embedding_method": non_oracle["method"],
        "source_seeded_mps_method": seeded_mps["method"],
        "source_variational_mps_method": var_mps["method"],
        "summary": {
            "denominator_ladder_count": len(denominator_ladder),
            "sampling_requirement_count": len(sampling_oracle_requirements),
            "blocking_sampling_requirement_count": sum(
                1 for row in sampling_oracle_requirements if row["blocks_sampling_bridge"]
            ),
            "bridge_decision_count": len(bridge_decisions),
            "b5_instance_count": d5_summary["instance_count"],
            "max_exact_d5_hilbert_dimension": d5_summary["max_hilbert_dimension"],
            "non_oracle_mean_relative_response_error": non_oracle_summary["selected_mean_relative_response_error"],
            "seeded_mps_mean_relative_response_error": seeded_summary["selected_mean_relative_response_error"],
            "variational_mps_mean_relative_response_error": var_summary["selected_mean_relative_response_error"],
            "seeded_mps_rows_beating_non_oracle_embedding": seeded_summary["mps_rows_beating_non_oracle_embedding"],
            "variational_mps_rows_beating_seeded_pressure": var_summary[
                "variational_mps_rows_beating_seeded_mps_pressure_reference"
            ],
            "sampling_oracle_constructed": sampling_oracle_constructed,
            "production_dmrg_available": production_dmrg_available,
            "same_access_positive_route_ready": same_access_positive_route_ready,
            "general_dequantization_theorem_proved": False,
            "sampling_access_theorem_proved": False,
            "bqp_separation_claimed": False,
            "quantum_advantage_claimed": False,
            "validation_error_count": len(validation_errors),
        },
        "denominator_ladder": denominator_ladder,
        "sampling_oracle_requirements": sampling_oracle_requirements,
        "bridge_decisions": bridge_decisions,
        "claim_boundary": {
            "sampling_oracle_constructed": sampling_oracle_constructed,
            "production_dmrg_available": production_dmrg_available,
            "same_access_positive_route_ready": same_access_positive_route_ready,
            "general_dequantization_theorem_proved": False,
            "sampling_access_theorem_proved": False,
            "bqp_separation_claimed": False,
            "quantum_advantage_claimed": False,
            "what_is_supported": (
                "For the current B5 Hubbard response portfolio, explicit denominators exist and exact-state-seeded MPS is a strong pressure reference. "
                "However, no comparable sampling/query oracle is constructed and the available variational MPS/ALS reference is not production DMRG."
            ),
            "what_is_not_supported": (
                "This is not a production DMRG result, not a same-access sampling theorem, not a quantum response win, "
                "not a dequantization theorem, and not a BQP separation."
            ),
        },
        "next_required_artifacts": [
            "Implement canonical-environment production DMRG/MPS for the same B5 response rows.",
            "If a sampling/query oracle is proposed, attach response-estimator variance, preparation/mixing cost, and confidence bounds.",
            "Compare any quantum response kernel against the explicit, non-oracle, seeded-MPS pressure, and production-DMRG denominators under the same access contract.",
        ],
        "validation_errors": validation_errors,
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# B10-T1 B5 Same-Access Sampling-or-DMRG Bridge v0.1",
        "",
        f"- Status: {report['status']}",
        f"- Method: {report['method']}",
        f"- Source access contract: {report['source_access_contract_method']}",
        f"- Denominator ladder rows: {report['summary']['denominator_ladder_count']}",
        f"- Sampling requirements: {report['summary']['sampling_requirement_count']}",
        f"- Blocking sampling requirements: {report['summary']['blocking_sampling_requirement_count']}",
        f"- Sampling oracle constructed: {report['summary']['sampling_oracle_constructed']}",
        f"- Production DMRG available: {report['summary']['production_dmrg_available']}",
        f"- Same-access positive route ready: {report['summary']['same_access_positive_route_ready']}",
        f"- Validation errors: {report['validation_errors']}",
        "",
        "## Denominator Ladder",
        "",
        "| id | access mode | status | mean error | max error | resource proxy | boundary |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for row in report["denominator_ladder"]:
        mean_error = "n/a" if row["mean_relative_response_error"] is None else f"{row['mean_relative_response_error']:.6g}"
        lines.append(
            f"| {row['id']} | {row['access_mode']} | {row['status']} | {mean_error} | "
            f"{row['max_relative_response_error']:.6g} | {row['resource_proxy']} | {row['claim_boundary']} |"
        )

    lines.extend(["", "## Sampling Oracle Requirements", ""])
    for row in report["sampling_oracle_requirements"]:
        lines.extend(
            [
                f"### {row['id']}",
                "",
                f"- Requirement: {row['requirement']}",
                f"- Current status: {row['current_status']}",
                f"- Blocks sampling bridge: {row['blocks_sampling_bridge']}",
                "",
            ]
        )

    lines.extend(["## Bridge Decisions", ""])
    for row in report["bridge_decisions"]:
        lines.extend(
            [
                f"### {row['access_mode']}",
                "",
                f"- Decision: {row['decision']}",
                f"- Reason: {row['reason']}",
                "",
            ]
        )

    lines.extend(["## Claim Boundary", ""])
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
        default=Path("results/B10_t1_b5_same_access_sampling_or_dmrg_bridge_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B10_t1_b5_same_access_sampling_or_dmrg_bridge.md"),
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
    return 0 if not report["validation_errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
