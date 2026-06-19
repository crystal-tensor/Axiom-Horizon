#!/usr/bin/env python3
"""Absorption/exactification gate for B1/B7 cone_01 local dressing.

T-B1-004r found numerical SU(2)xSU(2) local dressings for the three
invariant-flat pattern packets. This gate asks the next resource-accounting
question: can those continuous dressing parameters be snapped to the exact
pi/4 grid, shared across pattern packets, or otherwise accepted as an
occurrence-removing certificate?

The expected output today is a negative gate. A small continuous residual is
not enough for B7. The dressing must survive exactification or carry a replay
certificate before it can remove occurrences from the fault-tolerant ledger.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from b1_b7_cone01_flat_pattern_kak_packet import parse_normalized_op, replace_target_ry_with_grid
from b1_b7_cone01_local_dressing_search_gate import dressed_unitary
from b1_b7_cone01_phase_removal_gate import EXACT_TOLERANCE, residual_norm, unitary_for_ops


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DRESSING_PATH = ROOT / "results" / "B1_B7_cone01_local_dressing_search_gate_v0.json"
SOURCE_PACKET_PATH = ROOT / "results" / "B1_B7_cone01_flat_pattern_kak_packet_v0.json"
JSON_OUT = ROOT / "results" / "B1_B7_cone01_dressing_absorption_gate_v0.json"
MD_OUT = ROOT / "research" / "B1_B7_cone01_dressing_absorption_gate.md"

METHOD = "b1_b7_cone01_dressing_absorption_gate_v0"
STATUS = "cone01_dressing_absorption_negative_gate"
MODEL_STATUS = "off_grid_local_dressing_not_absorbed_or_exactified"
PROXY_T_PER_OCCURRENCE = 20
REQUIRED_OCCURRENCE_REMOVALS = 30
GRID_TOLERANCE = 1e-6
NEAR_GRID_TOLERANCE = 1e-2


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict[str, Any], pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2 if pretty else None, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def nearest_pi_over_four(value: float) -> float:
    return round(value / (math.pi / 4.0)) * (math.pi / 4.0)


def grid_label(value: float) -> int:
    return int(round(value / (math.pi / 4.0)))


def grid_distance(value: float) -> float:
    return abs(float(value) - nearest_pi_over_four(float(value)))


def reconstruct_pattern(packet: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    ops = [parse_normalized_op(text) for text in packet["normalized_window_text"]]
    target = unitary_for_ops(ops, [0, 1])
    grid_ops = replace_target_ry_with_grid(ops, float(packet["nearest_grid_angle"]))
    return target, unitary_for_ops(grid_ops, [0, 1])


def residual_for_params(grid_unitary: np.ndarray, target: np.ndarray, values: list[float]) -> float:
    return residual_norm(dressed_unitary(grid_unitary, np.array(values, dtype=float)), target)


def single_snap_residuals(
    grid_unitary: np.ndarray, target: np.ndarray, values: list[float], off_grid_indices: list[int]
) -> list[dict[str, Any]]:
    rows = []
    for index in off_grid_indices:
        trial = list(values)
        trial[index] = nearest_pi_over_four(trial[index])
        rows.append(
            {
                "parameter_index": index,
                "grid_distance_before_snap": grid_distance(values[index]),
                "residual_norm_after_single_snap": residual_for_params(grid_unitary, target, trial),
            }
        )
    rows.sort(key=lambda row: row["residual_norm_after_single_snap"])
    return rows


def analyze_pattern(
    packet: dict[str, Any], dressing_row: dict[str, Any]
) -> dict[str, Any]:
    target, grid_unitary = reconstruct_pattern(packet)
    wrapped = [float(value) for value in dressing_row["best_attempt"]["wrapped_parameters"]]
    snapped = [nearest_pi_over_four(value) for value in wrapped]
    distances = [grid_distance(value) for value in wrapped]
    off_grid_indices = [index for index, distance in enumerate(distances) if distance > GRID_TOLERANCE]
    near_grid_indices = [index for index, distance in enumerate(distances) if GRID_TOLERANCE < distance <= NEAR_GRID_TOLERANCE]
    far_off_grid_indices = [index for index, distance in enumerate(distances) if distance > NEAR_GRID_TOLERANCE]
    projected_residual = residual_for_params(grid_unitary, target, snapped)
    single_rows = single_snap_residuals(grid_unitary, target, wrapped, off_grid_indices)
    return {
        "pattern_id": dressing_row["pattern_id"],
        "occurrence_count": dressing_row["occurrence_count"],
        "nearest_grid_label": dressing_row["nearest_grid_label"],
        "source_local_dressing_residual_norm": dressing_row["best_local_dressing_residual_norm"],
        "pi_over_four_projected_residual_norm": projected_residual,
        "pi_over_four_projection_exact_pass": projected_residual <= EXACT_TOLERANCE,
        "grid_signature": [grid_label(value) for value in wrapped],
        "off_grid_parameter_indices": off_grid_indices,
        "off_grid_parameter_count": len(off_grid_indices),
        "near_grid_parameter_count": len(near_grid_indices),
        "far_off_grid_parameter_count": len(far_off_grid_indices),
        "max_grid_distance": max(distances, default=0.0),
        "sum_grid_distance": sum(distances),
        "best_single_parameter_snap_residual_norm": single_rows[0]["residual_norm_after_single_snap"] if single_rows else 0.0,
        "single_parameter_snap_exact_pass_count": sum(
            1 for row in single_rows if row["residual_norm_after_single_snap"] <= EXACT_TOLERANCE
        ),
        "single_parameter_snap_trials": single_rows,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "absorption_certificate_claimed": False,
        "exactification_certificate_claimed": False,
        "shared_dressing_certificate_claimed": False,
    }


def build_payload() -> dict[str, Any]:
    dressing = load_json(SOURCE_DRESSING_PATH)
    packet_payload = load_json(SOURCE_PACKET_PATH)
    packets = {packet["pattern_id"]: packet for packet in packet_payload["pattern_packets"]}
    pattern_rows = [
        analyze_pattern(packets[row["pattern_id"]], row)
        for row in dressing["pattern_dressing_results"]
    ]
    signature_count = len({tuple(row["grid_signature"]) for row in pattern_rows})
    projected_pass_count = sum(1 for row in pattern_rows if row["pi_over_four_projection_exact_pass"])
    accepted_occurrence_removal = sum(row["accepted_occurrence_removal"] for row in pattern_rows)
    total_off_grid = sum(row["off_grid_parameter_count"] for row in pattern_rows)
    total_near_grid = sum(row["near_grid_parameter_count"] for row in pattern_rows)
    missing_occurrences = REQUIRED_OCCURRENCE_REMOVALS - accepted_occurrence_removal
    summary = {
        "source_method": dressing.get("method"),
        "source_status": dressing.get("status"),
        "pattern_group_count": len(pattern_rows),
        "covered_invariant_flat_occurrence_count": sum(int(row["occurrence_count"]) for row in pattern_rows),
        "source_local_dressing_exact_pass_count": dressing["summary"].get("local_dressing_exact_pass_count"),
        "pi_over_four_projection_exact_pass_count": projected_pass_count,
        "all_pi_over_four_projections_exact": projected_pass_count == len(pattern_rows),
        "max_pi_over_four_projected_residual_norm": max(
            (row["pi_over_four_projected_residual_norm"] for row in pattern_rows), default=0.0
        ),
        "min_pi_over_four_projected_residual_norm": min(
            (row["pi_over_four_projected_residual_norm"] for row in pattern_rows), default=0.0
        ),
        "unique_grid_signature_count": signature_count,
        "shared_grid_signature_across_patterns": signature_count == 1,
        "total_off_grid_local_dressing_parameter_count": total_off_grid,
        "total_near_grid_local_dressing_parameter_count": total_near_grid,
        "total_far_off_grid_local_dressing_parameter_count": total_off_grid - total_near_grid,
        "max_grid_distance": max((row["max_grid_distance"] for row in pattern_rows), default=0.0),
        "single_parameter_snap_exact_pass_count": sum(
            row["single_parameter_snap_exact_pass_count"] for row in pattern_rows
        ),
        "accepted_occurrence_removal": accepted_occurrence_removal,
        "accepted_proxy_t_reduction": 0,
        "required_occurrence_removals_for_b7_target": REQUIRED_OCCURRENCE_REMOVALS,
        "missing_occurrences_after_gate": missing_occurrences,
        "missing_proxy_t_after_gate": missing_occurrences * PROXY_T_PER_OCCURRENCE,
        "absorption_certificate_claimed": False,
        "exactification_certificate_claimed": False,
        "shared_dressing_certificate_claimed": False,
        "rewrite_claimed": False,
        "semantic_certificate_claimed": False,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "validation_error_count": None,
    }
    payload = {
        "benchmark_id": "B1",
        "problem_id": 25,
        "linked_b7_problem_id": 21,
        "title": "B1/B7 cone_01 dressing absorption and exactification gate",
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "method": METHOD,
        "source_result": display_path(SOURCE_DRESSING_PATH),
        "source_method": dressing.get("method"),
        "source_packet_result": display_path(SOURCE_PACKET_PATH),
        "workload": "qasmbench_medium_exact/gcm_h6.qasm",
        "summary": summary,
        "pattern_absorption_results": pattern_rows,
        "claim_boundary": {
            "absorption_certificate_claimed": False,
            "exactification_certificate_claimed": False,
            "shared_dressing_certificate_claimed": False,
            "rewrite_claimed": False,
            "semantic_certificate_claimed": False,
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
            "supported_claim": (
                "Nearest pi/4-grid exactification, shared grid signatures, and single-parameter "
                "snap checks do not turn the T-B1-004r numerical dressings into accepted "
                "occurrence-removing certificates."
            ),
            "unsupported_claims": [
                "This does not prove that no other exact local dressing exists.",
                "This does not provide a replayable circuit rewrite certificate.",
                "This does not provide accepted B7 resource reduction.",
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
    if payload.get("method") != METHOD:
        errors.append("method_mismatch")
    if payload.get("status") != STATUS:
        errors.append("status_mismatch")
    if payload.get("source_method") != "b1_b7_cone01_local_dressing_search_gate_v0":
        errors.append("source_method_mismatch")
    if summary.get("pattern_group_count") != 3:
        errors.append("pattern_group_count_mismatch")
    if summary.get("covered_invariant_flat_occurrence_count") != 11:
        errors.append("covered_occurrence_count_mismatch")
    if summary.get("source_local_dressing_exact_pass_count") != 3:
        errors.append("source_local_dressing_exact_pass_count_mismatch")
    if summary.get("pi_over_four_projection_exact_pass_count") != 0:
        errors.append("projection_should_not_exact_pass")
    if summary.get("all_pi_over_four_projections_exact") is not False:
        errors.append("all_projection_flag_should_be_false")
    if summary.get("unique_grid_signature_count") != 3:
        errors.append("grid_signatures_should_not_share_across_patterns")
    if summary.get("shared_grid_signature_across_patterns") is not False:
        errors.append("shared_signature_flag_should_be_false")
    if summary.get("total_off_grid_local_dressing_parameter_count", 0) <= 0:
        errors.append("off_grid_parameter_count_should_be_positive")
    if summary.get("single_parameter_snap_exact_pass_count") != 0:
        errors.append("single_parameter_snap_should_not_exact_pass")
    if summary.get("accepted_occurrence_removal") != 0:
        errors.append("accepted_occurrence_removal_must_remain_zero")
    if summary.get("accepted_proxy_t_reduction") != 0:
        errors.append("accepted_proxy_t_reduction_must_remain_zero")
    if summary.get("missing_occurrences_after_gate") != 30:
        errors.append("missing_occurrences_after_gate_mismatch")
    if summary.get("missing_proxy_t_after_gate") != 600:
        errors.append("missing_proxy_t_after_gate_mismatch")
    for field in [
        "absorption_certificate_claimed",
        "exactification_certificate_claimed",
        "shared_dressing_certificate_claimed",
        "rewrite_claimed",
        "semantic_certificate_claimed",
        "resource_saving_claimed",
        "b7_ledger_improvement_claimed",
    ]:
        if summary.get(field) is not False or payload["claim_boundary"].get(field) is not False:
            errors.append(f"forbidden_claim_{field}")
    for row in payload.get("pattern_absorption_results", []):
        if row.get("pi_over_four_projection_exact_pass") is not False:
            errors.append(f"pattern_{row.get('pattern_id')}_projection_should_fail")
        if row.get("accepted_occurrence_removal") != 0:
            errors.append(f"pattern_{row.get('pattern_id')}_accepted_removal_nonzero")
        if row.get("off_grid_parameter_count", 0) <= 0:
            errors.append(f"pattern_{row.get('pattern_id')}_missing_off_grid_parameters")
    return errors


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    summary = payload["summary"]
    lines = [
        "# B1/B7 Cone 01 Dressing Absorption Gate",
        "",
        f"Status: `{payload['status']}`",
        "",
        "This artifact tests the next obligation after the numerical local-dressing search: whether the off-grid local dressing can be exactified to the pi/4 grid, shared across the three packets, or counted as an absorption certificate. It is a negative resource-accounting gate.",
        "",
        "## Summary",
        "",
        f"- Pattern groups: `{summary['pattern_group_count']}`",
        f"- Covered invariant-flat occurrences: `{summary['covered_invariant_flat_occurrence_count']}`",
        f"- Source local-dressing exact passes: `{summary['source_local_dressing_exact_pass_count']}`",
        f"- Pi/4 projection exact passes: `{summary['pi_over_four_projection_exact_pass_count']}`",
        f"- Unique pi/4 grid signatures: `{summary['unique_grid_signature_count']}`",
        f"- Total off-grid local dressing parameters: `{summary['total_off_grid_local_dressing_parameter_count']}`",
        f"- Total near-grid local dressing parameters: `{summary['total_near_grid_local_dressing_parameter_count']}`",
        f"- Single-parameter snap exact passes: `{summary['single_parameter_snap_exact_pass_count']}`",
        f"- Accepted occurrence removal: `{summary['accepted_occurrence_removal']}`",
        f"- Missing occurrences after this gate: `{summary['missing_occurrences_after_gate']}`",
        "",
        "## Pattern Results",
        "",
        "| Pattern | Occurrences | Grid | Source residual | Pi/4 projected residual | Off-grid params | Near-grid params | Best single snap residual | Accepted removal |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["pattern_absorption_results"]:
        lines.append(
            "| {pattern_id} | {occurrence_count} | `{grid}` | `{source:.12g}` | `{projected:.12g}` | `{off_grid}` | `{near_grid}` | `{single:.12g}` | `{accepted}` |".format(
                pattern_id=row["pattern_id"],
                occurrence_count=row["occurrence_count"],
                grid=row["nearest_grid_label"],
                source=row["source_local_dressing_residual_norm"],
                projected=row["pi_over_four_projected_residual_norm"],
                off_grid=row["off_grid_parameter_count"],
                near_grid=row["near_grid_parameter_count"],
                single=row["best_single_parameter_snap_residual_norm"],
                accepted=row["accepted_occurrence_removal"],
            )
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- The three numerical dressings are not accepted as resource savings after pi/4-grid exactification checks.",
            "- The three patterns have three distinct grid signatures, so this gate does not find a shared exact dressing object.",
            "- Single-parameter snapping does not produce an exact-pass certificate.",
            "- No absorption certificate, exactification certificate, semantic rewrite, resource saving, or B7 ledger improvement is claimed.",
            "",
            f"Validation error count: `{summary['validation_error_count']}`",
            "",
        ]
    )
    write_text(path, "\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", type=Path, default=JSON_OUT)
    parser.add_argument("--markdown-output", type=Path, default=MD_OUT)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    payload = build_payload()
    write_json(args.json_output, payload, pretty=args.pretty)
    write_markdown(payload, args.markdown_output)
    print(json.dumps(payload["summary"], indent=2 if args.pretty else None, sort_keys=True))
    return 0 if not payload["validation_errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
