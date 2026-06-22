#!/usr/bin/env python3
"""Grid-snap pricing gate for the B1/B7 cone_01 union-region census candidates.

T-B1-004bf found four exact two-CNOT orientation-sequence candidates for the
line-1378/1381 union target, while T-B1-004bg rejected that route as pricing
dominated by the current line-1381 patch boundary. This gate checks the cheap
escape hatch: snap every local-U3 parameter in each exact census candidate to
the pi/4 grid and replay the same union target.

All four grid-snapped census candidates fail exact replay, so the union census
route cannot be accepted by pretending its local-U3 burden is grid-priced for
free. This is a scoped pricing gate, not a global synthesis lower bound.
"""

from __future__ import annotations

import argparse
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
from b1_b7_cone01_local_u3_exactification_gate import snap_to_pi_over_four, wrap_angle
from b1_b7_cone01_packet_synthesis_search_gate import (
    EXACT_TOLERANCE,
    parameter_stats,
    residual_norm,
    target_matrix,
)
from b1_b7_cone01_union_region_two_cnot_orientation_census_gate import (
    mixed_scaffold_unitary,
)


ROOT = Path(__file__).resolve().parents[1]
SEMANTIC_PACKET_PATH = ROOT / "results" / "B1_B7_cone01_semantic_replay_packet_gate_v0.json"
ORIENTATION_CENSUS_PATH = (
    ROOT / "results" / "B1_B7_cone01_union_region_two_cnot_orientation_census_gate_v0.json"
)
PRICING_DOMINANCE_PATH = (
    ROOT / "results" / "B1_B7_cone01_union_region_pricing_dominance_gate_v0.json"
)
JSON_OUT = ROOT / "results" / "B1_B7_cone01_union_region_grid_snap_pricing_gate_v0.json"
MD_OUT = ROOT / "research" / "B1_B7_cone01_union_region_grid_snap_pricing_gate.md"

METHOD = "b1_b7_cone01_union_region_grid_snap_pricing_gate_v0"
STATUS = "cone01_union_region_grid_snap_pricing_rejected"
MODEL_STATUS = "two_cnot_union_census_candidates_do_not_become_grid_priced"
TARGET_LINE = 1381


def line_packet(payload: dict[str, Any], line_number: int) -> dict[str, Any]:
    for packet in payload.get("semantic_replay_packets", []):
        if int(packet["candidate_line_number"]) == line_number:
            return packet
    raise ValueError(f"missing semantic packet line {line_number}")


def snap_parameters(values: list[float]) -> tuple[np.ndarray, list[float]]:
    snapped = []
    errors = []
    for value in values:
        grid_value = float(wrap_angle(snap_to_pi_over_four(float(value))))
        snapped.append(grid_value)
        errors.append(abs(float(value) - grid_value))
    return np.array(snapped, dtype=float), errors


