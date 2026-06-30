#!/usr/bin/env python3
"""Gate B7 resource credit on B2 calibrated-evidence readiness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


METHOD = "b7_b2_calibrated_dependency_credit_gate_v0"
STATUS = "b2_calibrated_dependency_credit_rejected_missing_hardware_evidence"
MODEL_STATUS = "b7_dependency_bridge_structural_only_b2_claim_credit_blocked"
VERSION = "0.1"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any], pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(
        payload,
        indent=2 if pretty else None,
        separators=None if pretty else (",", ":"),
        sort_keys=True,
    )
    path.write_text(text + "\n", encoding="utf-8")


def gate(
    gate_id: str,
    label: str,
    passed: bool,
    evidence: dict[str, Any],
    acceptance_rule: str,
    blocks_credit: bool,
) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
        "acceptance_rule": acceptance_rule,
        "blocks_credit": bool(blocks_credit),
    }


def find_matching_target_row(target_payload: dict[str, Any], target: dict[str, Any]) -> dict[str, Any] | None:
    for row in target_payload["results"]:
        if (
            row.get("met") is True
            and row.get("memory_basis") == target["memory_basis"]
            and float(row.get("physical_error")) == float(target["physical_error"])
            and float(row.get("target_logical_error")) == float(target["target_logical_error"])
            and int(row.get("distance")) == int(target["distance"])
            and int(row.get("space_time_volume")) == int(target["space_time_volume"])
        ):
            return row
    return None


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    b7_bridge = load_json(args.b7_bridge_result)
    b2_contract = load_json(args.b2_contract_result)
    b2_target_volume = load_json(args.b2_target_volume)

    selected = b7_bridge["selected_b2_target"]
    selected_row = find_matching_target_row(b2_target_volume, selected)
    b2_summary = b2_contract["summary"]
    b2_claims = b2_contract["claim_boundary"]

    no_forbidden_claims = not any(
        bool(b2_claims[key])
        for key in [
            "production_decoder_claimed",
            "threshold_claimed",
            "new_code_claimed",
            "hardware_result_claimed",
            "calibrated_device_claimed",
            "quantum_advantage_claimed",
        ]
    )
    calibrated_blockers_open = [
        gate_id
        for gate_id, ready in [
            ("C4", b2_summary["calibrated_flag_data_used"]),
            ("C5", b2_summary["real_hardware_trace_used"]),
            ("C6", b2_summary["holdout_improvement_gate_passed"]),
        ]
        if not ready
    ]
    dependency_credit_allowed = (
        b7_bridge.get("benchmark_id") == "B7"
        and b7_bridge.get("method") == "b1_b2_dependency_schedule_bridge_v0"
        and selected_row is not None
        and b2_contract.get("benchmark_id") == "B2"
        and b2_contract.get("method") == "b2_calibrated_evidence_contract_gate_v0"
        and not b2_contract.get("validation_errors")
        and b2_summary["calibrated_flag_data_used"]
        and b2_summary["real_hardware_trace_used"]
        and b2_summary["holdout_improvement_gate_passed"]
        and b2_summary["holdout_nonregression_gate_passed"]
        and no_forbidden_claims
    )

    requirements = [
        gate(
            "D1",
            "B7 dependency bridge is present and structural",
            b7_bridge.get("benchmark_id") == "B7"
            and b7_bridge.get("method") == "b1_b2_dependency_schedule_bridge_v0"
            and b7_bridge.get("status") == "dependency_schedule_bridge_not_physical_layout",
            {
                "source_method": b7_bridge.get("method"),
                "source_status": b7_bridge.get("status"),
                "comparison_count": b7_bridge.get("comparison_count"),
                "min_space_time_volume_reduction": b7_bridge.get("min_space_time_volume_reduction"),
                "mean_space_time_volume_reduction": b7_bridge.get("mean_space_time_volume_reduction"),
            },
            "Use only the structural B1/B2 bridge as the dependency source.",
            False,
        ),
        gate(
            "D2",
            "Selected B2 target-volume row is replayable in the B2 baseline table",
            selected_row is not None,
            {
                "selected_b2_target": selected,
                "matched_row_found": selected_row is not None,
                "matched_logical_failures": None if selected_row is None else selected_row["logical_failures"],
                "matched_wilson_95_high": None if selected_row is None else selected_row["wilson_95_high"],
            },
            "The B7 bridge must point to an explicit B2 target-volume row.",
            False,
        ),
        gate(
            "D3",
            "B2 calibrated-evidence contract is valid",
            b2_contract.get("benchmark_id") == "B2"
            and b2_contract.get("method") == "b2_calibrated_evidence_contract_gate_v0"
            and not b2_contract.get("validation_errors"),
            {
                "contract_method": b2_contract.get("method"),
                "contract_status": b2_contract.get("status"),
                "validation_errors": b2_contract.get("validation_errors"),
                "failed_contract_requirement_ids": b2_summary["failed_contract_requirement_ids"],
            },
            "Consume the validated B2 calibrated-evidence contract.",
            False,
        ),
        gate(
            "D4",
            "Calibrated leakage/flag data are present",
            b2_summary["calibrated_flag_data_used"],
            {
                "source_gate": "K4/C4",
                "calibrated_flag_data_used": b2_summary["calibrated_flag_data_used"],
                "required_packet": "B2-C4-calibrated-flag-data",
            },
            "Submit calibrated leakage/flag rows before B2 credit enters B7.",
            True,
        ),
        gate(
            "D5",
            "Real or independently calibrated hardware traces are replayed",
            b2_summary["real_hardware_trace_used"],
            {
                "source_gate": "K5/C5",
                "real_hardware_trace_used": b2_summary["real_hardware_trace_used"],
                "required_packet": "B2-C5-hardware-trace-replay",
            },
            "Replay real or independently calibrated traces through the same B2 decoder path.",
            True,
        ),
        gate(
            "D6",
            "Strict holdout improvement is shown under the calibrated injection",
            b2_summary["holdout_improvement_gate_passed"],
            {
                "source_gate": "K6/C6",
                "holdout_improvement_gate_passed": b2_summary["holdout_improvement_gate_passed"],
                "holdout_baseline_failures": b2_summary["best_profile_holdout_baseline_failures"],
                "holdout_injected_failures": b2_summary["best_profile_holdout_injected_failures"],
                "holdout_failure_delta": b2_summary["best_profile_holdout_failure_delta"],
            },
            "Show fewer holdout logical failures while preserving non-regression.",
            True,
        ),
        gate(
            "D7",
            "Forbidden production, threshold, hardware, and advantage claims remain absent",
            no_forbidden_claims,
            {
                "production_decoder_claimed": b2_claims["production_decoder_claimed"],
                "threshold_claimed": b2_claims["threshold_claimed"],
                "new_code_claimed": b2_claims["new_code_claimed"],
                "hardware_result_claimed": b2_claims["hardware_result_claimed"],
                "calibrated_device_claimed": b2_claims["calibrated_device_claimed"],
                "quantum_advantage_claimed": b2_claims["quantum_advantage_claimed"],
            },
            "Keep B2 claim boundaries strict while the dependency gate is blocked.",
            False,
        ),
        gate(
            "D8",
            "B7 may count B2 calibrated-dependency credit",
            dependency_credit_allowed,
            {
                "dependency_credit_allowed": dependency_credit_allowed,
                "open_calibrated_blockers": calibrated_blockers_open,
                "b7_structural_min_space_time_volume_reduction": b7_bridge[
                    "min_space_time_volume_reduction"
                ],
                "b7_claim_credit_space_time_volume_reduction": None,
            },
            "Allow B2-derived B7 credit only after D4-D7 all pass.",
            True,
        ),
    ]

    passed_count = sum(1 for item in requirements if item["passed"])
    failed_ids = [item["gate_id"] for item in requirements if not item["passed"]]
    blocking_failed_ids = [item["gate_id"] for item in requirements if not item["passed"] and item["blocks_credit"]]
    summary = {
        "source_b7_status": b7_bridge["status"],
        "source_b7_method": b7_bridge["method"],
        "source_b7_comparison_count": b7_bridge["comparison_count"],
        "source_b7_min_space_time_volume_reduction": b7_bridge["min_space_time_volume_reduction"],
        "source_b7_mean_space_time_volume_reduction": b7_bridge["mean_space_time_volume_reduction"],
        "selected_b2_physical_error": selected["physical_error"],
        "selected_b2_target_logical_error": selected["target_logical_error"],
        "selected_b2_distance": selected["distance"],
        "selected_b2_space_time_volume": selected["space_time_volume"],
        "selected_b2_wilson_95_high": selected["wilson_95_high"],
        "selected_b2_row_replayed": selected_row is not None,
        "source_b2_contract_status": b2_contract["status"],
        "source_b2_contract_failed_ids": b2_summary["failed_contract_requirement_ids"],
        "source_b2_contract_packet_ids": b2_summary["contract_packet_ids"],
        "calibrated_flag_data_used": b2_summary["calibrated_flag_data_used"],
        "real_hardware_trace_used": b2_summary["real_hardware_trace_used"],
        "holdout_improvement_gate_passed": b2_summary["holdout_improvement_gate_passed"],
        "holdout_nonregression_gate_passed": b2_summary["holdout_nonregression_gate_passed"],
        "holdout_baseline_failures": b2_summary["best_profile_holdout_baseline_failures"],
        "holdout_injected_failures": b2_summary["best_profile_holdout_injected_failures"],
        "holdout_failure_delta": b2_summary["best_profile_holdout_failure_delta"],
        "requirement_count": len(requirements),
        "passed_requirement_count": passed_count,
        "failed_requirement_count": len(requirements) - passed_count,
        "failed_requirement_ids": failed_ids,
        "blocking_failed_requirement_ids": blocking_failed_ids,
        "dependency_credit_allowed": dependency_credit_allowed,
        "b7_claim_credit_space_time_volume_reduction": None,
        "b7_structural_bridge_remains_usable_as_planning_input": True,
    }

    report = {
        "benchmark_id": "B7",
        "problem_id": 21,
        "title": "B7 B2 calibrated dependency credit gate",
        "version": VERSION,
        "last_updated": args.last_updated,
        "status": STATUS,
        "method": METHOD,
        "model_status": MODEL_STATUS,
        "sources": {
            "b7_bridge_result": str(args.b7_bridge_result),
            "b2_contract_result": str(args.b2_contract_result),
            "b2_target_volume": str(args.b2_target_volume),
        },
        "summary": summary,
        "requirements": requirements,
        "claim_boundary": {
            "b7_dependency_gate_built": True,
            "b7_structural_planning_bridge_supported": True,
            "b2_calibrated_credit_allowed": False,
            "b7_resource_reduction_claimed_from_b2_calibration": False,
            "physical_layout_claimed": False,
            "low_overhead_qec_claimed": False,
            "threshold_claimed": False,
            "hardware_result_claimed": False,
            "quantum_advantage_claimed": False,
            "what_is_supported": (
                "The existing B7 B1/B2 dependency bridge is preserved as a structural planning "
                "input, and B7 now has an explicit claim-credit gate tied to B2 calibrated "
                "flag data, real hardware trace replay, and holdout improvement."
            ),
            "what_is_not_supported": (
                "No B2-derived calibrated resource credit, physical layout result, low-overhead "
                "QEC claim, threshold claim, hardware result, or quantum advantage claim is "
                "supported until D4-D6 are closed."
            ),
        },
    }
    report["validation_errors"] = validate(report)
    return report


def validate(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    summary = report["summary"]
    claims = report["claim_boundary"]
    if summary["requirement_count"] != 8:
        errors.append("expected eight requirements")
    if summary["passed_requirement_count"] != 4:
        errors.append("current gate should pass four requirements")
    if summary["failed_requirement_count"] != 4:
        errors.append("current gate should fail four requirements")
    if summary["failed_requirement_ids"] != ["D4", "D5", "D6", "D8"]:
        errors.append("current failed requirement ids should be D4/D5/D6/D8")
    if summary["blocking_failed_requirement_ids"] != ["D4", "D5", "D6", "D8"]:
        errors.append("blocking failed ids should be D4/D5/D6/D8")
    if summary["source_b2_contract_failed_ids"] != ["K4", "K5", "K6"]:
        errors.append("B2 source contract must still fail K4/K5/K6")
    for key in [
        "selected_b2_row_replayed",
        "holdout_nonregression_gate_passed",
        "b7_structural_bridge_remains_usable_as_planning_input",
    ]:
        if summary.get(key) is not True:
            errors.append(f"{key} must be true")
    for key in [
        "calibrated_flag_data_used",
        "real_hardware_trace_used",
        "holdout_improvement_gate_passed",
        "dependency_credit_allowed",
    ]:
        if summary.get(key) is not False:
            errors.append(f"{key} must remain false")
    if summary["holdout_failure_delta"] != 0:
        errors.append("holdout failure delta should remain zero")
    if summary["b7_claim_credit_space_time_volume_reduction"] is not None:
        errors.append("B7 claim-credit reduction must remain null")
    if claims.get("b7_dependency_gate_built") is not True:
        errors.append("claim boundary must disclose dependency gate")
    for key in [
        "b2_calibrated_credit_allowed",
        "b7_resource_reduction_claimed_from_b2_calibration",
        "physical_layout_claimed",
        "low_overhead_qec_claimed",
        "threshold_claimed",
        "hardware_result_claimed",
        "quantum_advantage_claimed",
    ]:
        if claims.get(key) is not False:
            errors.append(f"{key} must remain false")
    return errors


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# B7 B2 Calibrated Dependency Credit Gate v0.1",
        "",
        f"Status: **{report['status']}**",
        "",
        "## Summary",
        "",
        f"- Method: {report['method']}",
        f"- Model status: {report['model_status']}",
        f"- Source B7 bridge: {summary['source_b7_method']} / {summary['source_b7_status']}",
        f"- Source B7 comparisons: {summary['source_b7_comparison_count']}",
        f"- Structural min / mean STV reduction: {summary['source_b7_min_space_time_volume_reduction']} / {summary['source_b7_mean_space_time_volume_reduction']}",
        f"- Selected B2 p / target / distance / STV: {summary['selected_b2_physical_error']} / {summary['selected_b2_target_logical_error']} / {summary['selected_b2_distance']} / {summary['selected_b2_space_time_volume']}",
        f"- Selected B2 Wilson 95 high: {summary['selected_b2_wilson_95_high']}",
        f"- B2 contract status: {summary['source_b2_contract_status']}",
        f"- B2 contract failed ids: {', '.join(summary['source_b2_contract_failed_ids'])}",
        f"- Calibrated flag data used: {summary['calibrated_flag_data_used']}",
        f"- Real hardware trace used: {summary['real_hardware_trace_used']}",
        f"- Holdout baseline / injected / delta: {summary['holdout_baseline_failures']} / {summary['holdout_injected_failures']} / {summary['holdout_failure_delta']}",
        f"- Requirements passed / failed: {summary['passed_requirement_count']} / {summary['failed_requirement_count']}",
        f"- Blocking failed ids: {', '.join(summary['blocking_failed_requirement_ids'])}",
        f"- B2 calibrated dependency credit allowed: {summary['dependency_credit_allowed']}",
        f"- B7 claim-credit STV reduction: {summary['b7_claim_credit_space_time_volume_reduction']}",
        f"- Validation errors: {report['validation_errors']}",
        "",
        "## Requirements",
        "",
        "| gate | passed | blocks credit | label | acceptance rule |",
        "|---|---:|---:|---|---|",
    ]
    for item in report["requirements"]:
        lines.append(
            f"| {item['gate_id']} | {item['passed']} | {item['blocks_credit']} | "
            f"{item['label']} | {item['acceptance_rule']} |"
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
    lines.extend(
        [
            "",
            "## Next Gate",
            "",
            "B7 can keep using the B1/B2 bridge as a planning input, but it must",
            "not count B2-derived calibrated resource credit until B2 closes D4-D6:",
            "calibrated leakage/flag rows, real or independently calibrated trace",
            "replay, and strict holdout improvement without regression.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--b7-bridge-result",
        type=Path,
        default=Path("results/B7_b1_b2_dependency_schedule_bridge_v0.json"),
    )
    parser.add_argument(
        "--b2-contract-result",
        type=Path,
        default=Path("results/B2_calibrated_evidence_contract_gate_v0.json"),
    )
    parser.add_argument(
        "--b2-target-volume",
        type=Path,
        default=Path("results/B2_stim_surface_code_target_volume_v0.json"),
    )
    parser.add_argument("--last-updated", default="2026-07-01")
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B7_B2_calibrated_dependency_credit_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B7_B2_calibrated_dependency_credit_gate.md"),
    )
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    report = build_report(args)
    write_json(args.json_output, report, args.pretty)
    write_markdown(report, args.markdown_output)
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
