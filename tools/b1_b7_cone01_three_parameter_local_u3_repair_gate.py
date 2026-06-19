#!/usr/bin/env python3
"""Three-parameter local-U3 repair gate for B1/B7 cone_01 packets.

T-B1-004ai showed that a one- or two-parameter sparse repair exactifies only
one of the three reduced-CNOT packet candidates. This gate performs the next
bounded continuation: for the two unresolved packets, exhaustively free exactly
three local-U3 parameters on the pi/4-snapped scaffold.

This remains packet-level evidence only. A repaired packet is not accepted as a
full-circuit rewrite, symbolic exact decomposition, or B7 ledger saving.
"""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path
from typing import Any

import numpy as np

from b1_b7_cone01_carrier_absorption_inventory_gate import (
    PROXY_T_PER_OCCURRENCE,
    REQUIRED_OCCURRENCE_REMOVALS,
    display_path,
    load_json,
    write_json,
    write_text,
)
from b1_b7_cone01_local_u3_exactification_gate import (
    best_exact_scaffold,
    parameter_stats,
    snap_to_pi_over_four,
    wrap_angle,
)
from b1_b7_cone01_packet_synthesis_search_gate import (
    first_cnot_orientation,
    residual_norm,
    scaffold_unitary,
    target_matrix,
)
from b1_b7_cone01_sparse_local_u3_repair_gate import optimize_free_indices


ROOT = Path(__file__).resolve().parents[1]
SEMANTIC_PACKET_PATH = ROOT / "results" / "B1_B7_cone01_semantic_replay_packet_gate_v0.json"
SYNTHESIS_PATH = ROOT / "results" / "B1_B7_cone01_packet_synthesis_search_gate_v0.json"
SPARSE_REPAIR_PATH = ROOT / "results" / "B1_B7_cone01_sparse_local_u3_repair_gate_v0.json"
JSON_OUT = ROOT / "results" / "B1_B7_cone01_three_parameter_local_u3_repair_gate_v0.json"
MD_OUT = ROOT / "research" / "B1_B7_cone01_three_parameter_local_u3_repair_gate.md"

METHOD = "b1_b7_cone01_three_parameter_local_u3_repair_gate_v0"
STATUS = "cone01_three_parameter_local_u3_repair_partial_not_ledger_accepted"
MODEL_STATUS = "two_packets_repaired_one_packet_remains_unrepaired"
FREE_PARAMETER_COUNT = 3
DEFAULT_MAX_NFEV = 700


