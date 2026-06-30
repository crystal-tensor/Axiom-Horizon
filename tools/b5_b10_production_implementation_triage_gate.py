#!/usr/bin/env python3
"""T-B5-006c/T-B10-014a: split the failed B5/B10 contract into PR-sized work."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b5_b10_production_implementation_triage_gate_v0"
STATUS = "production_implementation_triage_ready_no_positive_route"
MODEL_STATUS = "failed_production_contract_split_into_parallel_pr_work"
VERSION = "0.1"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any], pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if pretty:
        text = json.dumps(payload, indent=2, sort_keys=True)
    else:
        text = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    path.write_text(text + "\n", encoding="utf-8")


def fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def packet(
    packet_id: str,
    title: str,
    owner_role: str,
    status: str,
    blocker_gate_ids: list[str],
    expected_artifacts: list[str],
    acceptance_evidence: list[str],
) -> dict[str, Any]:
    return {
        "packet_id": packet_id,
        "title": title,
        "owner_role": owner_role,
        "status": status,
        "blocker_gate_ids": blocker_gate_ids,
        "expected_artifacts": expected_artifacts,
        "acceptance_evidence": acceptance_evidence,
    }


def condition(condition_id: str, label: str, satisfied: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "condition_id": condition_id,
        "label": label,
        "satisfied": bool(satisfied),
        "evidence": evidence,
    }


def build_payload(contract_path: Path) -> dict[str, Any]:
    started = time.time()
    contract = load_json(contract_path)
    summary = contract["summary"]
    gates = contract["contract_gates"]
    gate_by_id = {gate["gate_id"]: gate for gate in gates}

    failed_gate_ids = [gate["gate_id"] for gate in gates if not gate["passed"]]
    passed_gate_ids = [gate["gate_id"] for gate in gates if gate["passed"]]
    expected_failed = ["P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9"]

    work_packets = [
        packet(
            "W1",
            "Canonical production DMRG/MPS denominator engine",
            "correlated-matter-agent",
            "blocked_on_implementation",
            ["P2", "P3", "P4", "P5", "P6"],
            [
                "tools/b5_production_dmrg_mps_denominator.py",
                "results/B5_production_dmrg_mps_denominator_v0.json",
                "research/B5_production_dmrg_mps_denominator.md",
            ],
            [
                "all nine response rows covered",
                "stored left/right environments",
                "orthonormal residual ledger",
                "sweep convergence ledger",
                "no exact-state seeding",
                "rows beating seeded pressure or explicitly failing it",
            ],
        ),
        packet(
            "W2",
            "Exact-state seed removal and denominator replay",
            "baseline-adversary",
            "blocked_on_denominator",
            ["P5", "P6"],
            [
                "tools/b5_seeded_pressure_replacement_audit.py",
                "results/B5_seeded_pressure_replacement_audit_v0.json",
                "research/B5_seeded_pressure_replacement_audit.md",
            ],
            [
                "seeded MPS pressure no longer strongest or remains explicit blocker",
                "same row IDs and observable contract preserved",
                "selection rule does not consume exact target states",
            ],
        ),
        packet(
            "W3",
            "Same-access response oracle cost ledger",
            "quantum-response-agent",
            "blocked_on_oracle_construction",
            ["P7", "P8", "P9"],
            [
                "tools/b5_b10_response_oracle_cost_ledger.py",
                "results/B5_B10_response_oracle_cost_ledger_v0.json",
                "research/B5_B10_response_oracle_cost_ledger.md",
            ],
            [
                "state-preparation cost",
                "mixing or response-query cost",
                "measurement variance and confidence ledger",
                "classical denominator comparison",
                "no hidden access advantage",
            ],
        ),
        packet(
            "W4",
            "Row-contract preservation harness",
            "audit-agent",
            "ready_now",
            [],
            [
                "tools/b5_b10_row_contract_harness.py",
                "results/B5_B10_row_contract_harness_v0.json",
                "research/B5_B10_row_contract_harness.md",
            ],
            [
                "nine row IDs preserved",
                "response observable names preserved",
                "D5 denominator ladder linked",
                "future production outputs rejected if row contract drifts",
            ],
        ),
        packet(
            "W5",
            "B10-T1 theorem-boundary integration note",
            "theory-agent",
            "blocked_on_positive_denominator_or_oracle",
            ["P2", "P5", "P7", "P9"],
            [
                "research/B10_t1_b5_production_boundary_integration.md",
                "results/B10_t1_b5_production_boundary_integration_v0.json",
            ],
            [
                "explicit theorem assumptions",
                "same-access denominator branch status",
                "oracle branch status",
                "no BQP separation or dequantization theorem claim",
            ],
        ),
        packet(
            "W6",
            "Claim-safety and audit wiring",
            "maintainer-agent",
            "ready_now",
            [],
            [
                "tools/research_portfolio_audit.py",
                "research/portfolio_status_report.json",
                "research/portfolio_status_report.md",
            ],
            [
                "forbidden claims remain false",
                "future readiness upgrades must cite machine-readable evidence",
                "landing page updates preserve style and only update research content",
            ],
        ),
    ]

    ready_packets = [p for p in work_packets if p["status"] == "ready_now"]
    blocked_packets = [p for p in work_packets if p["status"] != "ready_now"]
    blocker_to_packets: dict[str, list[str]] = {gate_id: [] for gate_id in expected_failed}
    for p in work_packets:
        for gate_id in p["blocker_gate_ids"]:
            blocker_to_packets.setdefault(gate_id, []).append(p["packet_id"])

    readiness_conditions = [
        condition(
            "C1",
            "Source production contract is present and failed",
            contract.get("method") == "b5_b10_same_access_production_contract_gate_v0"
            and contract.get("status") == "same_access_production_contract_failed",
            {"source_method": contract.get("method"), "source_status": contract.get("status")},
        ),
        condition(
            "C2",
            "Failed production gates are exactly P2-P9",
            failed_gate_ids == expected_failed,
            {"failed_gate_ids": failed_gate_ids, "expected_failed_gate_ids": expected_failed},
        ),
        condition(
            "C3",
            "All current blockers are assigned to at least one work packet",
            all(blocker_to_packets.get(gate_id) for gate_id in expected_failed),
            {"blocker_to_packets": blocker_to_packets},
        ),
        condition(
            "C4",
            "At least two immediate maintenance/audit packets are ready",
            len(ready_packets) >= 2,
            {"ready_packet_ids": [p["packet_id"] for p in ready_packets]},
        ),
        condition(
            "C5",
            "Positive-route and forbidden claims remain false",
            summary.get("same_access_positive_route_ready") is False
            and summary.get("production_dmrg_claimed") is False
            and summary.get("quantum_response_win_claimed") is False
            and summary.get("quantum_advantage_claimed") is False
            and summary.get("bqp_separation_claimed") is False,
            {
                "same_access_positive_route_ready": summary.get("same_access_positive_route_ready"),
                "production_dmrg_claimed": summary.get("production_dmrg_claimed"),
                "quantum_response_win_claimed": summary.get("quantum_response_win_claimed"),
                "quantum_advantage_claimed": summary.get("quantum_advantage_claimed"),
                "bqp_separation_claimed": summary.get("bqp_separation_claimed"),
            },
        ),
        condition(
            "C6",
            "T-B5-006/T-B10-014 next gate is executable without changing the 100-problem catalog",
            True,
            {
                "catalog_change_required": False,
                "next_gate": "run W1/W2/W3 while W4/W6 enforce row and claim contracts",
            },
        ),
    ]

    validation_errors: list[str] = []
    if summary.get("instance_count") != 9:
        validation_errors.append("B5/B10 triage must stay on the same nine response rows")
    if failed_gate_ids != expected_failed:
        validation_errors.append("failed production gate IDs changed from expected P2-P9")
    if passed_gate_ids != ["P1", "P10"]:
        validation_errors.append("passed production gate IDs should remain P1/P10 only")
    if len(ready_packets) != 2:
        validation_errors.append("triage should have exactly two ready maintenance/audit packets")
    if len(blocked_packets) != 4:
        validation_errors.append("triage should have exactly four blocked implementation/theory packets")
    if any(not c["satisfied"] for c in readiness_conditions):
        validation_errors.append("all triage readiness conditions should be satisfied")
    if contract.get("validation_errors"):
        validation_errors.append("source production contract has validation errors")

    result_summary = {
        "source_contract_gate_count": int(summary["contract_gate_count"]),
        "source_contract_pass_count": int(summary["contract_pass_count"]),
        "source_contract_fail_count": int(summary["contract_fail_count"]),
        "failed_source_gate_ids": failed_gate_ids,
        "passed_source_gate_ids": passed_gate_ids,
        "work_packet_count": len(work_packets),
        "ready_packet_count": len(ready_packets),
        "blocked_packet_count": len(blocked_packets),
        "readiness_condition_count": len(readiness_conditions),
        "satisfied_readiness_condition_count": sum(1 for c in readiness_conditions if c["satisfied"]),
        "unsatisfied_readiness_condition_count": sum(1 for c in readiness_conditions if not c["satisfied"]),
        "production_dmrg_available": bool(summary["production_dmrg_available"]),
        "sampling_oracle_constructed": bool(summary["sampling_oracle_constructed"]),
        "same_access_positive_route_ready": bool(summary["same_access_positive_route_ready"]),
        "b10_t1_positive_route_ready": False,
        "production_dmrg_claimed": False,
        "quantum_response_win_claimed": False,
        "accuracy_per_resource_win_claimed": False,
        "same_access_positive_route_claimed": False,
        "quantum_advantage_claimed": False,
        "bqp_separation_claimed": False,
        "dequantization_theorem_claimed": False,
        "sampling_access_theorem_claimed": False,
        "catalog_change_required": False,
        "validation_error_count": len(validation_errors),
    }

    return {
        "benchmark_id": "B5",
        "problem_id": 38,
        "linked_benchmark_id": "B10",
        "linked_problem_id": 11,
        "title": "B5/B10 production implementation triage gate",
        "version": VERSION,
        "last_updated": time.strftime("%Y-%m-%d"),
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_production_contract_result": str(contract_path),
        "summary": result_summary,
        "readiness_conditions": readiness_conditions,
        "work_packets": work_packets,
        "blocker_to_packets": blocker_to_packets,
        "claim_boundary": {
            "what_is_supported": (
                "The failed B5/B10 production contract has been split into auditable PR-sized work packets. "
                "The next implementation steps are explicit and can be assigned to agents without changing "
                "the 100-problem catalog."
            ),
            "what_is_not_supported": (
                "This is not production DMRG, not a response oracle, not a positive same-access route, "
                "not quantum advantage, not BQP separation, and not a dequantization theorem."
            ),
            "next_gate": (
                "Run W1/W2/W3: a non-exact-state-seeded production DMRG/MPS denominator, a seeded-pressure "
                "replacement audit, or a fully costed same-access response oracle. Keep W4/W6 as row-contract "
                "and claim-safety guards."
            ),
            "production_dmrg_claimed": False,
            "quantum_response_win_claimed": False,
            "accuracy_per_resource_win_claimed": False,
            "same_access_positive_route_claimed": False,
            "quantum_advantage_claimed": False,
            "bqp_separation_claimed": False,
            "dequantization_theorem_claimed": False,
            "sampling_access_theorem_claimed": False,
        },
        "runtime_seconds": round(time.time() - started, 6),
        "validation_errors": validation_errors,
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    s = payload["summary"]
    cb = payload["claim_boundary"]
    lines = [
        "# B5/B10 Production Implementation Triage Gate v0.1",
        "",
        f"Last updated: {payload['last_updated']}",
        "",
        f"Status: **{payload['status']}**",
        "",
        "## Summary",
        "",
        f"- Method: `{payload['method']}`",
        f"- Model status: `{payload['model_status']}`",
        f"- Source contract gates passed/failed: {s['source_contract_pass_count']} / {s['source_contract_fail_count']}",
        f"- Failed source gates: {', '.join(s['failed_source_gate_ids'])}",
        f"- Work packets ready/blocked: {s['ready_packet_count']} / {s['blocked_packet_count']}",
        f"- Readiness conditions satisfied/unsatisfied: {s['satisfied_readiness_condition_count']} / {s['unsatisfied_readiness_condition_count']}",
        f"- Production DMRG available: {s['production_dmrg_available']}",
        f"- Sampling oracle constructed: {s['sampling_oracle_constructed']}",
        f"- Same-access positive route ready: {s['same_access_positive_route_ready']}",
        f"- Catalog change required: {s['catalog_change_required']}",
        f"- Validation errors: {s['validation_error_count']}",
        "",
        "## Work Packets",
        "",
        "| Packet | Status | Owner | Blockers | Expected artifacts | Acceptance evidence |",
        "|---|---|---|---|---|---|",
    ]
    for p in payload["work_packets"]:
        blockers = ", ".join(p["blocker_gate_ids"]) if p["blocker_gate_ids"] else "none"
        artifacts = "; ".join(p["expected_artifacts"])
        evidence = "; ".join(p["acceptance_evidence"])
        lines.append(
            f"| {p['packet_id']}: {p['title']} | {p['status']} | {p['owner_role']} | {blockers} | {artifacts} | {evidence} |"
        )
    lines.extend(
        [
            "",
            "## Readiness Conditions",
            "",
            "| Condition | Satisfied | Evidence |",
            "|---|---:|---|",
        ]
    )
    for c in payload["readiness_conditions"]:
        evidence = "; ".join(f"{k}={fmt(v)}" for k, v in c["evidence"].items())
        lines.append(f"| {c['condition_id']}: {c['label']} | {c['satisfied']} | {evidence} |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This gate turns the failed production contract into an executable multi-agent queue.",
            "W1, W2, and W3 are the only packets that can reopen B5/B10 as a positive technical route.",
            "W4 and W6 are ready guardrail packets: they preserve the row contract and keep unsupported claims out of the project state.",
            "The result is useful project motion, but it is still a negative/triage result rather than a production solver.",
            "",
            "## Claim Boundary",
            "",
        ]
    )
    for key, value in cb.items():
        lines.append(f"- {key}: {value}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path("results/B5_B10_same_access_production_contract_gate_v0.json"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B5_B10_production_implementation_triage_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B5_B10_production_implementation_triage_gate.md"),
    )
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_payload(args.contract)
    write_json(args.json_output, payload, pretty=args.pretty)
    write_markdown(args.markdown_output, payload)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "work_packet_count": payload["summary"]["work_packet_count"],
                "ready_packet_count": payload["summary"]["ready_packet_count"],
                "blocked_packet_count": payload["summary"]["blocked_packet_count"],
                "validation_errors": payload["validation_errors"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    if payload["validation_errors"]:
        raise SystemExit("B5/B10 production implementation triage gate validation failed")


if __name__ == "__main__":
    main()
