#!/usr/bin/env python3
"""Shared-theta synthesis object proposal gate for B1/B7 cone_01.

The theta-sharing ledger identified four repeated theta groups across 35
cone_01 windows.  This gate turns those groups into explicit machine-readable
shared synthesis object proposals.  It is deliberately only an existence gate:
the objects are not replay-verified, not laid out physically, and not accepted
as B7 resource reductions.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_shared_theta_synthesis_object_gate_v0"
STATUS = "cone01_shared_theta_synthesis_object_proposal"
MODEL_STATUS = "shared_theta_objects_exist_without_replay_or_resource_acceptance"
VERSION = "0.1"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any], pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2 if pretty else None, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def display_path(path: Path) -> str:
    root = Path(__file__).resolve().parents[1]
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(root))
    except ValueError:
        return str(path)


def build_objects(ledger: dict[str, Any]) -> list[dict[str, Any]]:
    rows = sorted(
        ledger["theta_group_accounting_rows"],
        key=lambda row: (-int(row["occurrence_count"]), float(row["canonical_theta"])),
    )
    objects = []
    for index, row in enumerate(rows, start=1):
        line_numbers = list(row["line_numbers"])
        first_line = min(line_numbers)
        objects.append(
            {
                "object_id": f"cone01_shared_theta_{index:02d}",
                "canonical_theta": row["canonical_theta"],
                "source_occurrence_count": int(row["occurrence_count"]),
                "duplicate_occurrence_count": int(row["template_cache_duplicate_occurrences"]),
                "covered_line_numbers": line_numbers,
                "anchor_line_number": first_line,
                "consumer_line_numbers": [line for line in line_numbers if line != first_line],
                "optimistic_cache_proxy_t_reuse": int(row["optimistic_cache_proxy_t_reuse"]),
                "occurrence_ledger_removed_occurrences": 0,
                "occurrence_ledger_proxy_t_reduction": 0,
                "semantic_replay_verified": False,
                "physical_layout_assigned": False,
                "factory_amortization_verified": False,
                "error_budget_verified": False,
                "b7_ledger_accepted": False,
            }
        )
    return objects


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    transfer = read_json(args.parameter_transfer_gate)
    ledger = read_json(args.theta_sharing_ledger_gate)
    ledger_summary = ledger["summary"]
    objects = build_objects(ledger)
    covered_lines = sorted({line for obj in objects for line in obj["covered_line_numbers"]})
    duplicate_count = sum(obj["duplicate_occurrence_count"] for obj in objects)
    optimistic_proxy_t = sum(obj["optimistic_cache_proxy_t_reuse"] for obj in objects)

    payload = {
        "benchmark_id": "B1",
        "problem_id": 25,
        "linked_b7_problem_id": 21,
        "title": "B1/B7 cone_01 shared-theta synthesis object proposal gate",
        "version": VERSION,
        "last_updated": args.last_updated,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "method": METHOD,
        "source_parameter_transfer_gate": display_path(args.parameter_transfer_gate),
        "source_theta_sharing_ledger_gate": display_path(args.theta_sharing_ledger_gate),
        "workload": "qasmbench_medium_exact/gcm_h6.qasm",
        "summary": {
            "candidate_window_count": int(ledger_summary["candidate_window_count"]),
            "shared_synthesis_object_count": len(objects),
            "distinct_theta_group_count": int(ledger_summary["distinct_theta_group_count"]),
            "covered_occurrence_count": len(covered_lines),
            "duplicate_theta_occurrence_count": duplicate_count,
            "optimistic_cache_proxy_t_reuse": optimistic_proxy_t,
            "target_proxy_t_ledger_reduction_for_gcm_h6_1_20": int(
                ledger_summary["target_proxy_t_ledger_reduction_for_gcm_h6_1_20"]
            ),
            "shared_object_existence_gate_passed": len(objects) == int(ledger_summary["distinct_theta_group_count"]),
            "all_candidate_windows_covered": len(covered_lines) == int(ledger_summary["candidate_window_count"]),
            "semantic_replay_verified_object_count": 0,
            "physical_layout_assigned_object_count": 0,
            "b7_ledger_accepted_object_count": 0,
            "occurrence_ledger_removed_occurrences": 0,
            "occurrence_ledger_proxy_t_reduction": 0,
            "cost_model_accepted": False,
            "rewrite_claimed": False,
            "resource_saving_claimed": False,
            "semantic_certificate_claimed": False,
            "physical_resource_reduction_claimed": False,
            "b7_ledger_improvement_claimed": False,
            "validation_error_count": None,
        },
        "shared_theta_synthesis_objects": objects,
        "claim_boundary": {
            "cost_model_accepted": False,
            "rewrite_claimed": False,
            "resource_saving_claimed": False,
            "semantic_certificate_claimed": False,
            "physical_resource_reduction_claimed": False,
            "b7_ledger_improvement_claimed": False,
            "supported_claim": (
                "The repeated cone_01 theta groups have explicit machine-readable "
                "shared synthesis object proposals covering all 35 candidate windows."
            ),
            "unsupported_claims": [
                "No shared object has a replay verifier.",
                "No shared object has a physical layout or routing assignment.",
                "No shared object has factory-amortization or error-budget evidence.",
                "No occurrence is removed from the current B7 ledger.",
                "No B7 resource reduction is counted.",
            ],
            "next_gate": (
                "Use these objects as CM-02 evidence, then build CM-03 replay "
                "verification and CM-04 physical layout before any cost model can be accepted."
            ),
        },
    }
    errors = validate(payload, transfer, ledger)
    payload["summary"]["validation_error_count"] = len(errors)
    payload["validation_errors"] = errors
    return payload


def validate(payload: dict[str, Any], transfer: dict[str, Any], ledger: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    summary = payload["summary"]
    ledger_summary = ledger["summary"]
    if payload.get("method") != METHOD:
        errors.append("method mismatch")
    if payload.get("status") != STATUS:
        errors.append("status mismatch")
    if payload.get("model_status") != MODEL_STATUS:
        errors.append("model_status mismatch")
    if summary["candidate_window_count"] != 35:
        errors.append("expected 35 cone_01 windows")
    if summary["shared_synthesis_object_count"] != 4:
        errors.append("expected 4 shared theta objects")
    if summary["distinct_theta_group_count"] != 4:
        errors.append("expected 4 theta groups")
    if summary["covered_occurrence_count"] != summary["candidate_window_count"]:
        errors.append("shared objects should cover all candidate windows")
    if summary["duplicate_theta_occurrence_count"] != int(ledger_summary["duplicate_theta_occurrence_count"]):
        errors.append("duplicate theta count must match ledger")
    if summary["optimistic_cache_proxy_t_reuse"] != int(ledger_summary["optimistic_cache_proxy_t_reuse"]):
        errors.append("optimistic cache proxy-T must match ledger")
    if summary["target_proxy_t_ledger_reduction_for_gcm_h6_1_20"] != int(
        transfer["summary"]["target_proxy_t_ledger_reduction_for_gcm_h6_1_20"]
    ):
        errors.append("target proxy-T must match parameter-transfer gate")
    if summary["shared_object_existence_gate_passed"] is not True:
        errors.append("shared object existence gate should pass")
    if summary["all_candidate_windows_covered"] is not True:
        errors.append("all windows should be covered by shared objects")
    for field in [
        "semantic_replay_verified_object_count",
        "physical_layout_assigned_object_count",
        "b7_ledger_accepted_object_count",
        "occurrence_ledger_removed_occurrences",
        "occurrence_ledger_proxy_t_reduction",
    ]:
        if summary[field] != 0:
            errors.append(f"{field} must remain zero")
    for field in [
        "cost_model_accepted",
        "rewrite_claimed",
        "resource_saving_claimed",
        "semantic_certificate_claimed",
        "physical_resource_reduction_claimed",
        "b7_ledger_improvement_claimed",
    ]:
        if summary[field] is not False:
            errors.append(f"{field} must remain false")
        if payload["claim_boundary"].get(field) is not False:
            errors.append(f"claim boundary {field} must remain false")
    for obj in payload["shared_theta_synthesis_objects"]:
        if obj["anchor_line_number"] in obj["consumer_line_numbers"]:
            errors.append(f"{obj['object_id']} anchor cannot also be a consumer")
        for field in [
            "semantic_replay_verified",
            "physical_layout_assigned",
            "factory_amortization_verified",
            "error_budget_verified",
            "b7_ledger_accepted",
        ]:
            if obj[field] is not False:
                errors.append(f"{obj['object_id']} {field} must remain false")
    return errors


def markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# B1/B7 Cone_01 Shared-Theta Synthesis Object Proposal Gate",
        "",
        f"Status: `{payload['status']}`",
        "",
        "This artifact converts the four repeated cone_01 theta groups into explicit "
        "shared synthesis object proposals. It is an object-existence step only. "
        "The objects do not yet have replay verification, physical layout, factory "
        "amortization, an error budget, or B7 ledger acceptance.",
        "",
        "It is not a rewrite certificate, not a semantic certificate, not a physical "
        "resource-saving claim, and not a B7 resource improvement.",
        "",
        "## Summary",
        "",
        f"- Candidate windows: `{summary['candidate_window_count']}`",
        f"- Shared synthesis objects: `{summary['shared_synthesis_object_count']}`",
        f"- Covered occurrences: `{summary['covered_occurrence_count']}`",
        f"- Duplicate theta occurrences: `{summary['duplicate_theta_occurrence_count']}`",
        f"- Optimistic cache proxy-T reuse: `{summary['optimistic_cache_proxy_t_reuse']}`",
        f"- Shared object existence gate passed: `{summary['shared_object_existence_gate_passed']}`",
        f"- All candidate windows covered: `{summary['all_candidate_windows_covered']}`",
        f"- Semantic replay verified objects: `{summary['semantic_replay_verified_object_count']}`",
        f"- Physical layout assigned objects: `{summary['physical_layout_assigned_object_count']}`",
        f"- B7 ledger accepted objects: `{summary['b7_ledger_accepted_object_count']}`",
        f"- Occurrence-ledger removed occurrences: `{summary['occurrence_ledger_removed_occurrences']}`",
        f"- Cost model accepted: `{summary['cost_model_accepted']}`",
        f"- Validation errors: `{summary['validation_error_count']}`",
        "",
        "## Shared Objects",
        "",
        "| object | theta | source occurrences | duplicate occurrences | anchor line | consumers | optimistic proxy-T |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for obj in payload["shared_theta_synthesis_objects"]:
        lines.append(
            f"| `{obj['object_id']}` | `{obj['canonical_theta']}` | "
            f"{obj['source_occurrence_count']} | {obj['duplicate_occurrence_count']} | "
            f"{obj['anchor_line_number']} | {len(obj['consumer_line_numbers'])} | "
            f"{obj['optimistic_cache_proxy_t_reuse']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This closes one bookkeeping gap in the physical theta-sharing route: the "
            "project now has concrete shared object proposals rather than only a "
            "theta-group count. The hard gates remain ahead. The next admissible "
            "step is a replay verifier for these objects across the covered windows, "
            "followed by layout, factory, error-budget, independent-baseline, and "
            "refreshed-ledger checks.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    root = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--parameter-transfer-gate",
        type=Path,
        default=root / "results" / "B1_B7_cone01_parameter_transfer_gate_v0.json",
    )
    parser.add_argument(
        "--theta-sharing-ledger-gate",
        type=Path,
        default=root / "results" / "B1_B7_cone01_theta_sharing_ledger_gate_v0.json",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=root / "results" / "B1_B7_cone01_shared_theta_synthesis_object_gate_v0.json",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=root / "research" / "B1_B7_cone01_shared_theta_synthesis_object_gate.md",
    )
    parser.add_argument("--last-updated", default="2026-06-18")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    payload = build_payload(args)
    write_json(args.json_output, payload, args.pretty)
    write_text(args.markdown_output, markdown(payload))
    if args.pretty:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Wrote {args.json_output}")
        print(f"Wrote {args.markdown_output}")


if __name__ == "__main__":
    main()
