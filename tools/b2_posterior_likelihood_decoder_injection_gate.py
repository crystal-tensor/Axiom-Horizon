#!/usr/bin/env python3
"""Consume B2 per-shot traces with a posterior-likelihood decoder injection gate."""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path
from typing import Any

import numpy as np
import pymatching

from b2_stim_heralded_erasure_stress import base_circuit, inject_tick_noise, wilson_interval


METHOD = "b2_posterior_likelihood_decoder_injection_gate_v0"
STATUS = "posterior_likelihood_injection_interface_negative_boundary"
MODEL_STATUS = "per_shot_synthetic_flag_likelihood_injection_not_calibrated_decoder"
VERSION = "0.1"


INJECTION_PROFILES = [
    {
        "name": "mild_flag_weight_shift",
        "alpha": 0.25,
        "min_weight": 0.25,
        "claim_level": "interface_sensitivity",
    },
    {
        "name": "nominal_flag_weight_shift",
        "alpha": 0.50,
        "min_weight": 0.10,
        "claim_level": "interface_sensitivity",
    },
    {
        "name": "strong_flag_weight_shift",
        "alpha": 0.75,
        "min_weight": 0.05,
        "claim_level": "stress_only",
    },
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def bitstring_to_array(bitstring: str) -> np.ndarray:
    return np.fromiter((char == "1" for char in bitstring), dtype=np.bool_)


def observable_int(bitstring: str) -> int:
    if not bitstring:
        return 0
    return int(bitstring, 2)


def build_base_matching(challenge: dict[str, Any]) -> pymatching.Matching:
    circuit = inject_tick_noise(
        base_circuit(
            distance=int(challenge["candidate_distance"]),
            physical_error=float(challenge["physical_error"]),
            basis=str(challenge["memory_basis"]),
        ),
        mode="heralded_erasure_proxy",
        leakage_rate=float(challenge["effective_erasure_rate_per_tick"]),
    )
    dem = circuit.detector_error_model(decompose_errors=True, approximate_disjoint_errors=True)
    return pymatching.Matching.from_detector_error_model(dem)


def max_incident_posterior(
    node1: int,
    node2: int | None,
    flagged_posteriors: dict[int, float],
) -> float:
    values = []
    if node1 in flagged_posteriors:
        values.append(flagged_posteriors[node1])
    if node2 is not None and node2 in flagged_posteriors:
        values.append(flagged_posteriors[node2])
    return max(values) if values else 0.0


def reweighted_matching(
    base_edges: list[tuple[int, int | None, dict[str, Any]]],
    flagged_posteriors: dict[int, float],
    alpha: float,
    min_weight: float,
) -> pymatching.Matching:
    matching = pymatching.Matching()
    for node1, node2, data in base_edges:
        posterior = max_incident_posterior(node1, node2, flagged_posteriors)
        base_weight = float(data.get("weight", 1.0))
        if posterior > 0:
            adjusted_weight = max(min_weight, base_weight * (1.0 - alpha * posterior))
        else:
            adjusted_weight = base_weight
        fault_ids = set(data.get("fault_ids", set()))
        error_probability = data.get("error_probability")
        if node2 is None:
            matching.add_boundary_edge(
                node1,
                fault_ids=fault_ids,
                weight=adjusted_weight,
                error_probability=error_probability,
            )
        else:
            matching.add_edge(
                node1,
                node2,
                fault_ids=fault_ids,
                weight=adjusted_weight,
                error_probability=error_probability,
            )
    return matching


def decode_prediction_int(prediction: np.ndarray) -> int:
    if len(prediction) == 0:
        return 0
    return int("".join("1" if bool(bit) else "0" for bit in prediction), 2)


def evaluate_profile(
    packet: dict[str, Any],
    base_edges: list[tuple[int, int | None, dict[str, Any]]],
    profile: dict[str, Any],
) -> dict[str, Any]:
    started = time.perf_counter()
    baseline_failures = 0
    injected_failures = 0
    changed_predictions = 0
    fixed_failures = 0
    introduced_failures = 0
    flagged_shots = 0
    total_flag_events = 0
    total_adjusted_edges = 0
    shot_rows = []
    cache: dict[tuple[tuple[tuple[int, float], ...], float, float], pymatching.Matching] = {}

    for trace in packet["shot_traces"]:
        detector_events = bitstring_to_array(trace["detector_bitstring"])
        observable = observable_int(trace["observable_bitstring"])
        baseline_prediction = observable_int(trace["predicted_observable_bitstring"])
        baseline_failed = bool(trace["logical_failure"])
        baseline_failures += int(baseline_failed)

        flagged_posteriors = {
            int(event["detector_id"]): float(event["posterior_leakage_probability_given_flag"])
            for event in trace.get("synthetic_flag_events", [])
        }
        if flagged_posteriors:
            flagged_shots += 1
        total_flag_events += len(flagged_posteriors)
        cache_key = (
            tuple(sorted(flagged_posteriors.items())),
            float(profile["alpha"]),
            float(profile["min_weight"]),
        )
        if cache_key not in cache:
            cache[cache_key] = reweighted_matching(
                base_edges=base_edges,
                flagged_posteriors=flagged_posteriors,
                alpha=float(profile["alpha"]),
                min_weight=float(profile["min_weight"]),
            )
        injected_matching = cache[cache_key]
        injected_prediction = decode_prediction_int(injected_matching.decode(detector_events))
        injected_failed = injected_prediction != observable
        injected_failures += int(injected_failed)
        prediction_changed = injected_prediction != baseline_prediction
        changed_predictions += int(prediction_changed)
        fixed = baseline_failed and not injected_failed
        introduced = (not baseline_failed) and injected_failed
        fixed_failures += int(fixed)
        introduced_failures += int(introduced)
        adjusted_edges = sum(
            1
            for node1, node2, _data in base_edges
            if max_incident_posterior(node1, node2, flagged_posteriors) > 0
        )
        total_adjusted_edges += adjusted_edges
        shot_rows.append(
            {
                "shot_index": trace["shot_index"],
                "flag_event_count": len(flagged_posteriors),
                "adjusted_edge_count": adjusted_edges,
                "baseline_prediction": baseline_prediction,
                "injected_prediction": injected_prediction,
                "observable": observable,
                "baseline_failed": baseline_failed,
                "injected_failed": injected_failed,
                "prediction_changed": prediction_changed,
                "fixed_failure": fixed,
                "introduced_failure": introduced,
            }
        )

    shots = len(packet["shot_traces"])
    _base_low, base_high = wilson_interval(baseline_failures, shots)
    _inj_low, injected_high = wilson_interval(injected_failures, shots)
    decode_seconds = time.perf_counter() - started
    return {
        "challenge_id": packet["challenge"]["challenge_id"],
        "profile": profile["name"],
        "alpha": profile["alpha"],
        "min_weight": profile["min_weight"],
        "claim_level": profile["claim_level"],
        "shots": shots,
        "baseline_failures": baseline_failures,
        "injected_failures": injected_failures,
        "failure_delta": injected_failures - baseline_failures,
        "baseline_wilson_95_high": base_high,
        "injected_wilson_95_high": injected_high,
        "wilson_high_delta": injected_high - base_high,
        "changed_predictions": changed_predictions,
        "fixed_failures": fixed_failures,
        "introduced_failures": introduced_failures,
        "flagged_shots": flagged_shots,
        "total_flag_events": total_flag_events,
        "mean_adjusted_edges_per_shot": total_adjusted_edges / shots if shots else 0.0,
        "decode_seconds": decode_seconds,
        "decode_seconds_per_shot": decode_seconds / shots if shots else 0.0,
        "shot_rows": shot_rows,
    }


def summarize(profile_results: list[dict[str, Any]]) -> dict[str, Any]:
    baseline_total = sum(row["baseline_failures"] for row in profile_results)
    injected_total = sum(row["injected_failures"] for row in profile_results)
    shots_total = sum(row["shots"] for row in profile_results)
    by_profile: dict[str, dict[str, Any]] = {}
    for profile in sorted({row["profile"] for row in profile_results}):
        subset = [row for row in profile_results if row["profile"] == profile]
        profile_baseline = sum(row["baseline_failures"] for row in subset)
        profile_injected = sum(row["injected_failures"] for row in subset)
        by_profile[profile] = {
            "challenge_count": len(subset),
            "shots": sum(row["shots"] for row in subset),
            "baseline_failures": profile_baseline,
            "injected_failures": profile_injected,
            "failure_delta": profile_injected - profile_baseline,
            "fixed_failures": sum(row["fixed_failures"] for row in subset),
            "introduced_failures": sum(row["introduced_failures"] for row in subset),
            "changed_predictions": sum(row["changed_predictions"] for row in subset),
            "mean_adjusted_edges_per_shot": (
                sum(row["mean_adjusted_edges_per_shot"] * row["shots"] for row in subset)
                / sum(row["shots"] for row in subset)
            ),
            "max_decode_seconds_per_shot": max(row["decode_seconds_per_shot"] for row in subset),
        }
    best_profile = min(
        by_profile.items(),
        key=lambda item: (item[1]["injected_failures"], item[1]["introduced_failures"]),
    )[0]
    best = by_profile[best_profile]
    improvement_gate_passed = (
        best["injected_failures"] < best["baseline_failures"]
        and best["introduced_failures"] == 0
    )
    robustness_gate_passed = all(
        row["injected_failures"] <= row["baseline_failures"]
        for row in profile_results
        if row["profile"] == best_profile
    )
    return {
        "source_challenge_count": len({row["challenge_id"] for row in profile_results}),
        "injection_profile_count": len(by_profile),
        "profile_result_count": len(profile_results),
        "total_profile_shots": shots_total,
        "baseline_total_failures": baseline_total,
        "best_profile": best_profile,
        "best_profile_injected_failures": best["injected_failures"],
        "best_profile_failure_delta": best["failure_delta"],
        "best_profile_fixed_failures": best["fixed_failures"],
        "best_profile_introduced_failures": best["introduced_failures"],
        "best_profile_changed_predictions": best["changed_predictions"],
        "posterior_likelihood_injection_performed": True,
        "synthetic_flag_likelihoods_consumed": True,
        "calibrated_flag_data_used": False,
        "real_hardware_trace_used": False,
        "production_decoder_claimed": False,
        "threshold_claimed": False,
        "new_code_claimed": False,
        "improvement_gate_passed": improvement_gate_passed,
        "all_challenge_nonregression_gate_passed": robustness_gate_passed,
        "route_demotion_recommended": not (improvement_gate_passed and robustness_gate_passed),
        "by_profile": by_profile,
    }


def validate(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    summary = report["summary"]
    claims = report["claim_boundary"]
    if summary["source_challenge_count"] != 3:
        errors.append("expected three source challenge rows")
    if summary["injection_profile_count"] != 3:
        errors.append("expected three injection profiles")
    if summary["total_profile_shots"] != 1728:
        errors.append("expected 1728 total profile shots")
    if summary["posterior_likelihood_injection_performed"] is not True:
        errors.append("posterior likelihood injection must be performed")
    if summary["synthetic_flag_likelihoods_consumed"] is not True:
        errors.append("synthetic flag likelihoods must be consumed")
    if summary["calibrated_flag_data_used"] is not False:
        errors.append("calibrated flag data must remain false")
    if summary["real_hardware_trace_used"] is not False:
        errors.append("real hardware trace must remain false")
    if summary["route_demotion_recommended"] is not True:
        errors.append("route should stay demoted unless improvement and robustness gates pass")
    if len(report.get("profile_results", [])) != summary["profile_result_count"]:
        errors.append("profile result count mismatch")
    for key in [
        "circuit_level_decoder_claimed",
        "production_decoder_claimed",
        "threshold_claimed",
        "new_code_claimed",
        "hardware_result_claimed",
        "calibrated_device_claimed",
        "quantum_advantage_claimed",
    ]:
        if claims.get(key) is not False:
            errors.append(f"{key} must remain False")
    if claims.get("posterior_likelihood_injection_interface_built") is not True:
        errors.append("claim boundary must disclose injection interface construction")
    return errors


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    source = load_json(args.source_result)
    profile_results: list[dict[str, Any]] = []
    for packet in source["challenge_packets"]:
        base_matching = build_base_matching(packet["challenge"])
        base_edges = base_matching.edges()
        for profile in INJECTION_PROFILES:
            profile_results.append(evaluate_profile(packet, base_edges, profile))
    summary = summarize(profile_results)
    report = {
        "benchmark_id": "B2",
        "problem_id": 22,
        "title": "B2 posterior-likelihood decoder injection gate",
        "version": VERSION,
        "last_updated": args.last_updated,
        "status": STATUS,
        "method": METHOD,
        "model_status": MODEL_STATUS,
        "toolchain": (
            "PyMatching edge-weight reconstruction from T-B2-009a per-shot detector traces; "
            "synthetic flag posteriors lower incident edge weights per shot"
        ),
        "source_result": str(args.source_result),
        "injection_profiles": INJECTION_PROFILES,
        "summary": summary,
        "claim_boundary": {
            "posterior_likelihood_injection_interface_built": True,
            "posterior_likelihood_injection_performed": True,
            "synthetic_flag_likelihoods_consumed": True,
            "real_flag_events_claimed": False,
            "circuit_level_decoder_claimed": False,
            "production_decoder_claimed": False,
            "threshold_claimed": False,
            "new_code_claimed": False,
            "hardware_result_claimed": False,
            "calibrated_device_claimed": False,
            "quantum_advantage_claimed": False,
            "what_is_supported": (
                "The persisted T-B2-009a detector traces can be consumed by a reproducible "
                "PyMatching edge-weight injection interface using declared synthetic flag posteriors."
            ),
            "what_is_not_supported": (
                "The injection is not calibrated, not hardware-derived, not a production "
                "shot-conditioned decoder, and it does not pass the improvement plus non-regression gate."
            ),
        },
        "profile_results": profile_results,
    }
    report["validation_errors"] = validate(report)
    return report


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# B2 Posterior-Likelihood Decoder Injection Gate v0.1",
        "",
        f"Status: **{report['status']}**",
        "",
        "## Summary",
        "",
        f"- Method: {report['method']}",
        f"- Model status: {report['model_status']}",
        f"- Source result: {report['source_result']}",
        f"- Source challenge count: {summary['source_challenge_count']}",
        f"- Injection profiles: {summary['injection_profile_count']}",
        f"- Total profile shots: {summary['total_profile_shots']}",
        f"- Baseline total failures across profiles: {summary['baseline_total_failures']}",
        f"- Best profile: {summary['best_profile']}",
        f"- Best profile injected failures: {summary['best_profile_injected_failures']}",
        f"- Best profile failure delta: {summary['best_profile_failure_delta']}",
        f"- Best profile fixed / introduced failures: {summary['best_profile_fixed_failures']} / {summary['best_profile_introduced_failures']}",
        f"- Best profile changed predictions: {summary['best_profile_changed_predictions']}",
        f"- Improvement gate passed: {summary['improvement_gate_passed']}",
        f"- All-challenge non-regression gate passed: {summary['all_challenge_nonregression_gate_passed']}",
        f"- Route demotion recommended: {summary['route_demotion_recommended']}",
        f"- Calibrated flag data used: {summary['calibrated_flag_data_used']}",
        f"- Real hardware trace used: {summary['real_hardware_trace_used']}",
        f"- Validation errors: {report['validation_errors']}",
        "",
        "## Profile Results",
        "",
        "| profile | shots | baseline failures | injected failures | delta | fixed | introduced | changed predictions | mean adjusted edges/shot | max decode s/shot |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for profile, row in summary["by_profile"].items():
        lines.append(
            f"| {profile} | {row['shots']} | {row['baseline_failures']} | "
            f"{row['injected_failures']} | {row['failure_delta']} | "
            f"{row['fixed_failures']} | {row['introduced_failures']} | "
            f"{row['changed_predictions']} | {row['mean_adjusted_edges_per_shot']:.6g} | "
            f"{row['max_decode_seconds_per_shot']:.6g} |"
        )
    lines.extend(["", "## Challenge/Profile Detail", ""])
    lines.extend(
        [
            "| challenge | profile | shots | baseline failures | injected failures | delta | fixed | introduced | changed |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in report["profile_results"]:
        lines.append(
            f"| {row['challenge_id']} | {row['profile']} | {row['shots']} | "
            f"{row['baseline_failures']} | {row['injected_failures']} | "
            f"{row['failure_delta']} | {row['fixed_failures']} | "
            f"{row['introduced_failures']} | {row['changed_predictions']} |"
        )
    lines.extend(["", "## Claim Boundary", ""])
    for key, value in report["claim_boundary"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Next Gate",
            "",
            "This interface must be replaced or strengthened with detector-to-edge semantics",
            "derived from calibrated leakage events, not synthetic detector flags. B2 should",
            "stay demoted until injected decoding improves strict challenge rows without",
            "introducing new failures and survives all-profile robustness pressure.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-result",
        type=Path,
        default=Path("results/B2_per_shot_decoder_trace_packet_v0.json"),
    )
    parser.add_argument("--last-updated", default="2026-06-18")
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B2_posterior_likelihood_decoder_injection_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B2_posterior_likelihood_decoder_injection_gate.md"),
    )
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    report = build_report(args)
    write_json(args.json_output, report)
    write_markdown(report, args.markdown_output)
    print(
        json.dumps(
            {
                "status": report["status"],
                "method": report["method"],
                **report["summary"],
                "validation_errors": report["validation_errors"],
            },
            indent=2 if args.pretty else None,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
