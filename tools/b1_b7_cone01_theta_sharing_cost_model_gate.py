#!/usr/bin/env python3
"""Physical cost-model feasibility gate for B1/B7 cone_01 theta sharing.

T-B1-004f showed that repeated theta values create a tempting cache signal, but
the current occurrence-based FT ledger does not count cache reuse as a physical
resource reduction. This gate states the acceptance requirements for any future
physical theta-sharing cost model and checks the current evidence against them.

The expected current result is negative: no new physical cost model is accepted.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_theta_sharing_cost_model_gate_v0"
STATUS = "cone01_theta_sharing_cost_model_not_accepted"
MODEL_STATUS = "physical_theta_sharing_cost_model_requirements_partially_scaffolded"
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


def build_requirement_rows(theta_summary: dict[str, Any], shared_summary: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Return current acceptance gates for a physical theta-sharing model."""
    shared_object_count = 0
    shared_object_gate_passed = False
    if shared_summary:
        shared_object_count = int(shared_summary["shared_synthesis_object_count"])
        shared_object_gate_passed = (
            shared_summary["shared_object_existence_gate_passed"] is True
            and shared_summary["all_candidate_windows_covered"] is True
            and int(shared_summary["semantic_replay_verified_object_count"]) == 0
            and int(shared_summary["physical_layout_assigned_object_count"]) == 0
            and int(shared_summary["b7_ledger_accepted_object_count"]) == 0
        )
    return [
        {
            "gate_id": "CM-01",
            "requirement": "At least 30 replayable occurrence-removing semantic certificates.",
            "current_evidence": int(theta_summary["occurrence_ledger_removed_occurrences"]),
            "required_evidence": int(theta_summary["target_removed_arbitrary_occurrences_for_gcm_h6_1_20"]),
            "passed": False,
            "failure_reason": "Current evidence has 0 accepted occurrence removals.",
        },
        {
            "gate_id": "CM-02",
            "requirement": "A shared synthesis object that replaces repeated theta occurrences, not only a classical template label.",
            "current_evidence": shared_object_count,
            "required_evidence": 4,
            "passed": shared_object_gate_passed,
            "failure_reason": (
                "Shared-theta object proposals now exist, but this gate alone does not replay-verify "
                "or physically accept the cost model."
                if shared_object_gate_passed
                else "No complete shared-theta synthesis object proposal covers the cone_01 windows."
            ),
        },
        {
            "gate_id": "CM-03",
            "requirement": "A replay verifier for the shared-theta object across all affected windows.",
            "current_evidence": False,
            "required_evidence": True,
            "passed": False,
            "failure_reason": "No replayable shared-theta verifier exists.",
        },
        {
            "gate_id": "CM-04",
            "requirement": "An explicit layout/routing model showing where the shared object lives and how windows consume it.",
            "current_evidence": False,
            "required_evidence": True,
            "passed": False,
            "failure_reason": "No physical layout or routing path is supplied.",
        },
        {
            "gate_id": "CM-05",
            "requirement": "A factory-amortization model proving lower T-factory pressure under the shared object.",
            "current_evidence": False,
            "required_evidence": True,
            "passed": False,
            "failure_reason": "No factory-throughput or amortization ledger is supplied.",
        },
        {
            "gate_id": "CM-06",
            "requirement": "A synthesis-error and correlation budget for shared theta reuse.",
            "current_evidence": False,
            "required_evidence": True,
            "passed": False,
            "failure_reason": "No shared-error or correlation budget is supplied.",
        },
        {
            "gate_id": "CM-07",
            "requirement": "An independent baseline showing cache-only accounting is not double-counting occurrence cost.",
            "current_evidence": False,
            "required_evidence": True,
            "passed": False,
            "failure_reason": "No independent physical baseline separates cache labels from occurrence cost.",
        },
        {
            "gate_id": "CM-08",
            "requirement": "A refreshed B7 FT ledger that accepts the model and improves the gcm_h6 min row.",
            "current_evidence": False,
            "required_evidence": True,
            "passed": False,
            "failure_reason": "No refreshed B7 ledger accepts theta sharing as a physical saving.",
        },
    ]


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    theta_gate = read_json(args.theta_sharing_gate)
    shared_object_gate = read_json(args.shared_object_gate) if args.shared_object_gate.exists() else None
    theta_summary = theta_gate["summary"]
    shared_summary = shared_object_gate["summary"] if shared_object_gate else None
    rows = build_requirement_rows(theta_summary, shared_summary)
    passed_count = sum(1 for row in rows if row["passed"])
    failed_count = len(rows) - passed_count
    optimistic_cache_signal_present = (
        theta_summary["optimistic_cache_model_clears_target"] is True
        and int(theta_summary["optimistic_cache_proxy_t_reuse"])
        >= int(theta_summary["target_proxy_t_ledger_reduction_for_gcm_h6_1_20"])
    )

    payload = {
        "benchmark_id": "B1",
        "problem_id": 25,
        "linked_b7_problem_id": 21,
        "title": "B1/B7 cone_01 theta-sharing physical cost-model gate",
        "version": VERSION,
        "last_updated": args.last_updated,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "method": METHOD,
        "source_theta_sharing_ledger_gate": display_path(args.theta_sharing_gate),
        "source_shared_theta_synthesis_object_gate": (
            display_path(args.shared_object_gate) if shared_object_gate else None
        ),
        "workload": "qasmbench_medium_exact/gcm_h6.qasm",
        "summary": {
            "candidate_window_count": int(theta_summary["candidate_window_count"]),
            "distinct_theta_group_count": int(theta_summary["distinct_theta_group_count"]),
            "duplicate_theta_occurrence_count": int(theta_summary["duplicate_theta_occurrence_count"]),
            "optimistic_cache_proxy_t_reuse": int(theta_summary["optimistic_cache_proxy_t_reuse"]),
            "target_proxy_t_ledger_reduction_for_gcm_h6_1_20": int(
                theta_summary["target_proxy_t_ledger_reduction_for_gcm_h6_1_20"]
            ),
            "optimistic_cache_signal_present": optimistic_cache_signal_present,
            "shared_synthesis_object_count": int(shared_summary["shared_synthesis_object_count"]) if shared_summary else 0,
            "shared_object_existence_gate_passed": (
                bool(shared_summary["shared_object_existence_gate_passed"]) if shared_summary else False
            ),
            "shared_object_all_windows_covered": (
                bool(shared_summary["all_candidate_windows_covered"]) if shared_summary else False
            ),
            "cost_model_acceptance_gate_count": len(rows),
            "cost_model_acceptance_pass_count": passed_count,
            "cost_model_acceptance_fail_count": failed_count,
            "cost_model_accepted": False,
            "occurrence_ledger_removed_occurrences": int(theta_summary["occurrence_ledger_removed_occurrences"]),
            "occurrence_ledger_proxy_t_reduction": int(theta_summary["occurrence_ledger_proxy_t_reduction"]),
            "b7_ledger_proxy_t_reduction_after_cost_model": 0,
            "additional_occurrence_certificates_required": int(
                theta_summary["additional_occurrence_certificates_required"]
            ),
            "additional_cost_model_gates_required": failed_count,
            "rewrite_claimed": False,
            "resource_saving_claimed": False,
            "semantic_certificate_claimed": False,
            "physical_resource_reduction_claimed": False,
            "b7_ledger_improvement_claimed": False,
            "validation_error_count": None,
        },
        "cost_model_acceptance_gates": rows,
        "claim_boundary": {
            "rewrite_claimed": False,
            "resource_saving_claimed": False,
            "semantic_certificate_claimed": False,
            "physical_resource_reduction_claimed": False,
            "b7_ledger_improvement_claimed": False,
            "supported_claim": (
                "A shared-theta synthesis object proposal now exists for all cone_01 windows, "
                "but the physical theta-sharing cost model is still not acceptable under the "
                "current evidence; the optimistic 620 proxy-T cache signal remains unaccepted."
            ),
            "unsupported_claims": [
                "No occurrence-removing semantic certificates are produced.",
                "No shared-theta replay verifier is produced.",
                "No layout, factory, or error-budget ledger accepts theta sharing.",
                "No B7 min-row resource improvement is counted.",
            ],
            "next_gate": (
                "A future PR must satisfy CM-01 through CM-08 or produce 30 occurrence-removing "
                "certificates before any B7 resource delta can be counted."
            ),
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
        errors.append("method mismatch")
    if payload.get("status") != STATUS:
        errors.append("status mismatch")
    if payload.get("model_status") != MODEL_STATUS:
        errors.append("model_status mismatch")
    if summary["candidate_window_count"] != 35:
        errors.append("expected 35 candidate windows")
    if summary["distinct_theta_group_count"] != 4:
        errors.append("expected 4 theta groups")
    if summary["duplicate_theta_occurrence_count"] != 31:
        errors.append("expected 31 duplicate theta occurrences")
    if summary["optimistic_cache_proxy_t_reuse"] != 620:
        errors.append("expected optimistic cache signal of 620 proxy-T")
    if summary["optimistic_cache_signal_present"] is not True:
        errors.append("optimistic cache signal should be present")
    if summary["cost_model_acceptance_gate_count"] != 8:
        errors.append("expected 8 cost-model acceptance gates")
    if summary["shared_synthesis_object_count"] != 4:
        errors.append("expected 4 shared synthesis object proposals")
    if summary["shared_object_existence_gate_passed"] is not True:
        errors.append("shared object existence gate should now pass")
    if summary["shared_object_all_windows_covered"] is not True:
        errors.append("shared objects should cover all cone_01 windows")
    if summary["cost_model_acceptance_pass_count"] != 1:
        errors.append("current cost-model acceptance passes must be 1")
    if summary["cost_model_acceptance_fail_count"] != 7:
        errors.append("current cost-model acceptance failures must be 7")
    if summary["cost_model_accepted"] is not False:
        errors.append("cost model must not be accepted")
    if summary["b7_ledger_proxy_t_reduction_after_cost_model"] != 0:
        errors.append("B7 ledger reduction after unaccepted cost model must be 0")
    for row in payload["cost_model_acceptance_gates"]:
        if row.get("gate_id") == "CM-02":
            if row.get("passed") is not True:
                errors.append("CM-02 should pass after shared object proposal gate")
        elif row.get("passed") is not False:
            errors.append(f"{row.get('gate_id')} must not pass under current evidence")
    for field in [
        "rewrite_claimed",
        "resource_saving_claimed",
        "semantic_certificate_claimed",
        "physical_resource_reduction_claimed",
        "b7_ledger_improvement_claimed",
    ]:
        if summary.get(field) is not False:
            errors.append(f"{field} must remain false in summary")
        if claims.get(field) is not False:
            errors.append(f"{field} must remain false in claim boundary")
    return errors


def markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# B1/B7 Cone_01 Theta-Sharing Physical Cost-Model Gate",
        "",
        f"Status: `{payload['status']}`",
        "",
        "This artifact asks whether the repeated-theta cache signal from T-B1-004f "
        "can already be promoted into a physical B7 cost model. The answer is no. "
        "A shared synthesis object proposal now exists for the four theta groups, "
        "but the current evidence still lacks replay certificates, layout, factory "
        "amortization, error budget, independent baseline, and refreshed B7 ledger.",
        "",
        "It is not a rewrite certificate, not a resource-saving claim, and not a "
        "physical cost-model acceptance.",
        "",
        "## Summary",
        "",
        f"- Candidate windows: `{summary['candidate_window_count']}`",
        f"- Distinct theta groups: `{summary['distinct_theta_group_count']}`",
        f"- Duplicate theta occurrences: `{summary['duplicate_theta_occurrence_count']}`",
        f"- Optimistic cache proxy-T signal: `{summary['optimistic_cache_proxy_t_reuse']}`",
        f"- Target proxy-T reduction: `{summary['target_proxy_t_ledger_reduction_for_gcm_h6_1_20']}`",
        f"- Optimistic cache signal present: `{summary['optimistic_cache_signal_present']}`",
        f"- Shared synthesis object proposals: `{summary['shared_synthesis_object_count']}`",
        f"- Shared object existence gate passed: `{summary['shared_object_existence_gate_passed']}`",
        f"- Acceptance gates passed / total: `{summary['cost_model_acceptance_pass_count']}` / `{summary['cost_model_acceptance_gate_count']}`",
        f"- Cost model accepted: `{summary['cost_model_accepted']}`",
        f"- B7 ledger proxy-T reduction after cost model: `{summary['b7_ledger_proxy_t_reduction_after_cost_model']}`",
        f"- Additional occurrence certificates required: `{summary['additional_occurrence_certificates_required']}`",
        f"- Additional cost-model gates required: `{summary['additional_cost_model_gates_required']}`",
        f"- Validation errors: `{summary['validation_error_count']}`",
        "",
        "## Acceptance Gates",
        "",
        "| gate | requirement | current evidence | required evidence | passed |",
        "|---|---|---:|---:|---|",
    ]
    for row in payload["cost_model_acceptance_gates"]:
        lines.append(
            f"| {row['gate_id']} | {row['requirement']} | `{row['current_evidence']}` | "
            f"`{row['required_evidence']}` | `{row['passed']}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The repeated-theta structure is valuable because it identifies where a "
            "future physical-sharing proposal would have leverage. The shared object "
            "proposal closes the object-existence gap, but it is not enough by itself. "
            "A future PR must satisfy the remaining gates, or bypass the cost-model "
            "route by producing 30 occurrence-removing certificates.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    root = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--theta-sharing-gate",
        type=Path,
        default=root / "results" / "B1_B7_cone01_theta_sharing_ledger_gate_v0.json",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=root / "results" / "B1_B7_cone01_theta_sharing_cost_model_gate_v0.json",
    )
    parser.add_argument(
        "--shared-object-gate",
        type=Path,
        default=root / "results" / "B1_B7_cone01_shared_theta_synthesis_object_gate_v0.json",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=root / "research" / "B1_B7_cone01_theta_sharing_cost_model_gate.md",
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
