#!/usr/bin/env python3
"""Build the T-B2-008 decoder-input feasibility gate."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b2_decoder_input_contract_feasibility_gate_v0"
STATUS = "decoder_input_contract_failed_calibrated_data_or_decoder_required"
MODEL_STATUS = "decoder_input_contract_from_aggregate_rows_not_circuit_level_decoder"
VERSION = "0.1"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def gate(
    gate_id: str,
    label: str,
    passed: bool,
    critical: bool,
    evidence: dict[str, Any],
    required_next_step: str,
) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "label": label,
        "passed": bool(passed),
        "critical": bool(critical),
        "evidence": evidence,
        "required_next_step": required_next_step,
    }


def build_report(risk_path: Path, shot_path: Path) -> dict[str, Any]:
    started = time.time()
    risk = load_json(risk_path)
    shot = load_json(shot_path)
    risk_summary = risk["summary"]
    shot_summary = shot["summary"]
    adjusted_survivors = risk.get("adjusted_survivor_rows", [])

    survivor_profiles = sorted({row["profile"] for row in adjusted_survivors})
    survivor_budgets = sorted({row["risk_budget"] for row in adjusted_survivors})
    strict_survivors = [
        row for row in adjusted_survivors if row["risk_budget"] == "strict_decoder_penalty"
    ]
    conservative_survivors = [
        row for row in adjusted_survivors if row["risk_budget"] == "conservative_decoder_penalty"
    ]

    contract_inputs = [
        {
            "input": "stim_detector_error_model",
            "available": True,
            "source": "upstream Stim/PyMatching false-positive stress",
            "blocker": None,
        },
        {
            "input": "aggregate_target_volume_rows",
            "available": True,
            "source": str(risk_path),
            "blocker": None,
        },
        {
            "input": "posterior_flag_probabilities",
            "available": True,
            "source": str(shot_path),
            "blocker": None,
        },
        {
            "input": "risk_adjusted_volume_rows",
            "available": True,
            "source": str(risk_path),
            "blocker": None,
        },
        {
            "input": "per_shot_syndrome_bitstrings",
            "available": False,
            "source": None,
            "blocker": "Only aggregate target-comparison rows are retained; per-shot syndrome traces are not present.",
        },
        {
            "input": "per_detector_flag_event_ids",
            "available": False,
            "source": None,
            "blocker": "Flag posterior rows are profile-level rows, not detector/tick-indexed flag events.",
        },
        {
            "input": "decoder_likelihood_injection_api",
            "available": False,
            "source": None,
            "blocker": "No PyMatching/Stim decoder path consumes posterior flag probabilities as edge weights.",
        },
        {
            "input": "calibrated_leakage_confusion_matrix",
            "available": False,
            "source": None,
            "blocker": "Detection efficiency and false-positive rates are profile assumptions, not measured calibration data.",
        },
        {
            "input": "holdout_validation_or_hardware_trace",
            "available": False,
            "source": None,
            "blocker": "No hardware trace, calibrated dataset, or holdout split exists for posterior-weight validation.",
        },
        {
            "input": "decoder_runtime_and_threshold_curve",
            "available": False,
            "source": None,
            "blocker": "No circuit-level shot-conditioned decoder runtime or distance-scaling curve has been measured.",
        },
    ]

    available_contract_inputs = sum(1 for row in contract_inputs if row["available"])
    missing_contract_inputs = len(contract_inputs) - available_contract_inputs

    gates = [
        gate(
            "G1",
            "Posterior flag probabilities exist",
            True,
            False,
            {
                "evaluated_profile_rows": shot_summary["evaluated_profile_rows"],
                "calibration_profile_count": shot_summary["calibration_profile_count"],
            },
            "Keep carrying posterior fields into decoder-facing artifacts.",
        ),
        gate(
            "G2",
            "Conservative risk-adjusted d=5/d=7 survivors exist",
            int(risk_summary["conservative_adjusted_surviving_d5_d7_rows"]) > 0,
            False,
            {
                "conservative_adjusted_surviving_d5_d7_rows": risk_summary[
                    "conservative_adjusted_surviving_d5_d7_rows"
                ],
                "conservative_max_decoder_adjusted_reduction": risk_summary[
                    "conservative_max_decoder_adjusted_reduction"
                ],
            },
            "Preserve these rows only as candidate rows for a real decoder run.",
        ),
        gate(
            "G3",
            "Strict risk-adjusted d=5/d=7 survivors exist",
            int(risk_summary["strict_adjusted_surviving_d5_d7_rows"]) > 0,
            False,
            {
                "strict_adjusted_surviving_d5_d7_rows": risk_summary[
                    "strict_adjusted_surviving_d5_d7_rows"
                ],
                "strict_max_decoder_adjusted_reduction": risk_summary[
                    "strict_max_decoder_adjusted_reduction"
                ],
            },
            "Run a decoder with these rows as challenge cases.",
        ),
        gate(
            "G4",
            "Strict high-purity survivor exists",
            int(risk_summary["strict_high_purity_adjusted_survivors"]) > 0,
            True,
            {
                "strict_high_purity_adjusted_survivors": risk_summary[
                    "strict_high_purity_adjusted_survivors"
                ],
            },
            "Obtain high-purity flag rows or demote the route under strict calibration assumptions.",
        ),
        gate(
            "G5",
            "All-profile robustness exists",
            bool(risk_summary["robust_all_profile_adjusted_survival"]),
            True,
            {
                "robust_all_profile_adjusted_survival": risk_summary[
                    "robust_all_profile_adjusted_survival"
                ],
                "survivor_profiles": survivor_profiles,
            },
            "Show survival across all declared detector profiles or keep the route profile-sensitive.",
        ),
        gate(
            "G6",
            "Per-shot syndrome and flag traces are available",
            False,
            True,
            {
                "per_shot_syndrome_bitstrings": False,
                "per_detector_flag_event_ids": False,
            },
            "Persist shot-level syndrome bitstrings and detector/tick-indexed flag events from Stim or hardware.",
        ),
        gate(
            "G7",
            "Posterior probabilities are injected into a circuit-level decoder",
            False,
            True,
            {
                "decoder_likelihood_injection_api": False,
                "circuit_level_decoder_claimed": False,
            },
            "Implement a PyMatching/Stim decoder path that consumes posterior flag likelihoods as edge weights.",
        ),
        gate(
            "G8",
            "Calibrated leakage/flag data are available",
            False,
            True,
            {
                "calibrated_leakage_confusion_matrix": False,
                "holdout_validation_or_hardware_trace": False,
            },
            "Collect calibrated leakage/flag data or provide a holdout validation split.",
        ),
        gate(
            "G9",
            "Claim boundary remains clean",
            True,
            False,
            {
                "new_code_claimed": False,
                "threshold_claimed": False,
                "production_decoder_claimed": False,
                "hardware_result_claimed": False,
            },
            "Continue to block threshold, hardware, and new-code claims until a real decoder passes.",
        ),
    ]
    passed_gate_count = sum(1 for row in gates if row["passed"])
    failed_gate_count = len(gates) - passed_gate_count
    failed_critical_gate_count = sum(1 for row in gates if row["critical"] and not row["passed"])

    summary = {
        "contract_input_count": len(contract_inputs),
        "available_contract_input_count": available_contract_inputs,
        "missing_contract_input_count": missing_contract_inputs,
        "feasibility_gate_count": len(gates),
        "passed_gate_count": passed_gate_count,
        "failed_gate_count": failed_gate_count,
        "failed_critical_gate_count": failed_critical_gate_count,
        "decoder_contract_satisfied": False,
        "demotion_recommended_until_decoder_or_calibration": True,
        "source_raw_surviving_d5_d7_rows": risk_summary["source_raw_surviving_d5_d7_rows"],
        "conservative_adjusted_surviving_d5_d7_rows": risk_summary[
            "conservative_adjusted_surviving_d5_d7_rows"
        ],
        "strict_adjusted_surviving_d5_d7_rows": risk_summary[
            "strict_adjusted_surviving_d5_d7_rows"
        ],
        "strict_high_purity_adjusted_survivors": risk_summary[
            "strict_high_purity_adjusted_survivors"
        ],
        "robust_all_profile_adjusted_survival": risk_summary[
            "robust_all_profile_adjusted_survival"
        ],
        "adjusted_survivor_row_count": len(adjusted_survivors),
        "strict_survivor_row_count": len(strict_survivors),
        "conservative_survivor_row_count": len(conservative_survivors),
        "survivor_profiles": survivor_profiles,
        "survivor_risk_budgets": survivor_budgets,
        "circuit_level_decoder_claimed": False,
        "production_decoder_claimed": False,
        "threshold_claimed": False,
        "hardware_result_claimed": False,
        "new_code_claimed": False,
        "validation_error_count": 0,
    }

    validation_errors = validate(summary, gates, contract_inputs)
    summary["validation_error_count"] = len(validation_errors)
    return {
        "benchmark_id": "B2",
        "problem_id": 22,
        "title": "B2 decoder input contract feasibility gate",
        "version": VERSION,
        "last_updated": time.strftime("%Y-%m-%d"),
        "status": STATUS,
        "method": METHOD,
        "model_status": MODEL_STATUS,
        "source_posterior_risk_ledger": str(risk_path),
        "source_shot_conditioned_boundary": str(shot_path),
        "summary": summary,
        "decoder_contract_inputs": contract_inputs,
        "feasibility_gates": gates,
        "strict_survivor_rows": strict_survivors,
        "claim_boundary": {
            "decoder_input_contract_built": True,
            "demotion_recommended_until_decoder_or_calibration": True,
            "circuit_level_decoder_claimed": False,
            "shot_conditioned_erasure_decoder_claimed": False,
            "production_decoder_claimed": False,
            "threshold_claimed": False,
            "new_code_claimed": False,
            "hardware_result_claimed": False,
            "calibrated_device_claimed": False,
            "what_is_supported": (
                "A decoder-facing input contract and feasibility gate over the current posterior/risk rows."
            ),
            "what_is_not_supported": (
                "This is not a circuit-level shot-conditioned decoder, not a production decoder, "
                "not calibrated leakage data, not a threshold result, not a hardware result, and not a new-code claim."
            ),
            "next_gate": (
                "Persist per-shot syndrome/flag traces and implement posterior likelihood injection in a decoder, "
                "or collect calibrated leakage/flag data."
            ),
        },
        "validation_errors": validation_errors,
        "runtime_seconds": round(time.time() - started, 6),
    }


def validate(
    summary: dict[str, Any],
    gates: list[dict[str, Any]],
    contract_inputs: list[dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    if summary["contract_input_count"] != 10:
        errors.append("expected ten decoder contract inputs")
    if summary["available_contract_input_count"] != 4:
        errors.append("expected four currently available decoder contract inputs")
    if summary["feasibility_gate_count"] != 9:
        errors.append("expected nine feasibility gates")
    if summary["failed_critical_gate_count"] < 4:
        errors.append("expected at least four failed critical gates")
    if summary["strict_high_purity_adjusted_survivors"] != 0:
        errors.append("strict high-purity survivors must remain zero")
    if summary["robust_all_profile_adjusted_survival"] is not False:
        errors.append("all-profile robustness must remain false")
    if summary["decoder_contract_satisfied"] is not False:
        errors.append("decoder contract must not be marked satisfied")
    if summary["demotion_recommended_until_decoder_or_calibration"] is not True:
        errors.append("demotion should be recommended until decoder or calibration exists")
    for field in [
        "circuit_level_decoder_claimed",
        "production_decoder_claimed",
        "threshold_claimed",
        "hardware_result_claimed",
        "new_code_claimed",
    ]:
        if summary[field] is not False:
            errors.append(f"{field} must remain False")
    if not any(row["input"] == "per_shot_syndrome_bitstrings" and not row["available"] for row in contract_inputs):
        errors.append("missing per-shot syndrome blocker")
    if any(row["critical"] and not row["passed"] for row in gates) is not True:
        errors.append("at least one critical feasibility gate must fail")
    return errors


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# B2 Decoder Input Contract Feasibility Gate v0.1",
        "",
        f"Last updated: {report['last_updated']}",
        "",
        f"Status: **{report['status']}**",
        "",
        "## Summary",
        "",
        f"- Method: `{report['method']}`",
        f"- Model status: `{report['model_status']}`",
        f"- Contract inputs available/missing: {summary['available_contract_input_count']} / {summary['missing_contract_input_count']}",
        f"- Feasibility gates passed/failed: {summary['passed_gate_count']} / {summary['failed_gate_count']}",
        f"- Failed critical gates: {summary['failed_critical_gate_count']}",
        f"- Raw / conservative / strict d=5/d=7 survivors: {summary['source_raw_surviving_d5_d7_rows']} / {summary['conservative_adjusted_surviving_d5_d7_rows']} / {summary['strict_adjusted_surviving_d5_d7_rows']}",
        f"- Strict high-purity adjusted survivors: {summary['strict_high_purity_adjusted_survivors']}",
        f"- Robust all-profile adjusted survival: {summary['robust_all_profile_adjusted_survival']}",
        f"- Decoder contract satisfied: {summary['decoder_contract_satisfied']}",
        f"- Demotion recommended until decoder or calibration: {summary['demotion_recommended_until_decoder_or_calibration']}",
        f"- Validation errors: {summary['validation_error_count']}",
        "",
        "## Decoder Contract Inputs",
        "",
        "| Input | Available | Source or blocker |",
        "|---|---:|---|",
    ]
    for row in report["decoder_contract_inputs"]:
        source_or_blocker = row["source"] if row["available"] else row["blocker"]
        lines.append(f"| {row['input']} | {row['available']} | {source_or_blocker} |")
    lines.extend(
        [
            "",
            "## Feasibility Gates",
            "",
            "| Gate | Critical | Passed | Evidence | Required next step |",
            "|---|---:|---:|---|---|",
        ]
    )
    for row in report["feasibility_gates"]:
        evidence = "; ".join(f"{key}={fmt(value)}" for key, value in row["evidence"].items())
        lines.append(
            f"| {row['gate_id']}: {row['label']} | {row['critical']} | {row['passed']} | {evidence} | {row['required_next_step']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The current B2 heralded-erasure route has useful posterior/risk rows, but it still lacks the data shape needed by a circuit-level shot-conditioned decoder.",
            "The route should stay demoted until per-shot syndrome/flag traces, posterior likelihood injection, and calibrated leakage/flag validation exist.",
            "",
            "## Claim Boundary",
            "",
        ]
    )
    for key, value in report["claim_boundary"].items():
        lines.append(f"- {key}: {value}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--risk-ledger",
        type=Path,
        default=Path("results/B2_posterior_weighted_decoder_risk_ledger_v0.json"),
    )
    parser.add_argument(
        "--shot-boundary",
        type=Path,
        default=Path("results/B2_shot_conditioned_erasure_decoder_boundary_v0.json"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B2_decoder_input_contract_feasibility_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B2_decoder_input_contract_feasibility_gate.md"),
    )
    args = parser.parse_args()
    report = build_report(args.risk_ledger, args.shot_boundary)
    write_json(args.json_output, report)
    write_markdown(report, args.markdown_output)
    print(json.dumps(report["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
