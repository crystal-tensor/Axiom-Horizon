#!/usr/bin/env python3
"""Context-absorption gate for the remaining line-1381 reduced-CNOT angles.

T-B1-004an showed that the five remaining line-1381 local-U3 parameters do not
pass simple exact-decomposition contracts. This gate asks the next local
question: do those angles already appear, or become exact after a single nearby
same-support rotation is combined with them, in the native optimized gcm_h6
context?

The gate is a search-boundary result, not a theorem. It only closes a cheap
context-inventory route; broader symbolic synthesis and full-circuit replay are
still open.
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
    wrap_angle,
    write_json,
    write_text,
)


ROOT = Path(__file__).resolve().parents[1]
EXACT_DECOMPOSITION_PATH = (
    ROOT / "results" / "B1_B7_cone01_line1381_exact_decomposition_pressure_gate_v0.json"
)
FIVE_PARAMETER_PATH = (
    ROOT / "results" / "B1_B7_cone01_five_parameter_line1381_exact_repair_gate_v0.json"
)
JSON_OUT = ROOT / "results" / "B1_B7_cone01_line1381_context_absorption_gate_v0.json"
MD_OUT = ROOT / "research" / "B1_B7_cone01_line1381_context_absorption_gate.md"

METHOD = "b1_b7_cone01_line1381_context_absorption_gate_v0"
STATUS = "cone01_line1381_context_absorption_not_accepted"
MODEL_STATUS = "remaining_five_line1381_parameters_have_no_single_step_context_absorption"
TARGET_LINE = 1381
CONTEXT_RADIUS = 64
ANGLE_TOLERANCE = 1e-9


def pi_over_four_distance(value: float) -> float:
    grid = round(value / (math.pi / 4.0)) * (math.pi / 4.0)
    return abs(wrap_angle(value - grid))


def best_context_grid_cancellation(
    value: float,
    context_rows: list[dict[str, Any]],
) -> dict[str, Any] | None:
    best: dict[str, Any] | None = None
    for row in context_rows:
        for sign in (1, -1):
            combined = wrap_angle(value + sign * float(row["angle"]))
            error = pi_over_four_distance(combined)
            candidate = {
                "line_number": row["line_number"],
                "gate": row["gate"],
                "argument_index": row["argument_index"],
                "qubit": row["qubit"],
                "raw_angle": row["raw_angle"],
                "sign": sign,
                "combined_angle": combined,
                "distance_to_pi_over_four_grid": error,
                "text": row["text"],
            }
            if best is None or (
                error,
                int(row["line_number"]),
                int(row["argument_index"]),
                sign,
            ) < (
                best["distance_to_pi_over_four_grid"],
                int(best["line_number"]),
                int(best["argument_index"]),
                int(best["sign"]),
            ):
                best = candidate
    return best


def analyze_parameter(
    index: int,
    value: float,
    support_qubits: set[int],
    window_start: int,
    window_end: int,
    inventory_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    context_start = window_start - CONTEXT_RADIUS
    context_end = window_end + CONTEXT_RADIUS
    exact_matches = [row for row in inventory_rows if same_angle(float(row["angle"]), value)]
    abs_matches = [row for row in inventory_rows if same_abs_angle(float(row["angle"]), value)]
    same_support_abs = [row for row in abs_matches if int(row["qubit"]) in support_qubits]
    context_rows = [
        row
        for row in inventory_rows
        if int(row["qubit"]) in support_qubits
        and context_start <= int(row["line_number"]) <= context_end
    ]
    context_abs = [row for row in context_rows if same_abs_angle(float(row["angle"]), value)]
    best_grid = best_context_grid_cancellation(value, context_rows)
    context_grid_pass = (
        best_grid is not None
        and best_grid["distance_to_pi_over_four_grid"] <= ANGLE_TOLERANCE
    )
    accepted_occurrence_removal = 0
    return {
        "parameter_index": index,
        "parameter_value": value,
        "value_over_pi": value / math.pi,
        "support_qubits": sorted(support_qubits),
        "context_start_line": context_start,
        "context_end_line": context_end,
        "context_rotation_argument_count": len(context_rows),
        "inventory_exact_match_count": len(exact_matches),
        "inventory_abs_angle_match_count": len(abs_matches),
        "same_support_abs_angle_match_count": len(same_support_abs),
        "context_abs_angle_match_count": len(context_abs),
        "best_context_grid_cancellation": best_grid,
        "context_grid_cancellation_exact": context_grid_pass,
        "accepted_context_absorption_certificate": False,
        "accepted_occurrence_removal": accepted_occurrence_removal,
        "accepted_proxy_t_reduction": accepted_occurrence_removal * PROXY_T_PER_OCCURRENCE,
        "sample_inventory_abs_matches": compact_matches(abs_matches),
        "sample_context_abs_matches": compact_matches(context_abs),
        "claim_boundary": (
            "Inventory/context matches and one-step pi/4-grid cancellation are search hints only. "
            "They are not commutation, symbolic replay, full-circuit replay, or B7 resource certificates."
        ),
    }


def build_payload() -> dict[str, Any]:
    exact_pressure = load_json(EXACT_DECOMPOSITION_PATH)
    five_parameter = load_json(FIVE_PARAMETER_PATH)
    pressure_rows = exact_pressure["line1381_exact_decomposition_pressure_rows"]
    five_row = five_parameter["five_parameter_line1381_exact_repair_rows"][0]
    support_qubits = {int(qubit) for qubit in five_row["support_qubits"]}
    window_start = int(five_row["window_start_line"])
    window_end = int(five_row["window_end_line"])
    inventory_rows = parse_rotation_inventory(INVENTORY_QASM_PATH)
    rows = [
        analyze_parameter(
            int(row["parameter_index"]),
            float(row["parameter_value"]),
            support_qubits,
            window_start,
            window_end,
            inventory_rows,
        )
        for row in pressure_rows
    ]
    accepted_removed = sum(row["accepted_occurrence_removal"] for row in rows)
    best_errors = [
        row["best_context_grid_cancellation"]["distance_to_pi_over_four_grid"]
        for row in rows
        if row["best_context_grid_cancellation"] is not None
    ]
    summary = {
        "source_exact_decomposition_pressure_method": exact_pressure.get("method"),
        "source_five_parameter_line1381_exact_repair_method": five_parameter.get("method"),
        "target_candidate_line_number": TARGET_LINE,
        "support_qubits": sorted(support_qubits),
        "window_start_line": window_start,
        "window_end_line": window_end,
        "context_radius": CONTEXT_RADIUS,
        "context_start_line": window_start - CONTEXT_RADIUS,
        "context_end_line": window_end + CONTEXT_RADIUS,
        "rotation_argument_inventory_count": len(inventory_rows),
        "context_rotation_argument_count": rows[0]["context_rotation_argument_count"]
        if rows
        else 0,
        "tested_remaining_parameter_count": len(rows),
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
        "accepted_occurrence_removal": accepted_removed,
        "accepted_proxy_t_reduction": accepted_removed * PROXY_T_PER_OCCURRENCE,
        "missing_occurrences_after_gate": max(0, REQUIRED_OCCURRENCE_REMOVALS - accepted_removed),
        "missing_proxy_t_after_gate": max(0, REQUIRED_OCCURRENCE_REMOVALS - accepted_removed)
        * PROXY_T_PER_OCCURRENCE,
        "context_absorption_claimed": False,
        "single_step_grid_cancellation_claimed": False,
        "full_circuit_rewrite_claimed": False,
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
        "inventory_qasm": display_path(INVENTORY_QASM_PATH),
        "source_exact_decomposition_pressure_result": display_path(EXACT_DECOMPOSITION_PATH),
        "source_five_parameter_line1381_exact_repair_result": display_path(FIVE_PARAMETER_PATH),
        "summary": summary,
        "line1381_context_absorption_rows": rows,
        "claim_boundary": {
            "supported_claim": (
                "The five remaining line-1381 parameters have no exact inventory match, "
                "no same-support context match within the configured radius, and no exact "
                "single-step pi/4-grid cancellation using nearby same-support rotations."
            ),
            "unsupported_claims": [
                "This is not a global obstruction theorem for line 1381.",
                "This does not reject multi-rotation context absorption.",
                "This does not reject broader symbolic synthesis or full-circuit replay.",
                "No B7 occurrence or proxy-T ledger reduction is accepted.",
            ],
            "context_absorption_claimed": False,
            "single_step_grid_cancellation_claimed": False,
            "full_circuit_rewrite_claimed": False,
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
    }
    payload["summary"]["validation_error_count"] = len(validate_payload(payload))
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    summary = payload.get("summary", {})
    rows = payload.get("line1381_context_absorption_rows", [])
    if payload.get("method") != METHOD:
        errors.append("method_mismatch")
    if payload.get("status") != STATUS:
        errors.append("status_mismatch")
    expected = {
        "target_candidate_line_number": TARGET_LINE,
        "support_qubits": [4, 8],
        "window_start_line": 1369,
        "window_end_line": 1379,
        "context_radius": 64,
        "context_start_line": 1305,
        "context_end_line": 1443,
        "rotation_argument_inventory_count": 2049,
        "context_rotation_argument_count": 44,
        "tested_remaining_parameter_count": 5,
        "inventory_exact_match_parameter_count": 0,
        "inventory_abs_match_parameter_count": 0,
        "same_support_abs_match_parameter_count": 0,
        "context_abs_match_parameter_count": 0,
        "context_grid_cancellation_exact_parameter_count": 0,
        "accepted_context_absorption_certificate_count": 0,
        "accepted_full_circuit_replay_certificate_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "missing_occurrences_after_gate": 30,
        "missing_proxy_t_after_gate": 600,
    }
    for field, expected_value in expected.items():
        if summary.get(field) != expected_value:
            errors.append(f"{field}_expected_{expected_value}_got_{summary.get(field)}")
    if len(rows) != 5:
        errors.append(f"row_count_expected_5_got_{len(rows)}")
    else:
        if [row.get("parameter_index") for row in rows] != [3, 4, 9, 16, 17]:
            errors.append("parameter_indices_mismatch")
        for row in rows:
            if row.get("accepted_context_absorption_certificate") is not False:
                errors.append(f"parameter_{row.get('parameter_index')}_must_not_accept_absorption")
            if row.get("context_grid_cancellation_exact") is not False:
                errors.append(f"parameter_{row.get('parameter_index')}_must_not_exact_cancel_to_grid")
            if row.get("inventory_abs_angle_match_count") != 0:
                errors.append(f"parameter_{row.get('parameter_index')}_inventory_abs_match_must_be_zero")
            if row.get("context_abs_angle_match_count") != 0:
                errors.append(f"parameter_{row.get('parameter_index')}_context_abs_match_must_be_zero")
    for field in [
        "context_absorption_claimed",
        "single_step_grid_cancellation_claimed",
        "full_circuit_rewrite_claimed",
        "resource_saving_claimed",
        "b7_ledger_improvement_claimed",
    ]:
        if summary.get(field) is not False:
            errors.append(f"{field}_must_be_false")
        if payload.get("claim_boundary", {}).get(field) is not False:
            errors.append(f"claim_boundary_{field}_must_be_false")
    return errors


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    rows = payload["line1381_context_absorption_rows"]
    lines = [
        "# B1/B7 Cone_01 Line-1381 Context Absorption Gate",
        "",
        f"Status: `{payload['status']}`",
        "",
        "This artifact consumes T-B1-004an and tests whether the five remaining line-1381 local-U3 parameters can be absorbed by exact inventory matches or one-step same-support context cancellation in the native optimized `gcm_h6` QASM.",
        "",
        "## Summary",
        "",
        f"- Target candidate line: `{summary['target_candidate_line_number']}`",
        f"- Support qubits: `{summary['support_qubits']}`",
        f"- Source window: `{summary['window_start_line']}`-`{summary['window_end_line']}`",
        f"- Context radius: `+/-{summary['context_radius']}` lines",
        f"- Context rotation arguments reviewed: `{summary['context_rotation_argument_count']}`",
        f"- Parameters tested: `{summary['tested_remaining_parameter_count']}`",
        f"- Inventory exact / absolute-angle matched parameters: `{summary['inventory_exact_match_parameter_count']}` / `{summary['inventory_abs_match_parameter_count']}`",
        f"- Same-support context absolute-angle matched parameters: `{summary['context_abs_match_parameter_count']}`",
        f"- One-step context pi/4-grid cancellations accepted: `{summary['context_grid_cancellation_exact_parameter_count']}`",
        f"- Min / max best one-step context grid-cancellation error: `{summary['min_best_context_grid_cancellation_error']:.12e}` / `{summary['max_best_context_grid_cancellation_error']:.12e}`",
        f"- Accepted replay / occurrence / proxy-T reduction: `{summary['accepted_full_circuit_replay_certificate_count']}` / `{summary['accepted_occurrence_removal']}` / `{summary['accepted_proxy_t_reduction']}`",
        f"- Validation errors: `{summary['validation_error_count']}`",
        "",
        "## Parameter Rows",
        "",
        "| Param index | Value/pi | Inventory abs matches | Context abs matches | Best context grid error | Best context line | Accepted |",
        "|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        best = row["best_context_grid_cancellation"] or {}
        lines.append(
            f"| {row['parameter_index']} | {row['value_over_pi']:.12f} | "
            f"{row['inventory_abs_angle_match_count']} | "
            f"{row['context_abs_angle_match_count']} | "
            f"{best.get('distance_to_pi_over_four_grid', float('nan')):.6e} | "
            f"{best.get('line_number', 'NA')} | "
            f"{row['accepted_context_absorption_certificate']} |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "This closes only a single-step context-inventory route. It does not rule out multi-rotation absorption, commutation-aware context rewriting, broader symbolic synthesis, or full-circuit replay. The B7 ledger remains unchanged at zero accepted occurrence removals and zero accepted proxy-T reduction.",
            "",
            "## Next Required Gate",
            "",
            "The next route must either build a multi-rotation/context-aware symbolic absorption search or abandon the local inventory route and construct a full-circuit replay certificate with explicit resource pricing for the five remaining line-1381 parameters.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", type=Path, default=JSON_OUT)
    parser.add_argument("--markdown-output", type=Path, default=MD_OUT)
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_payload()
    errors = validate_payload(payload)
    payload["summary"]["validation_error_count"] = len(errors)
    if errors:
        payload["validation_errors"] = errors
    write_json(args.json_output, payload, pretty=args.pretty)
    write_text(args.markdown_output, render_markdown(payload))
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
