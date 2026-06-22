#!/usr/bin/env python3
"""Context-absorption gate for the priced 3-CNOT union-region candidate.

T-B1-004bq showed that every length-3 CNOT direction sequence can locally
replay the line-1378/1381 union target, but the best-priced exact candidate
still carries 18 off-pi/4 local-U3 parameters / 360 proxy-T pressure.  This
gate asks the immediate follow-up question: can that 18-parameter burden be
cheaply absorbed by the native optimized gcm_h6 rotation inventory or by one
same-support context rotation around the source window?

This is a narrow negative gate.  It does not close symbolic multi-rotation
absorption, full-circuit replay, or alternative scaffold searches.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from b1_b7_cone01_carrier_absorption_inventory_gate import (
    INVENTORY_QASM_PATH,
    PROXY_T_PER_OCCURRENCE,
    REQUIRED_OCCURRENCE_REMOVALS,
    compact_matches,
    display_path,
    load_json,
    parse_rotation_inventory,
    same_abs_angle,
    same_angle,
    write_json,
    write_text,
)
from b1_b7_cone01_line1381_context_absorption_gate import (
    ANGLE_TOLERANCE,
    CONTEXT_RADIUS,
    best_context_grid_cancellation,
    pi_over_four_distance,
)
from b1_b7_cone01_union_region_three_cnot_pricing_screen_gate import (
    JSON_OUT as THREE_CNOT_PRICING_PATH,
)


ROOT = Path(__file__).resolve().parents[1]
JSON_OUT = ROOT / "results" / "B1_B7_cone01_three_cnot_context_absorption_gate_v0.json"
MD_OUT = ROOT / "research" / "B1_B7_cone01_three_cnot_context_absorption_gate.md"

METHOD = "b1_b7_cone01_three_cnot_context_absorption_gate_v0"
STATUS = "cone01_three_cnot_context_absorption_not_accepted"
MODEL_STATUS = "best_three_cnot_candidate_has_no_single_step_context_absorption"
PROXY_T_PER_OFF_GRID_PARAMETER = 20


def best_exact_priced_row(payload: dict[str, Any]) -> dict[str, Any]:
    rows = [
        row
        for row in payload.get("union_region_three_cnot_pricing_rows", [])
        if row.get("exact_pass") is True
    ]
    if not rows:
        raise ValueError("three-CNOT pricing payload has no exact rows")
    return min(
        rows,
        key=lambda row: (
            int(row["best"]["proxy_t_pressure"]),
            int(row["best"]["parameter_stats"]["off_pi_over_four_grid_parameter_count"]),
            float(row["best"]["residual_norm"]),
            row["sequence_id"],
        ),
    )


def off_grid_parameters(row: dict[str, Any]) -> list[dict[str, Any]]:
    parameters = [float(value) for value in row["best"]["wrapped_parameters"]]
    result: list[dict[str, Any]] = []
    for index, value in enumerate(parameters):
        distance = pi_over_four_distance(value)
        if distance > ANGLE_TOLERANCE:
            result.append(
                {
                    "parameter_index": index,
                    "parameter_value": value,
                    "value_over_pi": value / math.pi,
                    "distance_to_pi_over_four_grid": distance,
                }
            )
    return result


def context_rows(
    inventory_rows: list[dict[str, Any]],
    support_qubits: set[int],
    window_start: int,
    window_end: int,
) -> list[dict[str, Any]]:
    context_start = window_start - CONTEXT_RADIUS
    context_end = window_end + CONTEXT_RADIUS
    return [
        row
        for row in inventory_rows
        if int(row["qubit"]) in support_qubits
        and context_start <= int(row["line_number"]) <= context_end
    ]


def analyze_parameter(
    parameter: dict[str, Any],
    support_qubits: set[int],
    context_inventory_rows: list[dict[str, Any]],
    inventory_rows: list[dict[str, Any]],
    window_start: int,
    window_end: int,
) -> dict[str, Any]:
    value = float(parameter["parameter_value"])
    exact_matches = [row for row in inventory_rows if same_angle(float(row["angle"]), value)]
    abs_matches = [row for row in inventory_rows if same_abs_angle(float(row["angle"]), value)]
    same_support_abs = [row for row in abs_matches if int(row["qubit"]) in support_qubits]
    context_abs = [
        row for row in context_inventory_rows if same_abs_angle(float(row["angle"]), value)
    ]
    best_grid = best_context_grid_cancellation(value, context_inventory_rows)
    context_grid_exact = (
        best_grid is not None
        and best_grid["distance_to_pi_over_four_grid"] <= ANGLE_TOLERANCE
    )
    accepted_occurrence_removal = 0
    return {
        **parameter,
        "support_qubits": sorted(support_qubits),
        "context_start_line": window_start - CONTEXT_RADIUS,
        "context_end_line": window_end + CONTEXT_RADIUS,
        "context_rotation_argument_count": len(context_inventory_rows),
        "inventory_exact_match_count": len(exact_matches),
        "inventory_abs_angle_match_count": len(abs_matches),
        "same_support_abs_angle_match_count": len(same_support_abs),
        "context_abs_angle_match_count": len(context_abs),
        "best_context_grid_cancellation": best_grid,
        "context_grid_cancellation_exact": context_grid_exact,
        "accepted_context_absorption_certificate": False,
        "accepted_occurrence_removal": accepted_occurrence_removal,
        "accepted_proxy_t_reduction": accepted_occurrence_removal
        * PROXY_T_PER_OCCURRENCE,
        "sample_inventory_abs_matches": compact_matches(abs_matches),
        "sample_context_abs_matches": compact_matches(context_abs),
        "claim_boundary": (
            "Exact or absolute angle matches and one-step context grid cancellation "
            "are search hints only. They are not commutation, symbolic replay, "
            "full-circuit replay, local-U3 pricing acceptance, or B7 resource certificates."
        ),
    }


def build_payload() -> dict[str, Any]:
    pricing = load_json(THREE_CNOT_PRICING_PATH)
    pricing_summary = pricing["summary"]
    selected = best_exact_priced_row(pricing)
    support_qubits = {int(qubit) for qubit in pricing_summary["support_qubits"]}
    window_start = int(pricing_summary["union_window"][0])
    window_end = int(pricing_summary["union_window"][1])
    inventory_rows = parse_rotation_inventory(INVENTORY_QASM_PATH)
    same_context_rows = context_rows(inventory_rows, support_qubits, window_start, window_end)
    parameter_rows = off_grid_parameters(selected)
    rows = [
        analyze_parameter(
            parameter,
            support_qubits,
            same_context_rows,
            inventory_rows,
            window_start,
            window_end,
        )
        for parameter in parameter_rows
    ]
    accepted_removed = sum(row["accepted_occurrence_removal"] for row in rows)
    best_errors = [
        row["best_context_grid_cancellation"]["distance_to_pi_over_four_grid"]
        for row in rows
        if row["best_context_grid_cancellation"] is not None
    ]
    summary = {
        "source_three_cnot_pricing_method": pricing.get("method"),
        "source_three_cnot_pricing_status": pricing.get("status"),
        "source_three_cnot_pricing_model_status": pricing.get("model_status"),
        "inventory_qasm": display_path(INVENTORY_QASM_PATH),
        "target_line_number": pricing_summary["target_line_number"],
        "union_window": pricing_summary["union_window"],
        "support_qubits": pricing_summary["support_qubits"],
        "selected_sequence_id": selected["sequence_id"],
        "selected_cnot_sequence": selected["cnot_sequence"],
        "selected_residual_norm": selected["best"]["residual_norm"],
        "selected_max_abs_entry_error": selected["best"]["max_abs_entry_error"],
        "selected_off_pi_over_four_parameter_count": len(rows),
        "selected_proxy_t_pressure": len(rows) * PROXY_T_PER_OFF_GRID_PARAMETER,
        "source_reported_off_pi_over_four_parameter_count": selected["best"][
            "parameter_stats"
        ]["off_pi_over_four_grid_parameter_count"],
        "source_reported_proxy_t_pressure": selected["best"]["proxy_t_pressure"],
        "current_line1381_off_grid_parameter_count": pricing_summary[
            "current_line1381_off_grid_parameter_count"
        ],
        "current_line1381_proxy_t_pressure": pricing_summary[
            "current_line1381_proxy_t_pressure"
        ],
        "best_two_cnot_census_proxy_t_pressure": pricing_summary[
            "best_two_cnot_census_proxy_t_pressure"
        ],
        "rotation_argument_inventory_count": len(inventory_rows),
        "context_radius": CONTEXT_RADIUS,
        "context_start_line": window_start - CONTEXT_RADIUS,
        "context_end_line": window_end + CONTEXT_RADIUS,
        "context_rotation_argument_count": len(same_context_rows),
        "inventory_exact_match_parameter_count": sum(
            1 for row in rows if row["inventory_exact_match_count"] > 0
        ),
        "inventory_abs_match_parameter_count": sum(
            1 for row in rows if row["inventory_abs_angle_match_count"] > 0
        ),
        "same_support_abs_match_parameter_count": sum(
            1 for row in rows if row["same_support_abs_angle_match_count"] > 0
        ),
        "context_abs_match_parameter_count": sum(
            1 for row in rows if row["context_abs_angle_match_count"] > 0
        ),
        "context_grid_cancellation_exact_parameter_count": sum(
            1 for row in rows if row["context_grid_cancellation_exact"]
        ),
        "min_best_context_grid_cancellation_error": min(best_errors) if best_errors else None,
        "max_best_context_grid_cancellation_error": max(best_errors) if best_errors else None,
        "accepted_context_absorption_certificate_count": 0,
        "accepted_full_circuit_replay_certificate_count": 0,
        "accepted_local_u3_pricing_certificate_count": 0,
        "accepted_occurrence_removal": accepted_removed,
        "accepted_proxy_t_reduction": accepted_removed * PROXY_T_PER_OCCURRENCE,
        "missing_occurrences_after_gate": max(0, REQUIRED_OCCURRENCE_REMOVALS - accepted_removed),
        "missing_proxy_t_after_gate": max(0, REQUIRED_OCCURRENCE_REMOVALS - accepted_removed)
        * PROXY_T_PER_OCCURRENCE,
        "context_absorption_claimed": False,
        "single_step_grid_cancellation_claimed": False,
        "local_u3_pricing_accepted": False,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
    }
    payload = {
        "benchmark_id": "B1",
        "linked_b7_problem_id": 21,
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "workload": "qasmbench_medium_exact/gcm_h6.qasm",
        "source_three_cnot_pricing_result": display_path(THREE_CNOT_PRICING_PATH),
        "summary": summary,
        "three_cnot_context_absorption_rows": rows,
        "claim_boundary": {
            "supported_claim": (
                "For the best-priced exact 3-CNOT union-region candidate, this gate "
                "checks whether any off-pi/4 local-U3 parameter has exact/absolute "
                "inventory matches, same-support context matches, or one-step "
                "same-support context cancellation back to the pi/4 grid."
            ),
            "unsupported_claims": [
                "This is not a symbolic multi-rotation absorption theorem.",
                "This is not a full-circuit replay or QASM patch certificate.",
                "This does not accept the 3-CNOT route as lower cost than the current line-1381 boundary.",
                "This does not accept occurrence removal, proxy-T reduction, or B7 ledger improvement.",
            ],
            "context_absorption_claimed": False,
            "single_step_grid_cancellation_claimed": False,
            "local_u3_pricing_accepted": False,
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
    }
    payload["summary"]["validation_error_count"] = len(validate_payload(payload))
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    summary = payload.get("summary", {})
    rows = payload.get("three_cnot_context_absorption_rows", [])
    expected = {
        "source_three_cnot_pricing_method": "b1_b7_cone01_union_region_three_cnot_pricing_screen_gate_v0",
        "source_three_cnot_pricing_status": "cone01_union_region_three_cnot_pricing_screen_rejected",
        "source_three_cnot_pricing_model_status": "three_cnot_union_candidates_do_not_price_better_than_current_boundary",
        "target_line_number": 1381,
        "union_window": [1369, 1379],
        "support_qubits": [4, 8],
        "selected_sequence_id": "10-10-01",
        "selected_off_pi_over_four_parameter_count": 18,
        "selected_proxy_t_pressure": 360,
        "source_reported_off_pi_over_four_parameter_count": 18,
        "source_reported_proxy_t_pressure": 360,
        "current_line1381_off_grid_parameter_count": 5,
        "current_line1381_proxy_t_pressure": 100,
        "best_two_cnot_census_proxy_t_pressure": 260,
        "context_radius": 64,
        "context_start_line": 1305,
        "context_end_line": 1443,
        "accepted_context_absorption_certificate_count": 0,
        "accepted_full_circuit_replay_certificate_count": 0,
        "accepted_local_u3_pricing_certificate_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "missing_occurrences_after_gate": 30,
        "missing_proxy_t_after_gate": 600,
        "context_absorption_claimed": False,
        "single_step_grid_cancellation_claimed": False,
        "local_u3_pricing_accepted": False,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
    }
    if payload.get("benchmark_id") != "B1":
        errors.append("benchmark_id_mismatch")
    if payload.get("method") != METHOD:
        errors.append("method_mismatch")
    if payload.get("status") != STATUS:
        errors.append("status_mismatch")
    if payload.get("model_status") != MODEL_STATUS:
        errors.append("model_status_mismatch")
    for key, value in expected.items():
        if summary.get(key) != value:
            errors.append(f"summary_{key}_expected_{value!r}_got_{summary.get(key)!r}")
    if len(rows) != 18:
        errors.append(f"row_count_expected_18_got_{len(rows)}")
    if summary.get("context_rotation_argument_count") != (rows[0]["context_rotation_argument_count"] if rows else None):
        errors.append("context_rotation_argument_count_mismatch")
    if summary.get("context_grid_cancellation_exact_parameter_count") != sum(
        1 for row in rows if row.get("context_grid_cancellation_exact")
    ):
        errors.append("context_grid_cancellation_count_mismatch")
    for field in [
        "context_absorption_claimed",
        "single_step_grid_cancellation_claimed",
        "local_u3_pricing_accepted",
        "resource_saving_claimed",
        "b7_ledger_improvement_claimed",
    ]:
        if summary.get(field) is not False:
            errors.append(f"summary_{field}_not_false")
        if payload.get("claim_boundary", {}).get(field) is not False:
            errors.append(f"claim_boundary_{field}_not_false")
    if any(row.get("accepted_context_absorption_certificate") is not False for row in rows):
        errors.append("row_context_absorption_certificate_must_be_false")
    if any(row.get("accepted_occurrence_removal") != 0 for row in rows):
        errors.append("row_accepted_occurrence_removal_must_be_zero")
    return errors


def markdown_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# B1/B7 cone_01 Three-CNOT Context-Absorption Gate",
        "",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Model status: `{payload['model_status']}`",
        f"- Workload: `{payload['workload']}`",
        f"- Source pricing result: `{payload['source_three_cnot_pricing_result']}`",
        f"- Selected 3-CNOT sequence: `{summary['selected_sequence_id']}`",
        f"- Selected off-grid parameters / proxy-T pressure: `{summary['selected_off_pi_over_four_parameter_count']}` / `{summary['selected_proxy_t_pressure']}`",
        f"- Current line-1381 boundary: `{summary['current_line1381_off_grid_parameter_count']}` / `{summary['current_line1381_proxy_t_pressure']}`",
        f"- Inventory rotation arguments: `{summary['rotation_argument_inventory_count']}`",
        f"- Same-support context rotation arguments: `{summary['context_rotation_argument_count']}`",
        f"- Inventory exact / abs-match parameter counts: `{summary['inventory_exact_match_parameter_count']}` / `{summary['inventory_abs_match_parameter_count']}`",
        f"- Same-support / context abs-match parameter counts: `{summary['same_support_abs_match_parameter_count']}` / `{summary['context_abs_match_parameter_count']}`",
        f"- One-step context grid-cancellation exact parameter count: `{summary['context_grid_cancellation_exact_parameter_count']}`",
        f"- Best one-step grid-cancellation error range: `{summary['min_best_context_grid_cancellation_error']}` - `{summary['max_best_context_grid_cancellation_error']}`",
        f"- B7 ledger improvement claimed: `{summary['b7_ledger_improvement_claimed']}`",
        "",
        "## Claim Boundary",
        "",
        payload["claim_boundary"]["supported_claim"],
        "",
        "Unsupported claims:",
    ]
    for claim in payload["claim_boundary"]["unsupported_claims"]:
        lines.append(f"- {claim}")
    lines.extend(["", "## Parameter Rows", ""])
    for row in payload["three_cnot_context_absorption_rows"]:
        best_grid = row["best_context_grid_cancellation"]
        best_error = (
            best_grid["distance_to_pi_over_four_grid"] if best_grid is not None else None
        )
        lines.append(
            "- "
            f"parameter `{row['parameter_index']}`: "
            f"distance-to-grid `{row['distance_to_pi_over_four_grid']}`, "
            f"inventory abs `{row['inventory_abs_angle_match_count']}`, "
            f"context abs `{row['context_abs_angle_match_count']}`, "
            f"best one-step grid error `{best_error}`"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", type=Path, default=JSON_OUT)
    parser.add_argument("--markdown-output", type=Path, default=MD_OUT)
    args = parser.parse_args()

    payload = build_payload()
    errors = validate_payload(payload)
    if errors:
        raise SystemExit("validation failed: " + "; ".join(errors))
    write_json(args.json_output, payload, True)
    write_text(args.markdown_output, markdown_report(payload))
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
