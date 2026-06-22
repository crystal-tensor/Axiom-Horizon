#!/usr/bin/env python3
"""Two-free-parameter pricing gate for B1/B7 cone_01 union-region candidates.

T-B1-004bn showed that no exact 2-CNOT union-region candidate survives when all
local-U3 parameters are snapped to the pi/4 grid and only one parameter is
freed. This gate tests the next pricing rung: snap all local-U3 parameters to
the pi/4 grid, then free exactly two parameters and re-optimize that pair.

An exact pass here would create a 40-proxy-T union pricing candidate that still
needs a full-circuit QASM patch and replay certificate before B7 credit. A full
failure closes the cheap two-free-parameter union adoption route.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import least_squares

from b1_b7_cone01_carrier_absorption_inventory_gate import (
    PROXY_T_PER_OCCURRENCE,
    REQUIRED_OCCURRENCE_REMOVALS,
    display_path,
    load_json,
    write_json,
    write_text,
)
from b1_b7_cone01_local_u3_exactification_gate import wrap_angle
from b1_b7_cone01_packet_synthesis_search_gate import (
    EXACT_TOLERANCE,
    parameter_stats,
    residual_norm,
    residual_vector,
    target_matrix,
)
from b1_b7_cone01_union_region_one_free_parameter_pricing_gate import (
    GRID_SNAP_PATH,
    ORIENTATION_CENSUS_PATH,
    SEMANTIC_PACKET_PATH,
    TARGET_LINE,
    line_packet,
    snapped_parameters,
)
from b1_b7_cone01_union_region_two_cnot_orientation_census_gate import (
    mixed_scaffold_unitary,
)


ROOT = Path(__file__).resolve().parents[1]
ONE_FREE_PATH = (
    ROOT / "results" / "B1_B7_cone01_union_region_one_free_parameter_pricing_gate_v0.json"
)
JSON_OUT = (
    ROOT / "results" / "B1_B7_cone01_union_region_two_free_parameter_pricing_gate_v0.json"
)
MD_OUT = (
    ROOT / "research" / "B1_B7_cone01_union_region_two_free_parameter_pricing_gate.md"
)

METHOD = "b1_b7_cone01_union_region_two_free_parameter_pricing_gate_v0"
STATUS_REJECTED = "cone01_union_region_two_free_parameter_pricing_rejected"
STATUS_CANDIDATE = "cone01_union_region_two_free_parameter_candidate_needs_full_circuit_replay"
MODEL_REJECTED = "two_free_parameter_union_census_candidates_do_not_recover_exactness"
MODEL_CANDIDATE = "two_free_parameter_union_candidate_has_exact_local_replay_only"
DEFAULT_MAX_NFEV = 700


def two_free_seeds(
    base: np.ndarray,
    original: np.ndarray,
    pair: tuple[int, int],
) -> list[np.ndarray]:
    i, j = pair
    return [
        np.array([base[i], base[j]], dtype=float),
        np.array([original[i], original[j]], dtype=float),
        np.array([base[i], original[j]], dtype=float),
        np.array([original[i], base[j]], dtype=float),
        np.array([0.0, 0.0], dtype=float),
        np.array([math.pi / 4, -math.pi / 4], dtype=float),
        np.array([-math.pi / 4, math.pi / 4], dtype=float),
    ]


def optimize_two_parameters(
    base: np.ndarray,
    original: np.ndarray,
    pair: tuple[int, int],
    sequence: list[tuple[int, int]],
    target: np.ndarray,
    max_nfev: int,
) -> dict[str, Any]:
    i, j = pair

    def objective(values: np.ndarray) -> np.ndarray:
        trial = base.copy()
        trial[i] = values[0]
        trial[j] = values[1]
        return residual_vector(mixed_scaffold_unitary(trial, sequence), target)

    best: dict[str, Any] | None = None
    for seed_index, seed in enumerate(two_free_seeds(base, original, pair)):
        result = least_squares(
            objective,
            seed,
            method="trf",
            max_nfev=max_nfev,
            ftol=1e-12,
            xtol=1e-12,
            gtol=1e-12,
        )
        residual = float(np.linalg.norm(result.fun))
        if best is None or residual < best["residual_norm"]:
            repaired = base.copy()
            repaired[i] = result.x[0]
            repaired[j] = result.x[1]
            wrapped = [float(wrap_angle(value)) for value in repaired]
            best = {
                "free_parameter_pair": [i, j],
                "free_parameter_values": [
                    float(wrap_angle(result.x[0])),
                    float(wrap_angle(result.x[1])),
                ],
                "source_parameter_values": [float(original[i]), float(original[j])],
                "grid_parameter_values": [float(base[i]), float(base[j])],
                "residual_norm": residual,
                "residual_ratio_to_exact_tolerance": residual / EXACT_TOLERANCE,
                "exact_pass": residual <= EXACT_TOLERANCE,
                "optimizer_success": bool(result.success),
                "optimizer_nfev": int(result.nfev),
                "best_seed_index": seed_index,
                "repaired_parameter_stats": parameter_stats(wrapped),
            }
    assert best is not None
    return best


def run_probe(max_nfev: int) -> dict[str, Any]:
    semantic = load_json(SEMANTIC_PACKET_PATH)
    census = load_json(ORIENTATION_CENSUS_PATH)
    grid_snap = load_json(GRID_SNAP_PATH)
    one_free = load_json(ONE_FREE_PATH)
    packet = line_packet(semantic, TARGET_LINE)
    target = target_matrix(packet)

    trial_rows: list[dict[str, Any]] = []
    sequence_rows: list[dict[str, Any]] = []
    for row in census["union_region_two_cnot_orientation_rows"]:
        sequence = [(int(control), int(target_qubit)) for control, target_qubit in row["cnot_sequence"]]
        original = np.array([float(value) for value in row["best"]["wrapped_parameters"]], dtype=float)
        snapped = snapped_parameters(original.tolist())
        snapped_residual = residual_norm(mixed_scaffold_unitary(snapped, sequence), target)
        sequence_trials = []
        for pair in itertools.combinations(range(len(original)), 2):
            trial = optimize_two_parameters(
                snapped,
                original,
                pair,
                sequence,
                target,
                max_nfev,
            )
            trial.update(
                {
                    "sequence_id": row["sequence_id"],
                    "cnot_sequence": row["cnot_sequence"],
                }
            )
            sequence_trials.append(trial)
            trial_rows.append(trial)
        best_trial = min(sequence_trials, key=lambda trial: trial["residual_norm"])
        sequence_rows.append(
            {
                "sequence_id": row["sequence_id"],
                "cnot_sequence": row["cnot_sequence"],
                "source_residual_norm": row["best"]["residual_norm"],
                "source_off_pi_over_four_parameter_count": row["best"]["parameter_stats"][
                    "off_pi_over_four_grid_parameter_count"
                ],
                "grid_snap_residual_norm": snapped_residual,
                "two_free_trial_count": len(sequence_trials),
                "two_free_exact_pass_count": sum(
                    1 for trial in sequence_trials if trial["exact_pass"]
                ),
                "best_two_free_parameter_pair": best_trial["free_parameter_pair"],
                "best_two_free_residual_norm": best_trial["residual_norm"],
                "best_two_free_residual_ratio_to_exact_tolerance": best_trial[
                    "residual_ratio_to_exact_tolerance"
                ],
                "best_two_free_off_pi_over_four_parameter_count": best_trial[
                    "repaired_parameter_stats"
                ]["off_pi_over_four_grid_parameter_count"],
                "best_two_free_nonzero_parameter_count": best_trial[
                    "repaired_parameter_stats"
                ]["nonzero_parameter_count"],
            }
        )

    exact_pass_count = sum(1 for trial in trial_rows if trial["exact_pass"])
    best_trial = min(trial_rows, key=lambda trial: trial["residual_norm"])
    best_sequence = min(sequence_rows, key=lambda row: row["best_two_free_residual_norm"])
    worst_sequence = max(sequence_rows, key=lambda row: row["best_two_free_residual_norm"])
    accepted_removed = 0
    two_free_proxy_t_pressure = 40
    candidate_found = exact_pass_count > 0
    status = STATUS_CANDIDATE if candidate_found else STATUS_REJECTED
    model_status = MODEL_CANDIDATE if candidate_found else MODEL_REJECTED
    summary = {
        "source_semantic_packet_method": semantic.get("method"),
        "source_orientation_census_method": census.get("method"),
        "source_grid_snap_pricing_method": grid_snap.get("method"),
        "source_one_free_pricing_method": one_free.get("method"),
        "target_line_number": TARGET_LINE,
        "union_window": [
            int(packet["window_start_line"]),
            int(packet["window_end_line"]),
        ],
        "support_qubits": packet["support_qubits"],
        "source_cnot_count": int(packet["cx_count"]),
        "searched_cnot_count": 2,
        "orientation_sequence_count": len(sequence_rows),
        "orientation_sequence_ids": [row["sequence_id"] for row in sequence_rows],
        "two_free_trial_count": len(trial_rows),
        "two_free_exact_pass_count": exact_pass_count,
        "two_free_exact_fail_count": len(trial_rows) - exact_pass_count,
        "all_two_free_trials_fail": exact_pass_count == 0,
        "best_two_free_sequence_id": best_sequence["sequence_id"],
        "best_two_free_parameter_pair": best_trial["free_parameter_pair"],
        "best_two_free_residual_norm": best_trial["residual_norm"],
        "best_two_free_residual_ratio_to_exact_tolerance": best_trial[
            "residual_ratio_to_exact_tolerance"
        ],
        "worst_best_sequence_id": worst_sequence["sequence_id"],
        "worst_best_sequence_residual_norm": worst_sequence["best_two_free_residual_norm"],
        "two_free_proxy_t_pressure_if_accepted": two_free_proxy_t_pressure,
        "one_free_proxy_t_pressure_if_accepted": one_free["summary"][
            "one_free_proxy_t_pressure_if_accepted"
        ],
        "current_line1381_proxy_t_pressure": grid_snap["summary"][
            "current_line1381_proxy_t_pressure"
        ],
        "best_source_proxy_t_pressure": grid_snap["summary"]["best_source_proxy_t_pressure"],
        "two_free_pricing_candidate_found": candidate_found,
        "two_free_pricing_accepted": False,
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
        "status": status,
        "model_status": model_status,
        "workload": "qasmbench_medium_exact/gcm_h6.qasm",
        "source_semantic_packet_result": display_path(SEMANTIC_PACKET_PATH),
        "source_orientation_census_result": display_path(ORIENTATION_CENSUS_PATH),
        "source_grid_snap_pricing_result": display_path(GRID_SNAP_PATH),
        "source_one_free_pricing_result": display_path(ONE_FREE_PATH),
        "summary": summary,
        "union_region_two_free_sequence_rows": sequence_rows,
        "union_region_two_free_trial_rows": trial_rows,
        "claim_boundary": {
            "supported_claim": (
                "Within the T-B1-004bf union-region two-CNOT census candidates, "
                "this gate tests whether exactly two off-grid local-U3 parameters "
                "can recover exact replay after snapping all others to the pi/4 grid."
            ),
            "unsupported_claims": [
                "This is not a global lower bound for the union target.",
                "A local exact two-free candidate, if present, is not a full-circuit replay certificate.",
                "This does not accept occurrence removal, proxy-T reduction, or a B7 ledger improvement.",
            ],
            "two_free_pricing_accepted": False,
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
    sequence_rows = payload.get("union_region_two_free_sequence_rows", [])
    trial_rows = payload.get("union_region_two_free_trial_rows", [])
    expected = {
        "target_line_number": 1381,
        "union_window": [1369, 1379],
        "support_qubits": [4, 8],
        "source_cnot_count": 5,
        "searched_cnot_count": 2,
        "orientation_sequence_count": 4,
        "orientation_sequence_ids": ["01-01", "01-10", "10-01", "10-10"],
        "two_free_trial_count": 612,
        "two_free_pricing_accepted": False,
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
    if payload.get("status") not in {STATUS_REJECTED, STATUS_CANDIDATE}:
        errors.append("status_mismatch")
    if payload.get("model_status") not in {MODEL_REJECTED, MODEL_CANDIDATE}:
        errors.append("model_status_mismatch")
    for key, value in expected.items():
        if summary.get(key) != value:
            errors.append(f"summary_{key}_expected_{value!r}_got_{summary.get(key)!r}")
    if len(sequence_rows) != 4:
        errors.append(f"sequence_row_count_expected_4_got_{len(sequence_rows)}")
    if len(trial_rows) != 612:
        errors.append(f"trial_row_count_expected_612_got_{len(trial_rows)}")
    exact_count = sum(1 for trial in trial_rows if trial.get("exact_pass"))
    if summary.get("two_free_exact_pass_count") != exact_count:
        errors.append("exact_pass_count_mismatch")
    if summary.get("two_free_exact_fail_count") != len(trial_rows) - exact_count:
        errors.append("exact_fail_count_mismatch")
    if summary.get("all_two_free_trials_fail") != (exact_count == 0):
        errors.append("all_two_free_trials_fail_mismatch")
    if summary.get("two_free_pricing_candidate_found") != (exact_count > 0):
        errors.append("candidate_found_mismatch")
    claims = payload.get("claim_boundary", {})
    for field in [
        "two_free_pricing_accepted",
        "local_u3_pricing_completed",
        "resource_saving_claimed",
        "b7_ledger_improvement_claimed",
    ]:
        if claims.get(field) is not False:
            errors.append(f"claim_boundary_{field}_not_false")
    return errors


def markdown_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# B1/B7 cone_01 Union-Region Two-Free-Parameter Pricing Gate",
        "",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Model status: `{payload['model_status']}`",
        f"- Workload: `{payload['workload']}`",
        f"- Union window: `{summary['union_window']}`",
        f"- Support qubits: `{summary['support_qubits']}`",
        f"- Orientation sequences: `{summary['orientation_sequence_ids']}`",
        f"- Two-free trials: `{summary['two_free_trial_count']}`",
        f"- Exact pass / fail: `{summary['two_free_exact_pass_count']}` / `{summary['two_free_exact_fail_count']}`",
        f"- Best two-free residual: `{summary['best_two_free_residual_norm']}`",
        f"- Best two-free sequence / parameter pair: `{summary['best_two_free_sequence_id']}` / `{summary['best_two_free_parameter_pair']}`",
        f"- Worst best-sequence residual: `{summary['worst_best_sequence_residual_norm']}`",
        f"- Two-free proxy-T pressure if accepted: `{summary['two_free_proxy_t_pressure_if_accepted']}`",
        f"- Current line-1381 proxy-T pressure: `{summary['current_line1381_proxy_t_pressure']}`",
        f"- Two-free pricing candidate found: `{summary['two_free_pricing_candidate_found']}`",
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
    lines.extend(["", "## Sequence Best Rows", ""])
    for row in payload["union_region_two_free_sequence_rows"]:
        lines.append(
            "- "
            f"`{row['sequence_id']}`: best pair `{row['best_two_free_parameter_pair']}`, "
            f"residual `{row['best_two_free_residual_norm']}`, "
            f"exact passes `{row['two_free_exact_pass_count']}` / `{row['two_free_trial_count']}`"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", type=Path, default=JSON_OUT)
    parser.add_argument("--markdown-output", type=Path, default=MD_OUT)
    parser.add_argument("--max-nfev", type=int, default=DEFAULT_MAX_NFEV)
    args = parser.parse_args()

    payload = run_probe(args.max_nfev)
    errors = validate_payload(payload)
    if errors:
        raise SystemExit("validation failed: " + "; ".join(errors))
    write_json(args.json_output, payload, True)
    write_text(args.markdown_output, markdown_report(payload))
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