def run_probe() -> dict[str, Any]:
    semantic = load_json(SEMANTIC_PACKET_PATH)
    census = load_json(ORIENTATION_CENSUS_PATH)
    dominance = load_json(PRICING_DOMINANCE_PATH)
    packet = line_packet(semantic, TARGET_LINE)
    matrix = target_matrix(packet)
    rows = []
    for row in census["union_region_two_cnot_orientation_rows"]:
        params = [float(value) for value in row["best"]["wrapped_parameters"]]
        snapped, snap_errors = snap_parameters(params)
        sequence = [(int(control), int(target)) for control, target in row["cnot_sequence"]]
        residual = residual_norm(mixed_scaffold_unitary(snapped, sequence), matrix)
        source_stats = parameter_stats(params)
        snapped_stats = parameter_stats(snapped.tolist())
        exact_pass = residual <= EXACT_TOLERANCE
        rows.append(
            {
                "sequence_id": row["sequence_id"],
                "cnot_sequence": row["cnot_sequence"],
                "source_residual_norm": row["best"]["residual_norm"],
                "source_off_pi_over_four_parameter_count": source_stats[
                    "off_pi_over_four_grid_parameter_count"
                ],
                "source_nonzero_parameter_count": source_stats["nonzero_parameter_count"],
                "snapped_off_pi_over_four_parameter_count": snapped_stats[
                    "off_pi_over_four_grid_parameter_count"
                ],
                "snapped_nonzero_parameter_count": snapped_stats["nonzero_parameter_count"],
                "snapped_residual_norm": residual,
                "snapped_residual_ratio_to_exact_tolerance": residual / EXACT_TOLERANCE,
                "exact_pass_after_grid_snap": exact_pass,
                "max_absolute_snap_error": max(snap_errors),
                "mean_absolute_snap_error": float(np.mean(snap_errors)),
            }
        )

    exact_pass_count = sum(1 for row in rows if row["exact_pass_after_grid_snap"])
    best_row = min(rows, key=lambda row: row["snapped_residual_norm"])
    worst_row = max(rows, key=lambda row: row["snapped_residual_norm"])
    accepted_removed = 0
    summary = {
        "source_semantic_packet_method": semantic.get("method"),
        "source_orientation_census_method": census.get("method"),
        "source_pricing_dominance_method": dominance.get("method"),
        "target_line_number": TARGET_LINE,
        "union_window": [
            int(packet["window_start_line"]),
            int(packet["window_end_line"]),
        ],
        "support_qubits": packet["support_qubits"],
        "source_cnot_count": int(packet["cx_count"]),
        "searched_cnot_count": 2,
        "orientation_sequence_count": len(rows),
        "orientation_sequence_ids": [row["sequence_id"] for row in rows],
        "all_grid_snap_row_count": len(rows),
        "all_grid_snap_exact_pass_count": exact_pass_count,
        "all_grid_snap_exact_fail_count": len(rows) - exact_pass_count,
        "all_grid_snaps_fail": exact_pass_count == 0,
        "best_grid_snap_sequence_id": best_row["sequence_id"],
        "best_grid_snap_residual_norm": best_row["snapped_residual_norm"],
        "best_grid_snap_residual_ratio_to_exact_tolerance": best_row[
            "snapped_residual_ratio_to_exact_tolerance"
        ],
        "worst_grid_snap_sequence_id": worst_row["sequence_id"],
        "worst_grid_snap_residual_norm": worst_row["snapped_residual_norm"],
        "worst_grid_snap_residual_ratio_to_exact_tolerance": worst_row[
            "snapped_residual_ratio_to_exact_tolerance"
        ],
        "best_source_off_pi_over_four_parameter_count": min(
            row["source_off_pi_over_four_parameter_count"] for row in rows
        ),
        "best_source_proxy_t_pressure": dominance["summary"][
            "min_census_proxy_t_pressure"
        ],
        "current_line1381_proxy_t_pressure": dominance["summary"][
            "current_line1381_proxy_t_pressure"
        ],
        "grid_snap_pricing_accepted": False,
        "local_u3_pricing_completed": False,
        "accepted_full_circuit_replay_certificate_count": 0,
        "accepted_full_circuit_qasm_patch_count": 0,
        "accepted_occurrence_removal": accepted_removed,
        "accepted_proxy_t_reduction": 0,
        "missing_occurrences_after_gate": max(0, REQUIRED_OCCURRENCE_REMOVALS - accepted_removed),
        "missing_proxy_t_after_gate": max(
            0,
            (REQUIRED_OCCURRENCE_REMOVALS - accepted_removed) * PROXY_T_PER_OCCURRENCE,
        ),
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
        "source_semantic_packet_result": display_path(SEMANTIC_PACKET_PATH),
        "source_orientation_census_result": display_path(ORIENTATION_CENSUS_PATH),
        "source_pricing_dominance_result": display_path(PRICING_DOMINANCE_PATH),
        "summary": summary,
        "union_region_grid_snap_rows": rows,
        "claim_boundary": {
            "supported_claim": (
                "Within the T-B1-004bf union-region two-CNOT census candidates, "
                "snapping all local-U3 parameters to the pi/4 grid does not produce "
                "an exact replay of the union target."
            ),
            "unsupported_claims": [
                "This is not a global lower bound for the union target.",
                "This does not rule out a different scaffold or symbolic absorption.",
                "This does not accept local-U3 pricing, occurrence removal, or a B7 ledger improvement.",
            ],
            "grid_snap_pricing_accepted": False,
            "local_u3_pricing_completed": False,
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
    }
    payload["summary"]["validation_error_count"] = len(validate_payload(payload))
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    summary = payload.get("summary", {})
    rows = payload.get("union_region_grid_snap_rows", [])
    expected = {
        "target_line_number": 1381,
        "union_window": [1369, 1379],
        "support_qubits": [4, 8],
        "source_cnot_count": 5,
        "searched_cnot_count": 2,
        "orientation_sequence_count": 4,
        "all_grid_snap_row_count": 4,
        "all_grid_snap_exact_pass_count": 0,
        "all_grid_snap_exact_fail_count": 4,
        "all_grid_snaps_fail": True,
        "best_grid_snap_sequence_id": "10-10",
        "best_grid_snap_residual_norm": 0.36435162331693166,
        "best_grid_snap_residual_ratio_to_exact_tolerance": 36435162.331693165,
        "worst_grid_snap_sequence_id": "10-01",
        "worst_grid_snap_residual_norm": 1.021457442072864,
        "worst_grid_snap_residual_ratio_to_exact_tolerance": 102145744.20728639,
        "best_source_off_pi_over_four_parameter_count": 13,
        "best_source_proxy_t_pressure": 260,
        "current_line1381_proxy_t_pressure": 100,
        "grid_snap_pricing_accepted": False,
        "local_u3_pricing_completed": False,
        "accepted_full_circuit_replay_certificate_count": 0,
        "accepted_full_circuit_qasm_patch_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "missing_occurrences_after_gate": 30,
        "missing_proxy_t_after_gate": 600,
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
    if len(rows) != 4:
        errors.append(f"row_count_expected_4_got_{len(rows)}")
    if any(row.get("exact_pass_after_grid_snap") for row in rows):
        errors.append("unexpected_grid_snap_exact_pass")
    if any(row.get("snapped_off_pi_over_four_parameter_count") != 0 for row in rows):
        errors.append("grid_snap_rows_must_have_zero_off_grid_parameters")
    if payload.get("claim_boundary", {}).get("b7_ledger_improvement_claimed") is not False:
        errors.append("claim_boundary_b7_ledger_improvement_claimed_not_false")
    return errors


def markdown_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# B1/B7 cone_01 Union-Region Grid-Snap Pricing Gate",
        "",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Model status: `{payload['model_status']}`",
        f"- Workload: `{payload['workload']}`",
        f"- Source orientation census: `{payload['source_orientation_census_result']}`",
        f"- Source pricing dominance: `{payload['source_pricing_dominance_result']}`",
        "",
        "## Result",
        "",
        f"- Orientation sequences: `{summary['orientation_sequence_ids']}`",
        f"- Grid-snap exact pass / fail: `{summary['all_grid_snap_exact_pass_count']}` / `{summary['all_grid_snap_exact_fail_count']}`",
        f"- Best grid-snap residual: `{summary['best_grid_snap_residual_norm']}` at `{summary['best_grid_snap_sequence_id']}`",
        f"- Worst grid-snap residual: `{summary['worst_grid_snap_residual_norm']}` at `{summary['worst_grid_snap_sequence_id']}`",
        f"- Best source off-grid parameters / proxy-T pressure: `{summary['best_source_off_pi_over_four_parameter_count']}` / `{summary['best_source_proxy_t_pressure']}`",
        f"- Current line-1381 proxy-T pressure: `{summary['current_line1381_proxy_t_pressure']}`",
        f"- Grid-snap pricing accepted: `{summary['grid_snap_pricing_accepted']}`",
        f"- Accepted occurrence / proxy-T reduction / B7 claim: `{summary['accepted_occurrence_removal']}` / `{summary['accepted_proxy_t_reduction']}` / `{summary['b7_ledger_improvement_claimed']}`",
        "",
        "## Rows",
        "",
        "| Sequence | Source off-grid | Grid residual | Ratio to tolerance | Exact after snap |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for row in payload["union_region_grid_snap_rows"]:
        lines.append(
            "| "
            f"{row['sequence_id']} | "
            f"{row['source_off_pi_over_four_parameter_count']} | "
            f"{row['snapped_residual_norm']:.12g} | "
            f"{row['snapped_residual_ratio_to_exact_tolerance']:.6g} | "
            f"{row['exact_pass_after_grid_snap']} |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- This is a scoped grid-snap pricing rejection for the T-B1-004bf union-region census candidates.",
            "- It is not a global union-region lower bound and does not accept occurrence removal or B7 ledger credit.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", default=str(JSON_OUT))
    parser.add_argument("--markdown-output", default=str(MD_OUT))
    args = parser.parse_args()
    payload = run_probe()
    write_json(Path(args.json_output), payload, True)
    write_text(Path(args.markdown_output), markdown_report(payload))
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
