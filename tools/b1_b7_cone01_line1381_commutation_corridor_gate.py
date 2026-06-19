#!/usr/bin/env python3
"""Commutation-corridor gate for line-1381 context hints.

T-B1-004ap/aq rejected exact bounded same-support context absorption up to
four rotations. This gate asks a more replay-like question: even for the best
context candidates found so far, can the referenced rotations move through the
actual QASM corridor into the line-1381 packet under a conservative cheap
commutation model?

The model is intentionally strict. It accepts only external standalone RZ-like
context rotations whose path to the packet crosses no support-touching CNOT and
no non-diagonal support-touching single-qubit gate. A positive route would still
need symbolic/full-circuit replay before any B7 ledger credit.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from b1_b7_cone01_carrier_absorption_inventory_gate import (
    INVENTORY_QASM_PATH,
    PROXY_T_PER_OCCURRENCE,
    REQUIRED_OCCURRENCE_REMOVALS,
    display_path,
    eval_angle_expr,
    load_json,
    split_args,
    write_json,
    write_text,
)


ROOT = Path(__file__).resolve().parents[1]
FOUR_CONTEXT_PATH = ROOT / "results" / "B1_B7_cone01_line1381_four_rotation_context_gate_v0.json"
MULTI_CONTEXT_PATH = ROOT / "results" / "B1_B7_cone01_line1381_multi_rotation_context_gate_v0.json"
FIVE_PARAMETER_PATH = ROOT / "results" / "B1_B7_cone01_five_parameter_line1381_exact_repair_gate_v0.json"
JSON_OUT = ROOT / "results" / "B1_B7_cone01_line1381_commutation_corridor_gate_v0.json"
MD_OUT = ROOT / "research" / "B1_B7_cone01_line1381_commutation_corridor_gate.md"

METHOD = "b1_b7_cone01_line1381_commutation_corridor_gate_v0"
STATUS = "cone01_line1381_commutation_corridor_not_accepted"
MODEL_STATUS = "best_line1381_context_hints_have_no_replay_safe_commutation_corridor"
TARGET_LINE = 1381
SINGLE_QUBIT_RE = re.compile(r"^(u3|u|rz|rx|ry|u1|u2)\((.*)\) q\[(\d+)\];$")
CX_RE = re.compile(r"^cx q\[(\d+)\],q\[(\d+)\];$")
ANGLE_TOLERANCE = 1e-9


def parse_qasm(path: Path) -> dict[int, str]:
    return {idx: line.strip() for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)}


def is_zero_angle(raw: str) -> bool:
    return abs(eval_angle_expr(raw)) <= ANGLE_TOLERANCE


def single_qubit_gate(line: str) -> dict[str, Any] | None:
    match = SINGLE_QUBIT_RE.match(line.strip())
    if not match:
        return None
    gate, raw_args, qubit = match.groups()
    args = split_args(raw_args)
    diagonal = gate in {"rz", "u1"}
    if gate in {"u3", "u"} and args and is_zero_angle(args[0]):
        diagonal = True
    return {
        "gate": gate,
        "raw_args": args,
        "qubit": int(qubit),
        "diagonal_z_phase_family": diagonal,
        "non_diagonal_family": not diagonal,
    }


def cx_gate(line: str) -> dict[str, int] | None:
    match = CX_RE.match(line.strip())
    if not match:
        return None
    return {"control": int(match.group(1)), "target": int(match.group(2))}


def context_rotation_kind(row: dict[str, Any]) -> str:
    gate = row["gate"]
    argument_index = int(row["argument_index"])
    if gate in {"rz", "u1"}:
        return "standalone_z_rotation"
    if gate in {"u3", "u"} and argument_index in {1, 2}:
        return "embedded_u3_z_phase"
    if gate in {"u3", "u"} and argument_index == 0:
        return "embedded_u3_non_diagonal_theta"
    if gate in {"rx", "ry"}:
        return "standalone_non_diagonal_rotation"
    return "unknown_rotation_component"


def corridor_bounds(context_line: int, window_start: int, window_end: int) -> tuple[int, int, str]:
    if context_line < window_start:
        return context_line + 1, window_start - 1, "before_packet"
    if context_line > window_end:
        return window_end + 1, context_line - 1, "after_packet"
    return window_start, window_end, "inside_packet"


def classify_blocker(line_number: int, text: str, support_qubits: set[int]) -> dict[str, Any] | None:
    cx = cx_gate(text)
    if cx is not None:
        touches = cx["control"] in support_qubits or cx["target"] in support_qubits
        if touches:
            return {
                "line_number": line_number,
                "text": text,
                "blocker_type": "support_touching_cx",
                "qubits": [cx["control"], cx["target"]],
                "reason": "CNOT touching a support qubit blocks cheap movement without semantic replay.",
            }
        return None

    single = single_qubit_gate(text)
    if single is None or int(single["qubit"]) not in support_qubits:
        return None
    if single["non_diagonal_family"]:
        return {
            "line_number": line_number,
            "text": text,
            "blocker_type": "support_touching_non_diagonal_single_qubit",
            "qubits": [int(single["qubit"])],
            "reason": "Non-diagonal single-qubit gate on support qubit blocks cheap rotation transport.",
        }
    return None


def analyze_context_reference(
    context_row: dict[str, Any],
    qasm_lines: dict[int, str],
    support_qubits: set[int],
    window_start: int,
    window_end: int,
) -> dict[str, Any]:
    line_number = int(context_row["line_number"])
    start, end, position = corridor_bounds(line_number, window_start, window_end)
    kind = context_rotation_kind(context_row)
    blockers = []
    if position != "inside_packet":
        blockers = [
            blocker
            for line in range(start, end + 1)
            if (blocker := classify_blocker(line, qasm_lines.get(line, ""), support_qubits))
        ]
    accepted_external_z = kind == "standalone_z_rotation" and position != "inside_packet"
    corridor_clear = position != "inside_packet" and not blockers
    accepted = accepted_external_z and corridor_clear
    if position == "inside_packet":
        rejection = "context reference is inside the target packet and cannot be counted as external absorption"
    elif kind != "standalone_z_rotation":
        rejection = "context reference is not a standalone RZ-like rotation under the cheap corridor model"
    elif blockers:
        rejection = "support-touching CNOT or non-diagonal single-qubit blockers prevent cheap movement"
    else:
        rejection = "accepted cheap corridor reference"
    return {
        "line_number": line_number,
        "gate": context_row["gate"],
        "argument_index": int(context_row["argument_index"]),
        "qubit": int(context_row["qubit"]),
        "raw_angle": context_row["raw_angle"],
        "text": context_row["text"],
        "rotation_kind": kind,
        "corridor_position": position,
        "corridor_start_line": start,
        "corridor_end_line": end,
        "corridor_line_count": max(0, end - start + 1) if position != "inside_packet" else 0,
        "blocker_count": len(blockers),
        "blockers_sample": blockers[:8],
        "cheap_commutation_corridor_clear": corridor_clear,
        "accepted_cheap_corridor_reference": accepted,
        "rejection_reason": rejection,
    }


def candidate_from_multi(row: dict[str, Any]) -> dict[str, Any]:
    candidate = row["best_multi_rotation_context_candidate"]
    return {
        "source_gate": "T-B1-004ap",
        "parameter_index": int(row["parameter_index"]),
        "width": int(candidate["width"]),
        "distance_to_pi_over_four_grid": float(candidate["distance_to_pi_over_four_grid"]),
        "context_rows": candidate["context_rows"],
    }


def candidate_from_four(row: dict[str, Any]) -> dict[str, Any]:
    candidate = row["four_rotation_result"]["best_absorption_candidate"]
    return {
        "source_gate": "T-B1-004aq",
        "parameter_index": int(row["parameter_index"]),
        "width": int(candidate["width"]),
        "distance_to_pi_over_four_grid": float(candidate["distance_to_pi_over_four_grid"]),
        "context_rows": candidate["context_rows"],
    }


def analyze_candidate(
    candidate: dict[str, Any],
    qasm_lines: dict[int, str],
    support_qubits: set[int],
    window_start: int,
    window_end: int,
) -> dict[str, Any]:
    context_checks = [
        analyze_context_reference(row, qasm_lines, support_qubits, window_start, window_end)
        for row in candidate["context_rows"]
    ]
    accepted_reference_count = sum(1 for row in context_checks if row["accepted_cheap_corridor_reference"])
    all_references_accepted = accepted_reference_count == len(context_checks)
    return {
        "source_gate": candidate["source_gate"],
        "parameter_index": candidate["parameter_index"],
        "width": candidate["width"],
        "distance_to_pi_over_four_grid": candidate["distance_to_pi_over_four_grid"],
        "context_reference_count": len(context_checks),
        "accepted_cheap_corridor_reference_count": accepted_reference_count,
        "all_context_references_corridor_accepted": all_references_accepted,
        "accepted_commutation_corridor_replay_candidate": False,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "context_reference_checks": context_checks,
        "claim_boundary": (
            "A clear cheap corridor would still be only a movement precondition. "
            "It is not a symbolic/full-circuit replay certificate or B7 ledger saving."
        ),
    }


def build_payload() -> dict[str, Any]:
    four_context = load_json(FOUR_CONTEXT_PATH)
    multi_context = load_json(MULTI_CONTEXT_PATH)
    five_parameter = load_json(FIVE_PARAMETER_PATH)
    five_row = five_parameter["five_parameter_line1381_exact_repair_rows"][0]
    support_qubits = {int(qubit) for qubit in five_row["support_qubits"]}
    window_start = int(five_row["window_start_line"])
    window_end = int(five_row["window_end_line"])
    qasm_lines = parse_qasm(INVENTORY_QASM_PATH)

    raw_candidates = [
        *(candidate_from_multi(row) for row in multi_context["line1381_multi_rotation_context_rows"]),
        *(candidate_from_four(row) for row in four_context["line1381_four_rotation_context_rows"]),
    ]
    rows = [
        analyze_candidate(candidate, qasm_lines, support_qubits, window_start, window_end)
        for candidate in raw_candidates
    ]
    context_checks = [check for row in rows for check in row["context_reference_checks"]]
    unique_context_lines = sorted({int(check["line_number"]) for check in context_checks})
    accepted_removed = sum(row["accepted_occurrence_removal"] for row in rows)
    summary = {
        "source_multi_rotation_context_method": multi_context.get("method"),
        "source_four_rotation_context_method": four_context.get("method"),
        "source_five_parameter_line1381_exact_repair_method": five_parameter.get("method"),
        "target_candidate_line_number": TARGET_LINE,
        "support_qubits": sorted(support_qubits),
        "window_start_line": window_start,
        "window_end_line": window_end,
        "best_context_candidate_count": len(rows),
        "context_reference_count": len(context_checks),
        "unique_context_reference_line_count": len(unique_context_lines),
        "unique_context_reference_lines": unique_context_lines,
        "inside_packet_reference_count": sum(1 for row in context_checks if row["corridor_position"] == "inside_packet"),
        "non_standalone_context_reference_count": sum(
            1 for row in context_checks if row["rotation_kind"] != "standalone_z_rotation"
        ),
        "blocked_corridor_reference_count": sum(1 for row in context_checks if row["blocker_count"] > 0),
        "clear_external_standalone_z_reference_count": sum(
            1 for row in context_checks if row["accepted_cheap_corridor_reference"]
        ),
        "candidate_all_references_corridor_accepted_count": sum(
            1 for row in rows if row["all_context_references_corridor_accepted"]
        ),
        "accepted_commutation_corridor_replay_candidate_count": 0,
        "accepted_full_circuit_replay_certificate_count": 0,
        "accepted_occurrence_removal": accepted_removed,
        "accepted_proxy_t_reduction": accepted_removed * PROXY_T_PER_OCCURRENCE,
        "missing_occurrences_after_gate": max(0, REQUIRED_OCCURRENCE_REMOVALS - accepted_removed),
        "missing_proxy_t_after_gate": max(0, REQUIRED_OCCURRENCE_REMOVALS - accepted_removed)
        * PROXY_T_PER_OCCURRENCE,
        "commutation_corridor_replay_claimed": False,
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
        "source_multi_rotation_context_result": display_path(MULTI_CONTEXT_PATH),
        "source_four_rotation_context_result": display_path(FOUR_CONTEXT_PATH),
        "source_five_parameter_line1381_exact_repair_result": display_path(FIVE_PARAMETER_PATH),
        "summary": summary,
        "line1381_commutation_corridor_rows": rows,
        "claim_boundary": {
            "supported_claim": (
                "The best bounded two-/three-/four-rotation line-1381 context hints do not "
                "form a cheap commutation corridor into the target packet under the declared model."
            ),
            "unsupported_claims": [
                "This is not a symbolic/full-circuit replay proof.",
                "This is not a global obstruction theorem for line 1381.",
                "This does not reject non-cheap commutation, resynthesis, or a different scaffold.",
                "No B7 occurrence or proxy-T ledger reduction is accepted.",
            ],
            "commutation_corridor_replay_claimed": False,
            "full_circuit_rewrite_claimed": False,
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
        "validation": {
            "required_source_files_present": all(
                path.exists() for path in [FOUR_CONTEXT_PATH, MULTI_CONTEXT_PATH, FIVE_PARAMETER_PATH, INVENTORY_QASM_PATH]
            ),
            "validation_errors": [],
        },
    }
    errors = payload["validation"]["validation_errors"]
    if summary["accepted_occurrence_removal"] != 0:
        errors.append("corridor gate must not accept occurrence removal")
    if summary["accepted_full_circuit_replay_certificate_count"] != 0:
        errors.append("corridor gate must not accept full-circuit replay certificates")
    if any(row["accepted_commutation_corridor_replay_candidate"] for row in rows):
        errors.append("candidate rows must keep replay acceptance false")
    summary["validation_error_count"] = len(errors)
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    return "\n".join(
        [
            "# B1/B7 cone_01 Line-1381 Commutation Corridor Gate",
            "",
            "## Summary",
            "",
            f"- Method: `{payload['method']}`",
            f"- Status: `{payload['status']}`",
            f"- Target line / window: {summary['target_candidate_line_number']} / {summary['window_start_line']}-{summary['window_end_line']}",
            f"- Best context candidates reviewed: {summary['best_context_candidate_count']}",
            f"- Context references reviewed / unique lines: {summary['context_reference_count']} / {summary['unique_context_reference_line_count']}",
            f"- Inside-packet / non-standalone / blocked corridor references: {summary['inside_packet_reference_count']} / {summary['non_standalone_context_reference_count']} / {summary['blocked_corridor_reference_count']}",
            f"- Clear external standalone-Z references: {summary['clear_external_standalone_z_reference_count']}",
            f"- Candidates with all references corridor-accepted: {summary['candidate_all_references_corridor_accepted_count']}",
            f"- Accepted replay / occurrence / proxy-T reduction: {summary['accepted_full_circuit_replay_certificate_count']} / {summary['accepted_occurrence_removal']} / {summary['accepted_proxy_t_reduction']}",
            f"- Validation errors: {summary['validation_error_count']}",
            "",
            "## Claim Boundary",
            "",
            payload["claim_boundary"]["supported_claim"],
            "",
            "Unsupported claims:",
            "",
            *[f"- {claim}" for claim in payload["claim_boundary"]["unsupported_claims"]],
            "",
            "## Interpretation",
            "",
            "The bounded context hints now fail a replay-adjacent precondition: the referenced rotations are either inside the target packet, embedded inside U3 components, or blocked by support-touching CNOT/non-diagonal structure before they can be moved into the packet under the cheap commutation model. The next useful route is a real symbolic/full-circuit replay scaffold or a different occurrence-removing rewrite, not counting any B7 saving from these hints.",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path, default=JSON_OUT)
    parser.add_argument("--markdown-output", type=Path, default=MD_OUT)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    payload = build_payload()
    write_json(args.json_output, payload, pretty=args.pretty)
    write_text(args.markdown_output, render_markdown(payload))
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
