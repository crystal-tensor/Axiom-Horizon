#!/usr/bin/env python3
"""Build a B5/B10 same-access production contract gate from current evidence."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b5_b10_same_access_production_contract_gate_v0"
STATUS = "same_access_production_contract_failed"
MODEL_STATUS = "production_dmrg_or_response_oracle_requirements_unmet"
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


def contract_gate(
    gate_id: str,
    label: str,
    passed: bool,
    evidence: dict[str, Any],
    required_next_step: str,
) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
        "required_next_step": required_next_step,
    }


def build_payload(readiness_path: Path, smoke_path: Path, bridge_path: Path) -> dict[str, Any]:
    started = time.time()
    readiness = load_json(readiness_path)
    smoke = load_json(smoke_path)
    bridge = load_json(bridge_path)

    readiness_summary = readiness["summary"]
    smoke_summary = smoke["summary"]
    bridge_summary = bridge["summary"]

    instance_count = int(readiness_summary["instance_count"])
    if int(smoke_summary["instance_count"]) != instance_count:
        raise ValueError("B5 readiness and smoke gates must cover the same instance count")
    if int(bridge_summary["b5_instance_count"]) != instance_count:
        raise ValueError("B10 bridge must cover the same B5 instance count")

    production_dmrg_available = bool(bridge_summary["production_dmrg_available"])
    smoke_passed_rows = int(smoke_summary["smoke_passed_row_count"])
    readiness_passed_gates = int(readiness_summary["passed_gate_count"])
    blocking_sampling_requirements = int(bridge_summary["blocking_sampling_requirement_count"])
    same_access_positive_route_ready = bool(bridge_summary["same_access_positive_route_ready"])
    sampling_oracle_constructed = bool(bridge_summary["sampling_oracle_constructed"])
    seeded_mean = float(bridge_summary["seeded_mps_mean_relative_response_error"])
    variational_mean = float(bridge_summary["variational_mps_mean_relative_response_error"])
    seeded_beats_non_oracle_rows = int(bridge_summary["seeded_mps_rows_beating_non_oracle_embedding"])
    variational_beats_seeded_rows = int(bridge_summary["variational_mps_rows_beating_seeded_pressure"])

    gates = [
        contract_gate(
            "P1",
            "Same B5/B10 response rows are covered",
            True,
            {
                "readiness_instance_count": instance_count,
                "smoke_instance_count": smoke_summary["instance_count"],
                "bridge_b5_instance_count": bridge_summary["b5_instance_count"],
            },
            "Keep the same row IDs and response observable contract for all future production runs.",
        ),
        contract_gate(
            "P2",
            "Production DMRG denominator is available",
            production_dmrg_available,
            {"production_dmrg_available": production_dmrg_available},
            "Add a non-exact-state-seeded canonical DMRG/MPS denominator with convergence and cost ledgers.",
        ),
        contract_gate(
            "P3",
            "Canonical-environment smoke rows pass",
            smoke_passed_rows == instance_count,
            {"smoke_passed_row_count": smoke_passed_rows, "required_rows": instance_count},
            "Make all rows pass fixed-sector, variance, discarded-weight, monotonicity, and response checks.",
        ),
        contract_gate(
            "P4",
            "Readiness gates pass",
            readiness_passed_gates == int(readiness_summary["readiness_gate_count"]),
            {
                "readiness_passed_gate_count": readiness_passed_gates,
                "readiness_gate_count": readiness_summary["readiness_gate_count"],
            },
            "Satisfy the full canonical-DMRG readiness checklist before promoting B5 evidence.",
        ),
        contract_gate(
            "P5",
            "Non-seeded production route beats seeded pressure",
            variational_beats_seeded_rows > 0 and production_dmrg_available,
            {
                "variational_mps_rows_beating_seeded_pressure": variational_beats_seeded_rows,
                "production_dmrg_available": production_dmrg_available,
                "seeded_mps_mean_relative_response_error": seeded_mean,
                "variational_mps_mean_relative_response_error": variational_mean,
            },
            "Beat the exact-state-seeded pressure reference without using exact-state seeding.",
        ),
        contract_gate(
            "P6",
            "Seeded pressure is replaced by a deployable denominator",
            production_dmrg_available and seeded_beats_non_oracle_rows == 0,
            {
                "seeded_mps_rows_beating_non_oracle_embedding": seeded_beats_non_oracle_rows,
                "seeded_pressure_is_deployable": False,
            },
            "Replace exact-state-seeded MPS pressure with deployable tensor or DMRG evidence.",
        ),
        contract_gate(
            "P7",
            "Sampling or response oracle is constructed",
            sampling_oracle_constructed,
            {"sampling_oracle_constructed": sampling_oracle_constructed},
            "Construct a response observable sampler with preparation, mixing, variance, and confidence costs.",
        ),
        contract_gate(
            "P8",
            "Sampling requirements no longer block the bridge",
            blocking_sampling_requirements == 0,
            {"blocking_sampling_requirement_count": blocking_sampling_requirements},
            "Resolve all B10 same-access sampling requirements before claiming a positive route.",
        ),
        contract_gate(
            "P9",
            "Positive same-access route exists after full costs",
            same_access_positive_route_ready,
            {"same_access_positive_route_ready": same_access_positive_route_ready},
            "Beat the full denominator ladder after optimizer-loop, measurement, and classical-denominator costs.",
        ),
        contract_gate(
            "P10",
            "No forbidden claim is made",
            True,
            {
                "quantum_advantage_claimed": False,
                "bqp_separation_claimed": False,
                "same_access_positive_route_claimed": False,
                "production_dmrg_claimed": False,
            },
            "Keep claim boundaries explicit until the production contract passes.",
        ),
    ]

    pass_count = sum(1 for gate in gates if gate["passed"])
    fail_count = len(gates) - pass_count

    validation_errors: list[str] = []
    if instance_count != 9:
        validation_errors.append("contract must cover the nine current B5/B10 D5 Hubbard response rows")
    if pass_count != 2:
        validation_errors.append("current contract should pass only row coverage and no-forbidden-claim gates")
    if production_dmrg_available:
        validation_errors.append("current bridge unexpectedly reports production DMRG available")
    if smoke_passed_rows != 0:
        validation_errors.append("current canonical-environment smoke gate unexpectedly passed rows")
    if readiness_passed_gates != 0:
        validation_errors.append("current canonical DMRG readiness gate unexpectedly passed conditions")
    if blocking_sampling_requirements != 5:
        validation_errors.append("current bridge should still have five blocking sampling requirements")
    if same_access_positive_route_ready:
        validation_errors.append("current bridge unexpectedly reports a positive same-access route")
    if sampling_oracle_constructed:
        validation_errors.append("current bridge unexpectedly constructs a sampling oracle")
    for source, payload in [
        ("readiness", readiness),
        ("smoke", smoke),
        ("bridge", bridge),
    ]:
        if payload.get("validation_errors"):
            validation_errors.append(f"{source} source already has validation errors")

    summary = {
        "instance_count": instance_count,
        "contract_gate_count": len(gates),
        "contract_pass_count": pass_count,
        "contract_fail_count": fail_count,
        "contract_acceptance_passed": False,
        "production_contract_ready": False,
        "production_dmrg_available": production_dmrg_available,
        "canonical_environment_smoke_passed_rows": smoke_passed_rows,
        "readiness_passed_gate_count": readiness_passed_gates,
        "blocking_sampling_requirement_count": blocking_sampling_requirements,
        "sampling_oracle_constructed": sampling_oracle_constructed,
        "same_access_positive_route_ready": same_access_positive_route_ready,
        "b10_t1_positive_route_ready": False,
        "seeded_mps_mean_relative_response_error": seeded_mean,
        "variational_mps_mean_relative_response_error": variational_mean,
        "seeded_mps_rows_beating_non_oracle_embedding": seeded_beats_non_oracle_rows,
        "variational_mps_rows_beating_seeded_pressure": variational_beats_seeded_rows,
        "production_dmrg_claimed": False,
        "quantum_response_win_claimed": False,
        "accuracy_per_resource_win_claimed": False,
        "same_access_positive_route_claimed": False,
        "quantum_advantage_claimed": False,
        "bqp_separation_claimed": False,
        "dequantization_theorem_claimed": False,
        "sampling_access_theorem_claimed": False,
        "validation_error_count": len(validation_errors),
    }

    return {
        "benchmark_id": "B5",
        "problem_id": 38,
        "linked_benchmark_id": "B10",
        "linked_problem_id": 11,
        "title": "B5/B10 same-access production contract gate",
        "version": VERSION,
        "last_updated": time.strftime("%Y-%m-%d"),
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_readiness_result": str(readiness_path),
        "source_smoke_result": str(smoke_path),
        "source_same_access_bridge_result": str(bridge_path),
        "summary": summary,
        "contract_gates": gates,
        "claim_boundary": {
            "what_is_supported": (
                "The current B5/B10 evidence covers the same nine Hubbard response rows and keeps forbidden "
                "claims off, but the production same-access contract fails."
            ),
            "what_is_not_supported": (
                "This is not production DMRG, not a deployable tensor solver, not a response sampling oracle, "
                "not a same-access positive route, not quantum advantage, and not a BQP separation."
            ),
            "next_gate": (
                "Implement mature canonical-environment production DMRG/MPS or a real same-access response "
                "oracle with state-preparation, mixing, measurement, confidence, optimizer-loop, and classical "
                "denominator costs."
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
        "validation_errors": validation_errors,
        "runtime_seconds": round(time.time() - started, 6),
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# B5/B10 Same-Access Production Contract Gate v0.1",
        "",
        f"Last updated: {payload['last_updated']}",
        "",
        f"Status: **{payload['status']}**",
        "",
        "## Summary",
        "",
        f"- Method: `{payload['method']}`",
        f"- Model status: `{payload['model_status']}`",
        f"- Instances: {summary['instance_count']}",
        f"- Contract gates passed/failed: {summary['contract_pass_count']} / {summary['contract_fail_count']}",
        f"- Production DMRG available: {summary['production_dmrg_available']}",
        f"- Canonical-environment smoke rows passed: {summary['canonical_environment_smoke_passed_rows']}",
        f"- Readiness gates passed: {summary['readiness_passed_gate_count']}",
        f"- Blocking sampling requirements: {summary['blocking_sampling_requirement_count']}",
        f"- Same-access positive route ready: {summary['same_access_positive_route_ready']}",
        f"- Validation errors: {summary['validation_error_count']}",
        "",
        "## Contract Gates",
        "",
        "| Gate | Passed | Evidence | Required next step |",
        "|---|---:|---|---|",
    ]
    for gate in payload["contract_gates"]:
        evidence = "; ".join(f"{key}={fmt(value)}" for key, value in gate["evidence"].items())
        lines.append(
            f"| {gate['gate_id']}: {gate['label']} | {gate['passed']} | {evidence} | {gate['required_next_step']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The current portfolio now has a machine-checkable B5/B10 production contract rather than a loose next-step description.",
            "Only the row-coverage and no-forbidden-claim gates pass. The production route remains blocked by no production DMRG, no smoke-passed rows, no readiness gates, five blocking sampling requirements, and no same-access positive route.",
            "This artifact should be treated as the acceptance contract for future T-B5-006 and T-B10-014 work.",
            "",
            "## Claim Boundary",
            "",
        ]
    )
    for key, value in payload["claim_boundary"].items():
        lines.append(f"- {key}: {value}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readiness", type=Path, default=Path("results/B5_canonical_dmrg_readiness_gate_v0.json"))
    parser.add_argument("--smoke", type=Path, default=Path("results/B5_canonical_environment_smoke_gate_v0.json"))
    parser.add_argument(
        "--bridge",
        type=Path,
        default=Path("results/B10_t1_b5_same_access_sampling_or_dmrg_bridge_v0.json"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B5_B10_same_access_production_contract_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B5_B10_same_access_production_contract_gate.md"),
    )
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    payload = build_payload(args.readiness, args.smoke, args.bridge)
    write_json(args.json_output, payload, pretty=args.pretty)
    write_markdown(args.markdown_output, payload)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
