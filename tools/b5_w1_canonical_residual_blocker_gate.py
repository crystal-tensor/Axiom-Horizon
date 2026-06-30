#!/usr/bin/env python3
"""T-B5-006i/T-B10-014g: W1 canonical residual blocker gate."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b5_w1_canonical_residual_blocker_gate_v0"
STATUS = "w1_canonical_residual_blocker_gate_failed_missing_production_evidence"
MODEL_STATUS = "w1_v0_blockers_decomposed_for_production_dmrg_prs"
VERSION = "0.1"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any], pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2 if pretty else None, sort_keys=True)
    path.write_text(text + "\n", encoding="utf-8")


def requirement(requirement_id: str, label: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
    }


def row_blocker(row: dict[str, Any]) -> dict[str, Any]:
    stored_env = bool(row.get("stored_left_right_environments"))
    residual = bool(row.get("orthonormal_residual_ledger_present"))
    discarded = bool(row.get("discarded_weight_ledger_present"))
    fixed = bool(row.get("fixed_sector_norm_passed"))
    variance = bool(row.get("energy_variance_passed"))
    monotonic = bool(row.get("energy_monotonicity_passed"))
    convergence = bool(row.get("convergence_ledger_passed"))
    missing = []
    if not stored_env:
        missing.append("stored_left_right_environments")
    if not residual:
        missing.append("orthonormal_residual_ledger")
    if not discarded:
        missing.append("discarded_weight_ledger")
    if not fixed:
        missing.append("fixed_sector_norm")
    if not variance:
        missing.append("energy_variance")
    if not monotonic:
        missing.append("energy_monotonicity")
    if not convergence:
        missing.append("composite_convergence")
    return {
        "row_id": row["row_id"],
        "sites": int(row["sites"]),
        "u_over_t": float(row["u_over_t"]),
        "selected_candidate_family": row["selected_candidate_family"],
        "stored_left_right_environments": stored_env,
        "orthonormal_residual_ledger_present": residual,
        "discarded_weight_ledger_present": discarded,
        "fixed_sector_norm_passed": fixed,
        "energy_variance_passed": variance,
        "energy_monotonicity_passed": monotonic,
        "convergence_ledger_passed": convergence,
        "beats_seeded_mps_pressure": bool(row.get("beats_seeded_mps_pressure")),
        "selected_relative_response_error": float(row["selected_relative_response_error"]),
        "seeded_mps_pressure_relative_response_error": float(
            row["seeded_mps_pressure_relative_response_error"]
        ),
        "missing_production_evidence": missing,
        "required_solver_artifact": (
            "canonical-center sweep output with left/right environments, orthonormal residuals, "
            "discarded weights, monotone energy ledger, fixed-sector norm, energy variance, and "
            "same-access sweep/memory costs for this row"
        ),
    }


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    denominator = load_json(args.denominator_engine)
    summary = denominator["summary"]
    rows = [row_blocker(row) for row in denominator["rows"]]

    row_count = len(rows)
    env_rows = sum(row["stored_left_right_environments"] for row in rows)
    residual_rows = sum(row["orthonormal_residual_ledger_present"] for row in rows)
    discarded_rows = sum(row["discarded_weight_ledger_present"] for row in rows)
    fixed_rows = sum(row["fixed_sector_norm_passed"] for row in rows)
    variance_rows = sum(row["energy_variance_passed"] for row in rows)
    monotonic_rows = sum(row["energy_monotonicity_passed"] for row in rows)
    convergence_rows = sum(row["convergence_ledger_passed"] for row in rows)
    seeded_win_rows = sum(row["beats_seeded_mps_pressure"] for row in rows)

    pr_packets = [
        {
            "packet_id": "W1-E4-env-residuals",
            "owner_role": "DMRG Solver Agent",
            "required_artifact": "store canonical left/right environments and orthonormal residual norms for all 9 rows",
            "acceptance": "environment_rows == 9 and orthonormal_residual_rows == 9",
        },
        {
            "packet_id": "W1-E5-convergence",
            "owner_role": "Baseline Adversary",
            "required_artifact": "prove fixed-sector, energy-variance, discarded-weight, and monotonicity gates pass for all 9 rows",
            "acceptance": "convergence_passed_rows == 9",
        },
        {
            "packet_id": "W1-E6-seeded-pressure",
            "owner_role": "Tensor Denominator Agent",
            "required_artifact": "beat exact-state-seeded MPS pressure under the same 9-row access contract",
            "acceptance": "rows_beating_seeded_pressure == 9",
        },
        {
            "packet_id": "W1-E7-cost-ledger",
            "owner_role": "Cost Ledger Agent",
            "required_artifact": "add wall-clock, memory, sweep/matvec, and optimizer-loop costs for the production solver",
            "acceptance": "same_access_production_cost_ledger_complete == true",
        },
    ]

    requirements = [
        requirement(
            "C1",
            "Locked row contract is still intact",
            row_count == 9 and bool(summary.get("row_contract_hash")),
            {"row_count": row_count, "row_contract_hash": summary.get("row_contract_hash")},
        ),
        requirement(
            "C2",
            "Source W1 denominator v0 is valid and negative",
            summary.get("failed_denominator_requirement_ids") == ["E4", "E5", "E6", "E7"]
            and summary.get("validation_error_count") == 0,
            {
                "failed_denominator_requirement_ids": summary.get("failed_denominator_requirement_ids"),
                "validation_error_count": summary.get("validation_error_count"),
            },
        ),
        requirement(
            "C3",
            "Stored canonical environments are available for all rows",
            env_rows == 9,
            {"environment_rows": env_rows, "required_rows": 9},
        ),
        requirement(
            "C4",
            "Orthonormal residual ledgers are available for all rows",
            residual_rows == 9,
            {"orthonormal_residual_rows": residual_rows, "required_rows": 9},
        ),
        requirement(
            "C5",
            "All convergence diagnostics pass for all rows",
            convergence_rows == 9,
            {
                "convergence_passed_rows": convergence_rows,
                "fixed_sector_norm_passed_rows": fixed_rows,
                "energy_variance_passed_rows": variance_rows,
                "energy_monotonicity_passed_rows": monotonic_rows,
                "discarded_weight_rows": discarded_rows,
            },
        ),
        requirement(
            "C6",
            "Blockers are decomposed into PR-sized production packets",
            len(pr_packets) == 4,
            {"packet_ids": [packet["packet_id"] for packet in pr_packets]},
        ),
        requirement(
            "C7",
            "Same-access production cost ledger exists",
            False,
            {
                "same_access_production_cost_ledger_complete": False,
                "blocked_by": "W1-E7-cost-ledger",
            },
        ),
        requirement(
            "C8",
            "Forbidden claims remain false",
            all(
                summary.get(key) is False
                for key in [
                    "production_dmrg_claimed",
                    "same_access_positive_route_claimed",
                    "quantum_advantage_claimed",
                    "bqp_separation_claimed",
                ]
            ),
            {
                "production_dmrg_claimed": summary.get("production_dmrg_claimed"),
                "same_access_positive_route_claimed": summary.get("same_access_positive_route_claimed"),
                "quantum_advantage_claimed": summary.get("quantum_advantage_claimed"),
                "bqp_separation_claimed": summary.get("bqp_separation_claimed"),
            },
        ),
    ]
    passed = sum(1 for item in requirements if item["passed"])
    failed_ids = [item["requirement_id"] for item in requirements if not item["passed"]]

    validation_errors: list[str] = []
    if failed_ids != ["C3", "C4", "C5", "C7"]:
        validation_errors.append(f"unexpected failed canonical-residual requirements: {failed_ids}")
    if row_count != 9:
        validation_errors.append("expected nine locked B5/B10 rows")
    if convergence_rows != 0:
        validation_errors.append("v0 unexpectedly has convergence-passed rows")
    if seeded_win_rows != 0:
        validation_errors.append("v0 unexpectedly beats seeded pressure")

    blocker_summary = {
        "row_contract_count": row_count,
        "row_contract_hash": summary.get("row_contract_hash"),
        "source_denominator_method": denominator.get("method"),
        "source_failed_denominator_requirement_ids": summary.get("failed_denominator_requirement_ids"),
        "canonical_residual_requirement_count": len(requirements),
        "canonical_residual_requirements_passed": passed,
        "canonical_residual_requirements_failed": len(requirements) - passed,
        "failed_canonical_residual_requirement_ids": failed_ids,
        "environment_rows": env_rows,
        "orthonormal_residual_rows": residual_rows,
        "discarded_weight_rows": discarded_rows,
        "fixed_sector_norm_passed_rows": fixed_rows,
        "energy_variance_passed_rows": variance_rows,
        "energy_monotonicity_passed_rows": monotonic_rows,
        "convergence_passed_rows": convergence_rows,
        "rows_beating_seeded_pressure": seeded_win_rows,
        "same_access_production_cost_ledger_complete": False,
        "pr_packet_count": len(pr_packets),
        "w1_canonical_residual_gate_ready": False,
        "production_dmrg_available": False,
        "same_access_positive_route_ready": False,
        "production_dmrg_claimed": False,
        "same_access_positive_route_claimed": False,
        "quantum_advantage_claimed": False,
        "bqp_separation_claimed": False,
        "validation_error_count": len(validation_errors),
    }

    return {
        "benchmark_id": "B5",
        "linked_benchmark_id": "B10",
        "source_target_id": "B10-T1",
        "dependency_benchmarks": ["B5", "B10"],
        "title": "B5 W1 Canonical Residual Blocker Gate v0",
        "version": VERSION,
        "last_updated": args.last_updated,
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_denominator_engine_result": str(args.denominator_engine),
        "summary": blocker_summary,
        "requirements": requirements,
        "rows": rows,
        "pr_packets": pr_packets,
        "claim_boundary": {
            "what_is_supported": (
                "The E4/E5 W1 failures are decomposed into row-level missing evidence and PR-sized "
                "production-solver packets under the locked nine-row B5/B10 contract."
            ),
            "what_is_not_supported": (
                "This does not add production DMRG, canonical environments, residual ledgers, "
                "seeded-pressure wins, a same-access positive route, quantum advantage, or BQP separation."
            ),
            "next_gate": (
                "A future solver must satisfy C3/C4/C5/C7 by storing canonical environments, "
                "orthonormal residuals, convergence evidence, and a complete same-access cost ledger."
            ),
            "production_dmrg_claimed": False,
            "same_access_positive_route_claimed": False,
            "quantum_advantage_claimed": False,
            "bqp_separation_claimed": False,
        },
        "validation_errors": validation_errors,
        "runtime_seconds": time.time() - started,
    }


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    summary = payload["summary"]
    lines = [
        "# B5 W1 Canonical Residual Blocker Gate v0.1",
        "",
        f"Status: **{payload['status']}**",
        "",
        "## Summary",
        "",
        f"- Method: `{payload['method']}`",
        f"- Row contract count/hash: {summary['row_contract_count']} / `{summary['row_contract_hash']}`",
        f"- Requirements passed/failed: {summary['canonical_residual_requirements_passed']} / {summary['canonical_residual_requirements_failed']}",
        f"- Failed requirement IDs: {summary['failed_canonical_residual_requirement_ids']}",
        f"- Environment / residual rows: {summary['environment_rows']} / {summary['orthonormal_residual_rows']}",
        f"- Convergence-passed rows: {summary['convergence_passed_rows']}",
        f"- Rows beating seeded pressure: {summary['rows_beating_seeded_pressure']}",
        f"- PR packet count: {summary['pr_packet_count']}",
        "",
        "## Requirement Ledger",
        "",
        "| ID | Requirement | Passed | Evidence |",
        "| --- | --- | --- | --- |",
    ]
    for item in payload["requirements"]:
        evidence = "; ".join(f"{key}={value}" for key, value in item["evidence"].items())
        lines.append(f"| {item['requirement_id']} | {item['label']} | {item['passed']} | {evidence} |")

    lines.extend(
        [
            "",
            "## Row Blockers",
            "",
            "| row | missing production evidence | rel error | seeded rel error | convergence |",
            "| --- | --- | ---: | ---: | --- |",
        ]
    )
    for row in payload["rows"]:
        missing = ", ".join(row["missing_production_evidence"])
        lines.append(
            f"| {row['row_id']} | {missing} | {row['selected_relative_response_error']:.6g} | "
            f"{row['seeded_mps_pressure_relative_response_error']:.6g} | {row['convergence_ledger_passed']} |"
        )

    lines.extend(
        [
            "",
            "## PR Packets",
            "",
            "| Packet | Owner role | Required artifact | Acceptance |",
            "| --- | --- | --- | --- |",
        ]
    )
    for packet in payload["pr_packets"]:
        lines.append(
            f"| {packet['packet_id']} | {packet['owner_role']} | "
            f"{packet['required_artifact']} | `{packet['acceptance']}` |"
        )

    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            f"- what_is_supported: {payload['claim_boundary']['what_is_supported']}",
            f"- what_is_not_supported: {payload['claim_boundary']['what_is_not_supported']}",
            f"- next_gate: {payload['claim_boundary']['next_gate']}",
            f"- production_dmrg_claimed: {payload['claim_boundary']['production_dmrg_claimed']}",
            f"- quantum_advantage_claimed: {payload['claim_boundary']['quantum_advantage_claimed']}",
            f"- bqp_separation_claimed: {payload['claim_boundary']['bqp_separation_claimed']}",
            "",
            "## Validation",
            "",
            f"- validation_error_count: {len(payload['validation_errors'])}",
        ]
    )
    if payload["validation_errors"]:
        lines.extend(f"- {error}" for error in payload["validation_errors"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the B5/B10 W1 canonical residual blocker gate.")
    parser.add_argument(
        "--denominator-engine",
        type=Path,
        default=Path("results/B5_production_dmrg_mps_denominator_v0.json"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B5_w1_canonical_residual_blocker_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B5_w1_canonical_residual_blocker_gate.md"),
    )
    parser.add_argument("--last-updated", default=time.strftime("%Y-%m-%d"))
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    payload = build_payload(args)
    write_json(args.json_output, payload, pretty=args.pretty)
    write_markdown(payload, args.markdown_output)
    if args.pretty:
        print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0 if not payload["validation_errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
