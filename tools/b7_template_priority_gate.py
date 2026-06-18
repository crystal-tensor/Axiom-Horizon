#!/usr/bin/env python3
"""Rank B7 repeated templates against the gcm_h6 resource threshold.

This is a post-hoc gate on the nonlocal template scan. It does not synthesize a
new rewrite. It asks which repeated templates could matter if a future
occurrence-removing certificate exists, and how many arbitrary rotations per
occurrence would need to disappear before the gcm_h6 1.20x boundary can clear.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import yaml


METHOD = "b7_template_priority_gate_v0"
STATUS = "template_priority_gate_no_single_one_angle_template_clears_gcm_h6"
MODEL_STATUS = "posthoc_template_priority_gate_not_rewrite_or_lower_bound"
VERSION = "0.1"
PROXY_T_COST_PER_ARBITRARY_ROTATION = 20


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict, pretty: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    indent = 2 if pretty else None
    path.write_text(json.dumps(payload, indent=indent, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def claim_fragment_stats(manifest_path: Path) -> dict:
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    fragment = manifest["current_results"]["w8_21_claim_boundary_fragment_v0"]
    return {
        "total_optimizer_runs_across_searches": int(fragment["total_optimizer_runs_across_searches"]),
        "exact_rewrite_found": bool(fragment["exact_rewrite_found"]),
    }


def template_gate_rows(source: dict, target_removed: int) -> list[dict]:
    rows = []
    for template in source.get("top_templates", []):
        occurrences = int(template["nonoverlap_occurrences"])
        arbitrary_per_occurrence = int(template["arbitrary_rotations_per_occurrence"])
        physical_covered = int(template["physical_arbitrary_occurrences_covered"])
        required_per_occurrence = math.ceil(target_removed / occurrences)
        one_angle_removed_t_ledger = occurrences * PROXY_T_COST_PER_ARBITRARY_ROTATION
        row = {
            "template_id": template["template_id"],
            "width": int(template["width"]),
            "nonoverlap_occurrences": occurrences,
            "arbitrary_rotations_per_occurrence": arbitrary_per_occurrence,
            "physical_arbitrary_occurrences_covered": physical_covered,
            "unique_binding_count": int(template["unique_binding_count"]),
            "one_arbitrary_removed_per_occurrence": occurrences,
            "one_arbitrary_removed_t_ledger": one_angle_removed_t_ledger,
            "one_arbitrary_per_occurrence_clears_gcm_h6_1_20": occurrences >= target_removed,
            "required_arbitrary_removed_per_occurrence_for_gcm_h6_1_20": required_per_occurrence,
            "required_fraction_of_template_arbitrary_components": required_per_occurrence
            / arbitrary_per_occurrence,
            "all_arbitrary_components_removed_would_clear_gcm_h6_1_20": physical_covered
            >= target_removed,
            "same_access_rewrite_available": False,
            "exact_occurrence_removing_certificate_available": False,
        }
        rows.append(row)
    return rows


def validate(payload: dict) -> list[str]:
    errors = []
    summary = payload["summary"]
    claims = payload["claim_boundary"]
    rows = payload["template_priority_rows"]
    if payload.get("benchmark_id") != "B7":
        errors.append("benchmark_id must be B7")
    if payload.get("method") != METHOD:
        errors.append("method mismatch")
    if payload.get("status") != STATUS:
        errors.append("status mismatch")
    if payload.get("model_status") != MODEL_STATUS:
        errors.append("model_status mismatch")
    if summary.get("template_count") != len(rows):
        errors.append("template_count does not match row count")
    if summary.get("target_removed_arbitrary_occurrences_for_gcm_h6_1_20") != 30:
        errors.append("unexpected gcm_h6 target removed arbitrary count")
    if summary.get("single_template_one_angle_clear_count") != 0:
        errors.append("one-angle single-template route should not clear gcm_h6")
    if summary.get("best_template_id") != "w8_21":
        errors.append("best template should remain w8_21")
    if summary.get("best_template_required_arbitrary_removed_per_occurrence") < 2:
        errors.append("w8_21 should require at least two removals per occurrence")
    if summary.get("w8_21_prior_optimizer_runs") != 43480:
        errors.append("w8_21 prior optimizer-run total mismatch")
    if summary.get("w8_21_prior_exact_rewrite_found") is not False:
        errors.append("w8_21 prior exact rewrite must remain false")
    if summary.get("all_variant_1_20_by_gcm_h6_only") is not False:
        errors.append("all-variant 1.20x must remain false")
    for key in (
        "new_rewrite_claimed",
        "physical_resource_reduction_claimed",
        "global_lower_bound_claimed",
        "all_variant_1_20_claimed",
    ):
        if claims.get(key) is not False:
            errors.append(f"claim boundary must keep {key}=False")
    return errors


def build_payload(args: argparse.Namespace) -> dict:
    source = read_json(args.source_template_report)
    claim_stats = claim_fragment_stats(args.manifest)
    first_gcm = source["target_sweep"]["first_gcm_h6_1_20"]
    target_removed = int(first_gcm["removed_arbitrary_occurrences"])
    rows = template_gate_rows(source, target_removed)
    single_angle_clears = [row for row in rows if row["one_arbitrary_per_occurrence_clears_gcm_h6_1_20"]]
    all_component_clears = [
        row for row in rows if row["all_arbitrary_components_removed_would_clear_gcm_h6_1_20"]
    ]
    best = rows[0]
    payload = {
        "benchmark_id": "B7",
        "problem_id": 21,
        "title": "B7 template priority gate for gcm_h6 occurrence-removing rewrites",
        "version": VERSION,
        "last_updated": args.last_updated,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "method": METHOD,
        "source_template_report": str(args.source_template_report),
        "source_template_method": source.get("method"),
        "source_template_status": source.get("status"),
        "source_claim_fragment": "w8_21_claim_boundary_fragment_v0",
        "workload": "qasmbench_medium_exact/gcm_h6.qasm",
        "proxy_t_cost_per_arbitrary_rotation": PROXY_T_COST_PER_ARBITRARY_ROTATION,
        "target_boundary": {
            "target_removed_arbitrary_occurrences_for_gcm_h6_1_20": target_removed,
            "target_removed_t_ledger_for_gcm_h6_1_20": int(first_gcm["removed_t_ledger"]),
            "target_after_t_ledger_for_gcm_h6_1_20": int(first_gcm["after_t_ledger"]),
            "target_gcm_h6_min_space_time_volume_reduction": first_gcm[
                "gcm_h6_min_space_time_volume_reduction"
            ],
            "all_variant_1_20_by_gcm_h6_only": source["target_sweep"]["first_all_variant_1_20"]
            is not None,
        },
        "summary": {
            "template_count": len(rows),
            "target_removed_arbitrary_occurrences_for_gcm_h6_1_20": target_removed,
            "target_removed_t_ledger_for_gcm_h6_1_20": int(first_gcm["removed_t_ledger"]),
            "single_template_one_angle_clear_count": len(single_angle_clears),
            "single_template_all_components_clear_count": len(all_component_clears),
            "best_template_id": best["template_id"],
            "best_template_nonoverlap_occurrences": best["nonoverlap_occurrences"],
            "best_template_required_arbitrary_removed_per_occurrence": best[
                "required_arbitrary_removed_per_occurrence_for_gcm_h6_1_20"
            ],
            "best_template_one_angle_shortfall": max(
                0, target_removed - best["one_arbitrary_removed_per_occurrence"]
            ),
            "w8_21_prior_optimizer_runs": claim_stats["total_optimizer_runs_across_searches"],
            "w8_21_prior_exact_rewrite_found": claim_stats["exact_rewrite_found"],
            "all_variant_1_20_by_gcm_h6_only": source["target_sweep"]["first_all_variant_1_20"]
            is not None,
            "physical_resource_reduction_claimed": False,
            "global_lower_bound_claimed": False,
        },
        "template_priority_rows": rows,
        "claim_boundary": {
            "new_rewrite_claimed": False,
            "physical_resource_reduction_claimed": False,
            "global_lower_bound_claimed": False,
            "all_variant_1_20_claimed": False,
            "interpretation": "single_template_one_angle_rewrites_are_insufficient_for_gcm_h6_1_20",
            "next_gate": (
                "Produce a symbolic KAK/Clifford-scaffold proof, an exact occurrence-removing "
                "rewrite that removes at least the required per-occurrence arbitrary rotations, "
                "or return to B1 T-resource improvements."
            ),
        },
    }
    validation_errors = validate(payload)
    payload["summary"]["validation_error_count"] = len(validation_errors)
    payload["validation_errors"] = validation_errors
    return payload


def markdown(payload: dict) -> str:
    summary = payload["summary"]
    lines = [
        "# B7 Template Priority Gate v0.1",
        "",
        f"Status: **{payload['status']}**",
        "",
        "This gate ranks the retained nonlocal templates against the gcm_h6 1.20x",
        "resource threshold. It is not a new rewrite, not a symbolic proof, not a",
        "physical layout result, and not a global lower bound.",
        "",
        "## Summary",
        "",
        f"- Source scan: `{payload['source_template_report']}`",
        f"- Templates evaluated: {summary['template_count']}",
        "- gcm_h6 1.20x one-sided target: "
        f"{summary['target_removed_arbitrary_occurrences_for_gcm_h6_1_20']} removed arbitrary "
        f"occurrences / {summary['target_removed_t_ledger_for_gcm_h6_1_20']} proxy-T ledger units",
        f"- Single-template one-angle clear count: {summary['single_template_one_angle_clear_count']}",
        f"- Best template: `{summary['best_template_id']}` with "
        f"{summary['best_template_nonoverlap_occurrences']} nonoverlap occurrences",
        "- Best-template required removals per occurrence: "
        f"{summary['best_template_required_arbitrary_removed_per_occurrence']}",
        f"- Best-template one-angle shortfall: {summary['best_template_one_angle_shortfall']} arbitrary occurrences",
        f"- Prior `w8_21` optimizer runs: {summary['w8_21_prior_optimizer_runs']}",
        f"- Prior `w8_21` exact rewrite found: {summary['w8_21_prior_exact_rewrite_found']}",
        f"- All-variant 1.20x cleared by gcm_h6-only removals: {summary['all_variant_1_20_by_gcm_h6_only']}",
        "",
        "## Template Priority Table",
        "",
        "| Template | Width | Occurrences | Arbitrary/occ | One-angle clears? | Required arbitrary/occ | Physical covered | Certificate? |",
        "|---|---:|---:|---:|---|---:|---:|---|",
    ]
    for row in payload["template_priority_rows"]:
        lines.append(
            "| {template_id} | {width} | {nonoverlap_occurrences} | "
            "{arbitrary_rotations_per_occurrence} | {one_clear} | {required} | "
            "{covered} | {cert} |".format(
                template_id=row["template_id"],
                width=row["width"],
                nonoverlap_occurrences=row["nonoverlap_occurrences"],
                arbitrary_rotations_per_occurrence=row["arbitrary_rotations_per_occurrence"],
                one_clear=row["one_arbitrary_per_occurrence_clears_gcm_h6_1_20"],
                required=row["required_arbitrary_removed_per_occurrence_for_gcm_h6_1_20"],
                covered=row["physical_arbitrary_occurrences_covered"],
                cert=row["exact_occurrence_removing_certificate_available"],
            )
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- No new occurrence-removing rewrite is claimed.",
            "- No physical resource reduction is claimed.",
            "- No global KAK or two-qubit lower bound is claimed.",
            "- The all-variant portfolio 1.20x gate remains false.",
            "",
            "## Next Gate",
            "",
            "For `T-B7-010`, a useful PR must provide one of three things:",
            "",
            "1. a symbolic KAK/Clifford-scaffold proof for `w8_21`,",
            "2. a certified occurrence-removing rewrite for `gcm_h6` that removes at least the required per-occurrence arbitrary rotations, or",
            "3. a B1 T-resource improvement that moves the B7 min row without counting repeated templates as savings.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-template-report",
        type=Path,
        default=Path("results/B7_nonlocal_template_block_scan_v0.json"),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("benchmarks/B7_fault_tolerance_codesign.yaml"),
    )
    parser.add_argument("--json-output", type=Path, default=Path("results/B7_template_priority_gate_v0.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("research/B7_template_priority_gate.md"))
    parser.add_argument("--last-updated", default="2026-06-18")
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    payload = build_payload(args)
    write_json(args.json_output, payload, pretty=args.pretty)
    write_text(args.markdown_output, markdown(payload))
    if payload["validation_errors"]:
        for error in payload["validation_errors"]:
            print(f"validation error: {error}", file=sys.stderr)
        return 1
    print(f"wrote {args.json_output}")
    print(f"wrote {args.markdown_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