def analyze_unresolved_packet(
    packet: dict[str, Any],
    synthesis_row: dict[str, Any],
    sparse_row: dict[str, Any],
    max_nfev: int,
) -> dict[str, Any]:
    exact = best_exact_scaffold(synthesis_row)
    if exact is None:
        raise ValueError(f"missing exact scaffold for line {packet['candidate_line_number']}")

    original_parameters = np.array([float(value) for value in exact["best"]["wrapped_parameters"]])
    snapped_parameters = np.array(
        [wrap_angle(snap_to_pi_over_four(value)) for value in original_parameters],
        dtype=float,
    )
    matrix = target_matrix(packet)
    control, target_qubit = first_cnot_orientation(packet)
    cnot_count = int(exact["cnot_count"])
    snapped_residual = residual_norm(
        scaffold_unitary(snapped_parameters, cnot_count, control, target_qubit),
        matrix,
    )

    rows: list[dict[str, Any]] = []
    for free_indices in itertools.combinations(range(len(snapped_parameters)), FREE_PARAMETER_COUNT):
        rows.append(
            optimize_free_indices(
                snapped_parameters,
                original_parameters,
                tuple(free_indices),
                matrix,
                cnot_count,
                control,
                target_qubit,
                max_nfev,
            )
        )

    best = min(rows, key=lambda row: row["residual_norm"])
    exact_rows = [row for row in rows if row["exact_pass"]]
    best_exact = min(exact_rows, key=lambda row: row["residual_norm"], default=None)
    return {
        "pattern_id": packet["pattern_id"],
        "candidate_line_number": int(packet["candidate_line_number"]),
        "window_start_line": int(packet["window_start_line"]),
        "window_end_line": int(packet["window_end_line"]),
        "support_qubits": packet["support_qubits"],
        "source_cnot_count": int(packet["cx_count"]),
        "replacement_cnot_count": cnot_count,
        "candidate_cnot_reduction": int(packet["cx_count"]) - cnot_count,
        "replacement_parameter_count": len(original_parameters),
        "replacement_off_pi_over_four_parameter_count": int(
            parameter_stats([float(value) for value in original_parameters])[
                "off_pi_over_four_parameter_count"
            ]
        ),
        "source_best_one_parameter_residual_norm": sparse_row["best_one_parameter_residual_norm"],
        "source_best_two_parameter_residual_norm": sparse_row["best_two_parameter_residual_norm"],
        "snapped_residual_norm": snapped_residual,
        "three_parameter_candidate_count": len(rows),
        "three_parameter_exact_pass": best_exact is not None,
        "best_three_parameter_residual_norm": best["residual_norm"],
        "best_three_parameter_free_indices": best["free_indices"],
        "best_three_parameter_off_pi_over_four_parameter_count": int(
            best["repaired_parameter_stats"]["off_pi_over_four_parameter_count"]
        ),
        "exact_three_parameter_residual_norm": float(best_exact["residual_norm"])
        if best_exact
        else None,
        "exact_three_parameter_free_indices": best_exact["free_indices"] if best_exact else None,
        "exact_three_parameter_free_values": best_exact["free_parameter_values"]
        if best_exact
        else None,
        "exact_three_parameter_off_pi_over_four_parameter_count": int(
            best_exact["repaired_parameter_stats"]["off_pi_over_four_parameter_count"]
        )
        if best_exact
        else None,
        "accepted_three_parameter_repair_as_full_circuit_rewrite": False,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
    }


