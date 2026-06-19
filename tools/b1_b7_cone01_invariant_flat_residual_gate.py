#!/usr/bin/env python3
"""Residual obligation gate for B1/B7 cone_01 invariant-flat windows.

The previous local-equivalence invariant gate blocked local-only absorption for
24 of 35 cone_01 windows, but left 11 invariant-flat windows. This gate does
not solve those windows. It turns them into a replayable residual work packet
and quantifies why solving only that subset is insufficient for the B7
occurrence-ledger target.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "results" / "B1_B7_cone01_local_invariant_obligation_gate_v0.json"
JSON_OUT = ROOT / "results" / "B1_B7_cone01_invariant_flat_residual_gate_v0.json"
MD_OUT = ROOT / "research" / "B1_B7_cone01_invariant_flat_residual_gate.md"

METHOD = "b1_b7_cone01_invariant_flat_residual_gate_v0"
STATUS = "cone01_invariant_flat_residual_obligation_not_rewrite_certificate"
MODEL_STATUS = "residual_flat_window_work_packet_not_semantic_certificate"
PROXY_T_PER_OCCURRENCE = 20
REQUIRED_OCCURRENCE_REMOVALS = 30


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def normalize_window_text(row: dict[str, Any]) -> list[str]:
    target = f"q[{row['qubit']}]"
    partner = f"q[{row['partner']}]"
    normalized = []
    for text in row["window_text"]:
        normalized.append(text.replace(partner, "q[partner]").replace(target, "q[target]"))
    return normalized


def pattern_key(row: dict[str, Any]) -> tuple[str, tuple[str, ...]]:
    return (row["original_ry_params"], tuple(normalize_window_text(row)))


def build_payload() -> dict[str, Any]:
    source = load_json(SOURCE_PATH)
    source_summary = source.get("summary", {})
    flat_windows = source.get("invariant_flat_windows", [])
    sensitive_count = int(source_summary.get("local_equivalence_sensitive_count", 0))
    candidate_count = int(source_summary.get("candidate_window_count", 0))
    flat_count = len(flat_windows)

    theta_counts = Counter(row["original_ry_params"] for row in flat_windows)
    partner_counts = Counter(str(row["partner"]) for row in flat_windows)
    target_qubit_counts = Counter(str(row["qubit"]) for row in flat_windows)
    groups: dict[tuple[str, tuple[str, ...]], list[dict[str, Any]]] = defaultdict(list)
    for row in flat_windows:
        groups[pattern_key(row)].append(row)

    pattern_groups = []
    for index, ((theta, normalized_window), rows) in enumerate(
        sorted(groups.items(), key=lambda item: (-len(item[1]), item[0][0])),
        start=1,
    ):
        pattern_groups.append(
            {
                "pattern_id": f"flat_pattern_{index:02d}",
                "theta": theta,
                "occurrence_count": len(rows),
                "line_numbers": [row["line_number"] for row in rows],
                "target_qubits": sorted({row["qubit"] for row in rows}),
                "partner_qubits": sorted({row["partner"] for row in rows}),
                "normalized_window_text": list(normalized_window),
                "nearest_grid_labels": sorted({row["nearest_pi_over_four_label"] for row in rows}),
                "max_distance_to_nearest_pi_over_four": max(
                    float(row["distance_to_nearest_pi_over_four"]) for row in rows
                ),
            }
        )

    max_flat_occurrence_removal = flat_count
    max_flat_proxy_t_reduction = max_flat_occurrence_removal * PROXY_T_PER_OCCURRENCE
    missing_occurrences_after_all_flat_solved = max(
        0, REQUIRED_OCCURRENCE_REMOVALS - max_flat_occurrence_removal
    )
    missing_proxy_t_after_all_flat_solved = (
        missing_occurrences_after_all_flat_solved * PROXY_T_PER_OCCURRENCE
    )

    residual_packets = []
    for row in sorted(flat_windows, key=lambda item: item["line_number"]):
        residual_packets.append(
            {
                "line_number": row["line_number"],
                "op_index": row["op_index"],
                "target_qubit": row["qubit"],
                "partner_qubit": row["partner"],
                "theta": row["original_ry_params"],
                "previous_cx_line": row["previous_cx_line"],
                "next_cx_line": row["next_cx_line"],
                "window_operation_count": row["window_operation_count"],
                "invariant_derivative_norm": row["local_equivalence_invariant_derivative_norm"],
                "nearest_grid_invariant_distance": row["nearest_grid_invariant_distance"],
                "distance_to_nearest_pi_over_four": row["distance_to_nearest_pi_over_four"],
                "normalized_window_text": normalize_window_text(row),
                "required_next_evidence": [
                    "exact local two-qubit synthesis certificate",
                    "KAK/Clifford-scaffold theorem for this normalized pattern",
                    "or occurrence-removing rewrite replay accepted by the B7 ledger",
                ],
            }
        )

    summary = {
        "source_method": source.get("method"),
        "candidate_window_count": candidate_count,
        "local_equivalence_sensitive_count": sensitive_count,
        "invariant_flat_window_count": flat_count,
        "flat_window_fraction": flat_count / candidate_count if candidate_count else 0.0,
        "distinct_flat_theta_count": len(theta_counts),
        "largest_flat_theta_group_count": max(theta_counts.values()) if theta_counts else 0,
        "distinct_flat_pattern_count": len(pattern_groups),
        "all_flat_windows_share_single_partner": len(partner_counts) == 1,
        "flat_window_partner_counts": dict(sorted(partner_counts.items())),
        "flat_window_target_qubit_count": len(target_qubit_counts),
        "required_occurrence_removals_for_b7_target": REQUIRED_OCCURRENCE_REMOVALS,
        "proxy_t_per_occurrence": PROXY_T_PER_OCCURRENCE,
        "target_proxy_t_ledger_reduction_for_gcm_h6_1_20": REQUIRED_OCCURRENCE_REMOVALS
        * PROXY_T_PER_OCCURRENCE,
        "max_occurrence_removal_if_all_flat_windows_solved": max_flat_occurrence_removal,
        "max_proxy_t_reduction_if_all_flat_windows_solved": max_flat_proxy_t_reduction,
        "all_flat_windows_solved_clears_b7_target": max_flat_occurrence_removal
        >= REQUIRED_OCCURRENCE_REMOVALS,
        "missing_occurrences_after_all_flat_windows_solved": missing_occurrences_after_all_flat_solved,
        "missing_proxy_t_after_all_flat_windows_solved": missing_proxy_t_after_all_flat_solved,
        "rewrite_claimed": False,
        "semantic_certificate_claimed": False,
        "resource_saving_claimed": False,
        "kak_theorem_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "validation_error_count": None,
    }
    payload = {
        "benchmark_id": "B1",
        "problem_id": 25,
        "linked_b7_problem_id": 21,
        "title": "B1/B7 cone_01 invariant-flat residual gate",
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "method": METHOD,
        "source_result": display_path(SOURCE_PATH),
        "source_method": source.get("method"),
        "workload": "qasmbench_medium_exact/gcm_h6.qasm",
        "summary": summary,
        "flat_theta_counts": dict(sorted(theta_counts.items())),
        "flat_pattern_groups": pattern_groups,
        "residual_window_packets": residual_packets,
        "claim_boundary": {
            "rewrite_claimed": False,
            "semantic_certificate_claimed": False,
            "resource_saving_claimed": False,
            "kak_theorem_claimed": False,
            "b7_ledger_improvement_claimed": False,
            "supported_claim": (
                "The 11 invariant-flat cone_01 windows are now isolated into "
                "three normalized pattern groups and remain explicit residual obligations."
            ),
            "unsupported_claims": [
                "This is not an occurrence-removing rewrite certificate.",
                "Solving all 11 invariant-flat windows would still miss the 30-occurrence B7 target by 19 occurrences.",
                "No B7 proxy-T ledger reduction is counted.",
                "No KAK theorem or semantic equivalence proof is claimed.",
            ],
        },
    }
    errors = validate(payload)
    payload["summary"]["validation_error_count"] = len(errors)
    payload["validation_errors"] = errors
    return payload


def validate(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    summary = payload["summary"]
    claims = payload["claim_boundary"]
    if payload.get("method") != METHOD:
        errors.append("method_mismatch")
    if payload.get("source_method") != "b1_b7_cone01_local_invariant_obligation_gate_v0":
        errors.append("source_method_mismatch")
    if summary.get("candidate_window_count") != 35:
        errors.append("candidate_window_count_mismatch")
    if summary.get("local_equivalence_sensitive_count") != 24:
        errors.append("sensitive_window_count_mismatch")
    if summary.get("invariant_flat_window_count") != 11:
        errors.append("flat_window_count_mismatch")
    if summary.get("distinct_flat_theta_count") != 3:
        errors.append("distinct_flat_theta_count_mismatch")
    if summary.get("distinct_flat_pattern_count") != 3:
        errors.append("distinct_flat_pattern_count_mismatch")
    if summary.get("all_flat_windows_share_single_partner") is not True:
        errors.append("flat_windows_should_share_partner")
    if summary.get("max_occurrence_removal_if_all_flat_windows_solved") != 11:
        errors.append("max_flat_occurrence_removal_mismatch")
    if summary.get("max_proxy_t_reduction_if_all_flat_windows_solved") != 220:
        errors.append("max_flat_proxy_t_reduction_mismatch")
    if summary.get("all_flat_windows_solved_clears_b7_target") is not False:
        errors.append("flat_windows_should_not_clear_b7_target")
    if summary.get("missing_occurrences_after_all_flat_windows_solved") != 19:
        errors.append("missing_occurrences_mismatch")
    if summary.get("missing_proxy_t_after_all_flat_windows_solved") != 380:
        errors.append("missing_proxy_t_mismatch")
    for field in [
        "rewrite_claimed",
        "semantic_certificate_claimed",
        "resource_saving_claimed",
        "kak_theorem_claimed",
        "b7_ledger_improvement_claimed",
    ]:
        if summary.get(field) is not False or claims.get(field) is not False:
            errors.append(f"forbidden_claim_{field}")
    if len(payload.get("residual_window_packets", [])) != 11:
        errors.append("residual_packet_count_mismatch")
    return errors


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    summary = payload["summary"]
    lines = [
        "# B1/B7 Cone 01 Invariant-Flat Residual Gate",
        "",
        f"Status: `{payload['status']}`",
        "",
        "This artifact isolates the `cone_01` windows that were not blocked by "
        "the local-equivalence invariant diagnostic. It is a residual work packet, "
        "not a rewrite certificate and not a B7 resource claim.",
        "",
        "## Summary",
        "",
        f"- Candidate windows: `{summary['candidate_window_count']}`",
        f"- Local-equivalence sensitive windows: `{summary['local_equivalence_sensitive_count']}`",
        f"- Invariant-flat windows: `{summary['invariant_flat_window_count']}`",
        f"- Distinct flat theta groups: `{summary['distinct_flat_theta_count']}`",
        f"- Distinct normalized flat patterns: `{summary['distinct_flat_pattern_count']}`",
        f"- All flat windows share one partner: `{summary['all_flat_windows_share_single_partner']}`",
        f"- B7 required occurrence removals: `{summary['required_occurrence_removals_for_b7_target']}`",
        f"- Max occurrence removal if all flat windows are solved: `{summary['max_occurrence_removal_if_all_flat_windows_solved']}`",
        f"- Max proxy-T reduction if all flat windows are solved: `{summary['max_proxy_t_reduction_if_all_flat_windows_solved']}`",
        f"- Missing occurrences after all flat windows are solved: `{summary['missing_occurrences_after_all_flat_windows_solved']}`",
        f"- Missing proxy-T after all flat windows are solved: `{summary['missing_proxy_t_after_all_flat_windows_solved']}`",
        "",
        "## Pattern Groups",
        "",
        "| Pattern | Occurrences | Theta | Lines | Target qubits | Normalized window |",
        "|---|---:|---|---|---|---|",
    ]
    for group in payload["flat_pattern_groups"]:
        lines.append(
            "| {pattern_id} | {occurrence_count} | `{theta}` | {lines} | {targets} | `{window}` |".format(
                pattern_id=group["pattern_id"],
                occurrence_count=group["occurrence_count"],
                theta=group["theta"],
                lines=group["line_numbers"],
                targets=group["target_qubits"],
                window=" ".join(group["normalized_window_text"]),
            )
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- No occurrence-removing rewrite is claimed.",
            "- No KAK theorem or semantic equivalence theorem is claimed.",
            "- No B7 ledger improvement is counted.",
            "- Solving all 11 invariant-flat windows would still leave 19 occurrences / 380 proxy-T units missing for the current one-sided 1.20x `gcm_h6` target.",
            "",
            f"Validation error count: `{summary['validation_error_count']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path, default=JSON_OUT)
    parser.add_argument("--markdown-output", type=Path, default=MD_OUT)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    payload = build_payload()
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload, args.markdown_output)
    if args.pretty:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Wrote {args.json_output}")
        print(f"Wrote {args.markdown_output}")


if __name__ == "__main__":
    main()
