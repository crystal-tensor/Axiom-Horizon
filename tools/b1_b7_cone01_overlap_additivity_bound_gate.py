#!/usr/bin/env python3
"""Overlap additivity bound gate for the B1/B7 cone_01 candidate.

The non-overlap patch subset drops line 1378 because its source window is
contained inside the line-1381 window. This gate checks whether the dropped
3-CNOT delta can be recovered additively by merging the overlapping region.

It cannot: the union region has only five source CNOTs. Counting both the
line-1381 3-CNOT delta and the line-1378 3-CNOT delta would require a negative
replacement CNOT count. The result is a resource-accounting boundary, not a
new accepted B7 saving.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from b1_b7_cone01_carrier_absorption_inventory_gate import (
    PROXY_T_PER_OCCURRENCE,
    REQUIRED_OCCURRENCE_REMOVALS,
    display_path,
    load_json,
    write_json,
    write_text,
)


ROOT = Path(__file__).resolve().parents[1]
NONOVERLAP_PATH = ROOT / "results" / "B1_B7_cone01_nonoverlap_patch_subset_gate_v0.json"
PRICING_PATH = ROOT / "results" / "B1_B7_cone01_line1381_local_u3_pricing_gate_v0.json"
JSON_OUT = ROOT / "results" / "B1_B7_cone01_overlap_additivity_bound_gate_v0.json"
MD_OUT = ROOT / "research" / "B1_B7_cone01_overlap_additivity_bound_gate.md"

METHOD = "b1_b7_cone01_overlap_additivity_bound_gate_v0"
STATUS = "cone01_overlap_additivity_bound_blocks_line1378_delta_recovery"
MODEL_STATUS = "contained_overlap_window_makes_line1378_delta_nonadditive"


def row_by_line(rows: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    return {int(row["candidate_line_number"]): row for row in rows}


def is_contained(inner: dict[str, Any], outer: dict[str, Any]) -> bool:
    return (
        int(outer["window_start_line"])
        <= int(inner["window_start_line"])
        <= int(inner["window_end_line"])
        <= int(outer["window_end_line"])
    )


def run_probe() -> dict[str, Any]:
    nonoverlap_payload = load_json(NONOVERLAP_PATH)
    pricing_payload = load_json(PRICING_PATH)
    selected_rows = row_by_line(nonoverlap_payload.get("selected_nonoverlap_patch_rows", []))
    dropped_rows = row_by_line(nonoverlap_payload.get("dropped_overlap_patch_rows", []))
    line1381 = selected_rows[1381]
    line1378 = dropped_rows[1378]
    pricing_summary = pricing_payload.get("summary", {})

    contained = is_contained(line1378, line1381)
    same_support = line1378.get("support_qubits") == line1381.get("support_qubits")
    union_window_start = min(int(line1378["window_start_line"]), int(line1381["window_start_line"]))
    union_window_end = max(int(line1378["window_end_line"]), int(line1381["window_end_line"]))
    union_source_cnot_count = int(line1381["source_cnot_count"]) if contained else None
    line1381_delta = int(line1381["candidate_cnot_reduction"])
    line1378_delta = int(line1378["candidate_cnot_reduction"])
    additive_pair_delta = line1381_delta + line1378_delta
    required_replacement_cnot_for_additive_delta = (
        union_source_cnot_count - additive_pair_delta
        if union_source_cnot_count is not None
        else None
    )
    current_line1381_replacement_cnot_count = int(line1381["replacement_cnot_count"])
    max_additional_delta_vs_line1381_under_nonnegative_cnot = (
        union_source_cnot_count - line1381_delta if union_source_cnot_count is not None else None
    )
    additive_recovery_impossible_by_cnot_bound = (
        required_replacement_cnot_for_additive_delta is not None
        and required_replacement_cnot_for_additive_delta < 0
    )
    full_lost_delta_recoverable_by_contained_merge = (
        not additive_recovery_impossible_by_cnot_bound
        and max_additional_delta_vs_line1381_under_nonnegative_cnot is not None
        and max_additional_delta_vs_line1381_under_nonnegative_cnot >= line1378_delta
    )
    accepted_removed = 0

    summary = {
        "source_nonoverlap_subset_method": nonoverlap_payload.get("method"),
        "source_pricing_method": pricing_payload.get("method"),
        "selected_line_numbers": pricing_summary.get("selected_line_numbers"),
        "dropped_overlap_candidate_line_numbers": pricing_summary.get(
            "dropped_overlap_candidate_line_numbers"
        ),
        "line1378_window": [
            int(line1378["window_start_line"]),
            int(line1378["window_end_line"]),
        ],
        "line1381_window": [
            int(line1381["window_start_line"]),
            int(line1381["window_end_line"]),
        ],
        "union_window": [union_window_start, union_window_end],
        "line1378_window_contained_in_line1381": contained,
        "line1378_line1381_same_support": same_support,
        "support_qubits": line1381.get("support_qubits"),
        "union_source_cnot_count": union_source_cnot_count,
        "line1381_replacement_cnot_count": current_line1381_replacement_cnot_count,
        "line1378_replacement_cnot_count": int(line1378["replacement_cnot_count"]),
        "line1381_candidate_cnot_delta": line1381_delta,
        "line1378_candidate_cnot_delta": line1378_delta,
        "additive_pair_cnot_delta_requested": additive_pair_delta,
        "required_replacement_cnot_for_additive_pair_delta": (
            required_replacement_cnot_for_additive_delta
        ),
        "additive_recovery_impossible_by_cnot_bound": additive_recovery_impossible_by_cnot_bound,
        "max_additional_delta_vs_line1381_under_nonnegative_cnot": (
            max_additional_delta_vs_line1381_under_nonnegative_cnot
        ),
        "full_lost_line1378_delta_recoverable_by_contained_merge": (
            full_lost_delta_recoverable_by_contained_merge
        ),
        "line1378_delta_recovered": False,
        "merged_region_rewrite_emitted": False,
        "merged_region_replay_certificate_count": 0,
        "accepted_full_circuit_replay_certificate_count": pricing_summary.get(
            "accepted_full_circuit_replay_certificate_count"
        ),
        "accepted_full_circuit_qasm_patch_count": pricing_summary.get(
            "accepted_full_circuit_qasm_patch_count"
        ),
        "accepted_occurrence_removal": accepted_removed,
        "accepted_proxy_t_reduction": 0,
        "missing_occurrences_after_gate": max(0, REQUIRED_OCCURRENCE_REMOVALS - accepted_removed),
        "missing_proxy_t_after_gate": max(
            0,
            (REQUIRED_OCCURRENCE_REMOVALS - accepted_removed) * PROXY_T_PER_OCCURRENCE,
        ),
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "validation_error_count": 0,
    }
    payload = {
        "benchmark_id": "B1",
        "linked_b7_problem_id": 21,
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "workload": "qasmbench_medium_exact/gcm_h6.qasm",
        "source_nonoverlap_subset_result": display_path(NONOVERLAP_PATH),
        "source_pricing_result": display_path(PRICING_PATH),
        "summary": summary,
        "claim_boundary": {
            "supported_claim": (
                "Line 1378 is contained inside the line-1381 replacement window, "
                "so its 3-CNOT delta cannot be additively recovered on top of the "
                "line-1381 3-CNOT delta without requiring a negative replacement "
                "CNOT count for the union region."
            ),
            "unsupported_claims": [
                "This does not synthesize a new merged-region replacement.",
                "This does not recover the dropped line-1378 delta.",
                "This does not remove the remaining line-1381 local-U3 pricing burden.",
                "This does not improve the B7 ledger.",
            ],
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
            "line1378_delta_recovered": False,
            "merged_region_rewrite_emitted": False,
        },
    }
    return payload


def markdown_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# B1/B7 cone_01 Overlap Additivity Bound Gate",
        "",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Model status: `{payload['model_status']}`",
        f"- Workload: `{payload['workload']}`",
        f"- Source non-overlap subset: `{payload['source_nonoverlap_subset_result']}`",
        f"- Source pricing result: `{payload['source_pricing_result']}`",
        "",
        "## Result",
        "",
        f"- Line-1378 window: `{summary['line1378_window']}`",
        f"- Line-1381 window: `{summary['line1381_window']}`",
        f"- Union window: `{summary['union_window']}`",
        f"- Contained overlap / same support: `{summary['line1378_window_contained_in_line1381']}` / `{summary['line1378_line1381_same_support']}`",
        f"- Union source CNOT count: `{summary['union_source_cnot_count']}`",
        f"- Line-1381 delta / line-1378 delta: `{summary['line1381_candidate_cnot_delta']}` / `{summary['line1378_candidate_cnot_delta']}`",
        f"- Additive pair delta requested: `{summary['additive_pair_cnot_delta_requested']}`",
        f"- Required replacement CNOT count for additive pair delta: `{summary['required_replacement_cnot_for_additive_pair_delta']}`",
        f"- Additive recovery impossible by CNOT bound: `{summary['additive_recovery_impossible_by_cnot_bound']}`",
        f"- Max additional delta vs line 1381 under nonnegative replacement CNOT: `{summary['max_additional_delta_vs_line1381_under_nonnegative_cnot']}`",
        f"- Full lost line-1378 delta recoverable by contained merge: `{summary['full_lost_line1378_delta_recoverable_by_contained_merge']}`",
        f"- Accepted occurrence / proxy-T reduction: `{summary['accepted_occurrence_removal']}` / `{summary['accepted_proxy_t_reduction']}`",
        "",
        "## Claim Boundary",
        "",
        "- This is an overlap-accounting negative boundary, not a merged-region synthesis result.",
        "- The next valid route is not additive delta recovery; it must synthesize a new union-region replacement, prove replay, and price remaining local-U3 burden under B7.",
    ]
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