def build_payload(max_nfev: int) -> dict[str, Any]:
    semantic = load_json(SEMANTIC_PACKET_PATH)
    synthesis = load_json(SYNTHESIS_PATH)
    sparse = load_json(SPARSE_REPAIR_PATH)
    synthesis_by_line = {
        int(row["candidate_line_number"]): row
        for row in synthesis.get("packet_synthesis_rows", [])
    }
    sparse_by_line = {
        int(row["candidate_line_number"]): row
        for row in sparse.get("sparse_local_u3_repair_rows", [])
    }
    unresolved_lines = [
        int(row["candidate_line_number"])
        for row in sparse.get("sparse_local_u3_repair_rows", [])
        if not row.get("sparse_repair_exact_pass")
    ]
    packet_by_line = {
        int(packet["candidate_line_number"]): packet
        for packet in semantic.get("semantic_replay_packets", [])
    }
    rows = [
        analyze_unresolved_packet(
            packet_by_line[line],
            synthesis_by_line[line],
            sparse_by_line[line],
            max_nfev,
        )
        for line in unresolved_lines
    ]
    exact_rows = [row for row in rows if row["three_parameter_exact_pass"]]
    unresolved_rows = [row for row in rows if not row["three_parameter_exact_pass"]]
    prior_exact_rows = [
        row
        for row in sparse.get("sparse_local_u3_repair_rows", [])
        if row.get("sparse_repair_exact_pass")
    ]
    accepted_removed = sum(row["accepted_occurrence_removal"] for row in rows)
    summary = {
        "source_semantic_method": semantic.get("method"),
        "source_synthesis_method": synthesis.get("method"),
        "source_sparse_repair_method": sparse.get("method"),
        "source_sparse_repair_exact_packet_count": len(prior_exact_rows),
        "source_sparse_repair_unresolved_packet_count": len(unresolved_lines),
        "three_parameter_free_count": FREE_PARAMETER_COUNT,
        "three_parameter_packet_count": len(rows),
        "three_parameter_candidate_count": sum(
            row["three_parameter_candidate_count"] for row in rows
        ),
        "three_parameter_exact_packet_count": len(exact_rows),
        "three_parameter_unresolved_packet_count": len(unresolved_rows),
        "total_packet_exact_after_three_parameter_gate": len(prior_exact_rows) + len(exact_rows),
        "total_packet_unresolved_after_three_parameter_gate": len(unresolved_rows),
        "candidate_cnot_reduction_if_all_packets_accepted": int(
            sparse["summary"]["candidate_cnot_reduction_if_all_packets_accepted"]
        ),
        "partial_candidate_cnot_reduction_if_accepted": sum(
            int(row["candidate_cnot_reduction"]) for row in prior_exact_rows
        )
        + sum(int(row["candidate_cnot_reduction"]) for row in exact_rows),
        "remaining_unrepaired_replacement_off_pi_over_four_parameter_count": sum(
            row["replacement_off_pi_over_four_parameter_count"] for row in unresolved_rows
        ),
        "three_parameter_exact_repair_off_pi_over_four_parameter_count": sum(
            row["exact_three_parameter_off_pi_over_four_parameter_count"] or 0
            for row in exact_rows
        ),
        "accepted_three_parameter_repair_as_full_circuit_rewrite_count": 0,
        "accepted_occurrence_removal": accepted_removed,
        "accepted_proxy_t_reduction": 0,
        "missing_occurrences_after_gate": max(0, REQUIRED_OCCURRENCE_REMOVALS - accepted_removed),
        "missing_proxy_t_after_gate": max(
            0,
            (REQUIRED_OCCURRENCE_REMOVALS - accepted_removed) * PROXY_T_PER_OCCURRENCE,
        ),
        "partial_packet_repair_claimed_as_b7_saving": False,
        "symbolic_exact_decomposition_claimed": False,
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
        "workload": semantic.get("workload", "qasmbench_medium_exact/gcm_h6.qasm"),
        "source_semantic_packet_result": display_path(SEMANTIC_PACKET_PATH),
        "source_packet_synthesis_result": display_path(SYNTHESIS_PATH),
        "source_sparse_local_u3_repair_result": display_path(SPARSE_REPAIR_PATH),
        "summary": summary,
        "three_parameter_local_u3_repair_rows": rows,
        "claim_boundary": {
            "supported_claim": (
                "Exhaustive exactly-three-parameter repair over the two unresolved T-B1-004ai "
                "packets exactifies line 268, while line 1381 remains unrepaired."
            ),
            "unsupported_claims": [
                "The repaired packets are not accepted as full-circuit rewrites.",
                "No symbolic exact decomposition or absorption certificate is emitted.",
                "No B7 occurrence or proxy-T ledger reduction is accepted.",
            ],
            "partial_packet_repair_claimed_as_b7_saving": False,
            "symbolic_exact_decomposition_claimed": False,
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
    rows = payload.get("three_parameter_local_u3_repair_rows", [])
    if payload.get("method") != METHOD:
        errors.append("method_mismatch")
    if payload.get("status") != STATUS:
        errors.append("status_mismatch")
    expected = {
        "source_sparse_repair_exact_packet_count": 1,
        "source_sparse_repair_unresolved_packet_count": 2,
        "three_parameter_free_count": 3,
        "three_parameter_packet_count": 2,
        "three_parameter_candidate_count": 1632,
        "three_parameter_exact_packet_count": 1,
        "three_parameter_unresolved_packet_count": 1,
        "total_packet_exact_after_three_parameter_gate": 2,
        "total_packet_unresolved_after_three_parameter_gate": 1,
        "candidate_cnot_reduction_if_all_packets_accepted": 9,
        "partial_candidate_cnot_reduction_if_accepted": 6,
        "remaining_unrepaired_replacement_off_pi_over_four_parameter_count": 15,
        "three_parameter_exact_repair_off_pi_over_four_parameter_count": 0,
        "accepted_three_parameter_repair_as_full_circuit_rewrite_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "missing_occurrences_after_gate": 30,
        "missing_proxy_t_after_gate": 600,
    }
    for field, expected_value in expected.items():
        if summary.get(field) != expected_value:
            errors.append(f"{field}_expected_{expected_value}_got_{summary.get(field)}")
    for field in [
        "partial_packet_repair_claimed_as_b7_saving",
        "symbolic_exact_decomposition_claimed",
        "full_circuit_rewrite_claimed",
        "resource_saving_claimed",
        "b7_ledger_improvement_claimed",
    ]:
        if summary.get(field) is not False:
            errors.append(f"{field}_must_be_false")
        if payload.get("claim_boundary", {}).get(field) is not False:
            errors.append(f"claim_boundary_{field}_must_be_false")
    exact_lines = [
        row.get("candidate_line_number")
        for row in rows
        if row.get("three_parameter_exact_pass")
    ]
    if exact_lines != [268]:
        errors.append(f"exact_lines_expected_[268]_got_{exact_lines}")
    unresolved_lines = [
        row.get("candidate_line_number")
        for row in rows
        if not row.get("three_parameter_exact_pass")
    ]
    if unresolved_lines != [1381]:
        errors.append(f"unresolved_lines_expected_[1381]_got_{unresolved_lines}")
    for row in rows:
        if row.get("accepted_three_parameter_repair_as_full_circuit_rewrite") is not False:
            errors.append(f"{row.get('candidate_line_number')}_must_not_accept_rewrite")
        if row.get("accepted_occurrence_removal") != 0:
            errors.append(f"{row.get('candidate_line_number')}_accepted_occurrence_must_be_zero")
    return errors


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# B1/B7 Cone_01 Three-Parameter Local-U3 Repair Gate",
        "",
        f"Status: `{payload['status']}`",
        "",
        "This artifact consumes T-B1-004ai and exhaustively frees exactly three local-U3 parameters for each unresolved reduced-CNOT packet.",
        "",
        "## Summary",
        "",
        f"- Source sparse exact packets: `{summary['source_sparse_repair_exact_packet_count']}`",
        f"- Source unresolved packets: `{summary['source_sparse_repair_unresolved_packet_count']}`",
        f"- Three-parameter candidates searched: `{summary['three_parameter_candidate_count']}`",
        f"- New three-parameter exact packets: `{summary['three_parameter_exact_packet_count']}`",
        f"- Total exact packets after this gate: `{summary['total_packet_exact_after_three_parameter_gate']}` / `3`",
        f"- Remaining unresolved packets: `{summary['total_packet_unresolved_after_three_parameter_gate']}`",
        f"- Partial CNOT reduction if accepted: `{summary['partial_candidate_cnot_reduction_if_accepted']}`",
        f"- Remaining unrepaired off-grid replacement parameters: `{summary['remaining_unrepaired_replacement_off_pi_over_four_parameter_count']}`",
        f"- Accepted occurrence/proxy-T reduction: `{summary['accepted_occurrence_removal']}` / `{summary['accepted_proxy_t_reduction']}`",
        f"- Validation errors: `{summary['validation_error_count']}`",
        "",
        "## Packet Rows",
        "",
        "| Candidate line | Replacement CX | 2-param residual | Best 3-param residual | Exact 3-param pass | Exact indices | Accepted rewrite |",
        "|---:|---:|---:|---:|---|---|---|",
    ]
    for row in payload["three_parameter_local_u3_repair_rows"]:
        exact_indices = row["exact_three_parameter_free_indices"]
        lines.append(
            f"| {row['candidate_line_number']} | {row['replacement_cnot_count']} | "
            f"{row['source_best_two_parameter_residual_norm']:.6e} | "
            f"{row['best_three_parameter_residual_norm']:.6e} | "
            f"{row['three_parameter_exact_pass']} | "
            f"{exact_indices if exact_indices is not None else 'None'} | "
            f"{row['accepted_three_parameter_repair_as_full_circuit_rewrite']} |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "Line 268 now has a bounded packet-level exact repair after freeing three local-U3 parameters, while line 1381 remains unrepaired after all exactly-three-parameter combinations. The project still has only 2/3 bounded packet repairs, no symbolic exact decomposition, no full-circuit replay certificate, and no B7 occurrence/proxy-T saving.",
            "",
            "## Next Required Gate",
            "",
            "The next route must repair line 1381 with a broader scaffold, prove a scoped obstruction for this reduced-CNOT family, or abandon the reduced-CNOT scaffold for a different occurrence-removing route.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", type=Path, default=JSON_OUT)
    parser.add_argument("--markdown-output", type=Path, default=MD_OUT)
    parser.add_argument("--max-nfev", type=int, default=DEFAULT_MAX_NFEV)
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_payload(args.max_nfev)
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
