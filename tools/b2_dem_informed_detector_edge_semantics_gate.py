#!/usr/bin/env python3
"""Evaluate DEM-informed detector-to-edge posterior semantics for B2."""

from __future__ import annotations

import argparse
import json
import math
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pymatching

from b2_posterior_likelihood_decoder_injection_gate import (
    bitstring_to_array,
    build_base_matching,
    decode_prediction_int,
    observable_int,
)


METHOD = "b2_dem_informed_detector_edge_semantics_gate_v0"
STATUS = "dem_informed_detector_edge_semantics_negative_boundary"
MODEL_STATUS = "stim_dem_edge_probability_semantics_with_synthetic_flags_not_calibrated_data"
VERSION = "0.1"


SEMANTIC_PROFILES = [
    {
        "name": "conservative_dem_responsibility",
        "beta": 0.25,
        "max_edge_probability": 0.35,
        "claim_level": "dem_semantics_sensitivity",
    },
    {
        "name": "nominal_dem_responsibility",
        "beta": 0.50,
        "max_edge_probability": 0.45,
        "claim_level": "dem_semantics_sensitivity",
    },
    {
        "name": "aggressive_dem_responsibility",
        "beta": 0.90,
        "max_edge_probability": 0.55,
        "claim_level": "stress_only",
    },
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def probability_to_weight(probability: float) -> float:
    probability = min(max(probability, 1e-9), 1.0 - 1e-9)
    return math.log((1.0 - probability) / probability)


def edge_key(node1: int, node2: int | None, index: int) -> tuple[int, int | None, int]:
    return (int(node1), None if node2 is None else int(node2), int(index))


def build_incidence(
    base_edges: list[tuple[int, int | None, dict[str, Any]]],
) -> dict[int, list[tuple[int, int | None, int, float]]]:
    incidence: dict[int, list[tuple[int, int | None, int, float]]] = defaultdict(list)
    for index, (node1, node2, data) in enumerate(base_edges):
        probability = float(data.get("error_probability") or 0.0)
        incidence[int(node1)].append((int(node1), node2, index, probability))
        if node2 is not None:
            incidence[int(node2)].append((int(node1), node2, index, probability))
    return incidence


def dem_informed_edge_probabilities(
    base_edges: list[tuple[int, int | None, dict[str, Any]]],
    incidence: dict[int, list[tuple[int, int | None, int, float]]],
    flagged_posteriors: dict[int, float],
    beta: float,
    max_edge_probability: float,
) -> tuple[dict[int, float], int]:
    edge_extra_fail_probabilities: dict[int, list[float]] = defaultdict(list)
    for detector_id, posterior in flagged_posteriors.items():
        incident = incidence.get(detector_id, [])
        if not incident:
            continue
        denominator = sum(max(prob, 1e-12) for *_nodes, prob in incident)
        for _node1, _node2, edge_index, base_probability in incident:
            responsibility = max(base_probability, 1e-12) / denominator
            edge_extra_fail_probabilities[edge_index].append(beta * posterior * responsibility)

    adjusted: dict[int, float] = {}
    for edge_index, extras in edge_extra_fail_probabilities.items():
        base_probability = float(base_edges[edge_index][2].get("error_probability") or 0.0)
        no_extra_survival = 1.0
        for extra in extras:
            no_extra_survival *= 1.0 - min(max(extra, 0.0), 1.0)
        extra_probability = 1.0 - no_extra_survival
        adjusted_probability = base_probability + (1.0 - base_probability) * extra_probability
        adjusted[edge_index] = min(max_edge_probability, max(base_probability, adjusted_probability))
    return adjusted, len(adjusted)


def rebuild_matching_with_probabilities(
    base_edges: list[tuple[int, int | None, dict[str, Any]]],
    adjusted_probabilities: dict[int, float],
) -> pymatching.Matching:
    matching = pymatching.Matching()
    for index, (node1, node2, data) in enumerate(base_edges):
        probability = adjusted_probabilities.get(
            index,
            float(data.get("error_probability") or 1.0 / (1.0 + math.exp(float(data.get("weight", 1.0))))),
        )
        weight = probability_to_weight(probability)
        fault_ids = set(data.get("fault_ids", set()))
        if node2 is None:
            matching.add_boundary_edge(
                int(node1),
                fault_ids=fault_ids,
                weight=weight,
                error_probability=probability,
            )
        else:
            matching.add_edge(
                int(node1),
                int(node2),
                fault_ids=fault_ids,
                weight=weight,
                error_probability=probability,
            )
    return matching


def evaluate_profile(
    packet: dict[str, Any],
    base_edges: list[tuple[int, int | None, dict[str, Any]]],
    incidence: dict[int, list[tuple[int, int | None, int, float]]],
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
    max_adjusted_edge_probability = 0.0
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
            float(profile["beta"]),
            float(profile["max_edge_probability"]),
        )
        adjusted_probabilities, adjusted_edge_count = dem_informed_edge_probabilities(
            base_edges=base_edges,
            incidence=incidence,
            flagged_posteriors=flagged_posteriors,
            beta=float(profile["beta"]),
            max_edge_probability=float(profile["max_edge_probability"]),
        )
        if adjusted_probabilities:
            max_adjusted_edge_probability = max(
                max_adjusted_edge_probability,
                max(adjusted_probabilities.values()),
            )
        total_adjusted_edges += adjusted_edge_count
        if cache_key not in cache:
            cache[cache_key] = rebuild_matching_with_probabilities(
                base_edges=base_edges,
                adjusted_probabilities=adjusted_probabilities,
            )
        injected_prediction = decode_prediction_int(cache[cache_key].decode(detector_events))
        injected_failed = injected_prediction != observable
        injected_failures += int(injected_failed)
        changed = injected_prediction != baseline_prediction
        changed_predictions += int(changed)
        fixed_failures += int(baseline_failed and not injected_failed)
        introduced_failures += int((not baseline_failed) and injected_failed)

    shots = len(packet["shot_traces"])
    _base_low, base_high = wilson_interval_safe(baseline_failures, shots)
    _inj_low, injected_high = wilson_interval_safe(injected_failures, shots)
    seconds = time.perf_counter() - started
    return {
        "challenge_id": packet["challenge"]["challenge_id"],
        "profile": profile["name"],
        "beta": profile["beta"],
        "max_edge_probability": profile["max_edge_probability"],
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
        "max_adjusted_edge_probability": max_adjusted_edge_probability,
        "decode_seconds": seconds,
        "decode_seconds_per_shot": seconds / shots if shots else 0.0,
    }


def wilson_interval_safe(failures: int, shots: int, z: float = 1.96) -> tuple[float, float]:
    if shots <= 0:
        return 0.0, 0.0
    phat = failures / shots
    denom = 1 + z**2 / shots
    center = (phat + z**2 / (2 * shots)) / denom
    half = z * math.sqrt((phat * (1 - phat) + z**2 / (4 * shots)) / shots) / denom
    return max(0.0, center - half), min(1.0, center + half)


def summarize(profile_results: list[dict[str, Any]]) -> dict[str, Any]:
    by_profile: dict[str, dict[str, Any]] = {}
    for profile in sorted({row["profile"] for row in profile_results}):
        subset = [row for row in profile_results if row["profile"] == profile]
        baseline = sum(row["baseline_failures"] for row in subset)
        injected = sum(row["injected_failures"] for row in subset)
        shots = sum(row["shots"] for row in subset)
        by_profile[profile] = {
            "challenge_count": len(subset),
            "shots": shots,
            "baseline_failures": baseline,
            "injected_failures": injected,
            "failure_delta": injected - baseline,
            "fixed_failures": sum(row["fixed_failures"] for row in subset),
            "introduced_failures": sum(row["introduced_failures"] for row in subset),
            "changed_predictions": sum(row["changed_predictions"] for row in subset),
            "mean_adjusted_edges_per_shot": (
                sum(row["mean_adjusted_edges_per_shot"] * row["shots"] for row in subset) / shots
                if shots
                else 0.0
            ),
            "max_adjusted_edge_probability": max(
                row["max_adjusted_edge_probability"] for row in subset
            ),
            "max_decode_seconds_per_shot": max(row["decode_seconds_per_shot"] for row in subset),
        }
    best_profile = min(
        by_profile.items(),
        key=lambda item: (item[1]["injected_failures"], item[1]["introduced_failures"]),
    )[0]
    best = by_profile[best_profile]
    improvement_gate_passed = best["injected_failures"] < best["baseline_failures"]
    nonregression_gate_passed = all(
        row["injected_failures"] <= row["baseline_failures"]
        for row in profile_results
        if row["profile"] == best_profile
    )
    return {
        "source_challenge_count": len({row["challenge_id"] for row in profile_results}),
        "semantic_profile_count": len(by_profile),
        "profile_result_count": len(profile_results),
        "total_profile_shots": sum(row["shots"] for row in profile_results),
        "baseline_total_failures": sum(row["baseline_failures"] for row in profile_results),
        "best_profile": best_profile,
        "best_profile_injected_failures": best["injected_failures"],
        "best_profile_failure_delta": best["failure_delta"],
        "best_profile_fixed_failures": best["fixed_failures"],
        "best_profile_introduced_failures": best["introduced_failures"],
        "best_profile_changed_predictions": best["changed_predictions"],
        "best_profile_max_adjusted_edge_probability": best["max_adjusted_edge_probability"],
        "dem_edge_probability_semantics_performed": True,
        "synthetic_flag_likelihoods_consumed": True,
        "calibrated_flag_data_used": False,
        "real_hardware_trace_used": False,
        "improvement_gate_passed": improvement_gate_passed,
        "all_challenge_nonregression_gate_passed": nonregression_gate_passed,
        "route_demotion_recommended": not (improvement_gate_passed and nonregression_gate_passed),
        "by_profile": by_profile,
    }


def validate(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    summary = report["summary"]
    claims = report["claim_boundary"]
    if summary["source_challenge_count"] != 3:
        errors.append("expected three source challenge rows")
    if summary["semantic_profile_count"] != 3:
        errors.append("expected three semantic profiles")
    if summary["total_profile_shots"] != 1728:
        errors.append("expected 1728 total profile shots")
    if summary["dem_edge_probability_semantics_performed"] is not True:
        errors.append("DEM-informed edge semantics must be performed")
    if summary["synthetic_flag_likelihoods_consumed"] is not True:
        errors.append("synthetic flag likelihoods must be consumed")
    if summary["calibrated_flag_data_used"] is not False:
        errors.append("calibrated flag data must remain false")
    if summary["real_hardware_trace_used"] is not False:
        errors.append("real hardware trace must remain false")
    if summary["route_demotion_recommended"] is not True:
        errors.append("route should remain demoted unless improvement and non-regression pass")
    for key in [
        "production_decoder_claimed",
        "threshold_claimed",
        "new_code_claimed",
        "hardware_result_claimed",
        "calibrated_device_claimed",
        "quantum_advantage_claimed",
    ]:
        if claims.get(key) is not False:
            errors.append(f"{key} must remain False")
    if claims.get("dem_edge_probability_semantics_built") is not True:
        errors.append("claim boundary must disclose DEM edge-probability semantics")
    return errors


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    source = load_json(args.source_result)
    profile_results: list[dict[str, Any]] = []
    for packet in source["challenge_packets"]:
        matching = build_base_matching(packet["challenge"])
        base_edges = matching.edges()
        incidence = build_incidence(base_edges)
        for profile in SEMANTIC_PROFILES:
            profile_results.append(evaluate_profile(packet, base_edges, incidence, profile))
    summary = summarize(profile_results)
    report = {
        "benchmark_id": "B2",
        "problem_id": 22,
        "title": "B2 DEM-informed detector-to-edge semantics gate",
        "version": VERSION,
        "last_updated": args.last_updated,
        "status": STATUS,
        "method": METHOD,
        "model_status": MODEL_STATUS,
        "toolchain": (
            "Stim detector error model edge probabilities plus PyMatching graph "
            "reconstruction; synthetic flag posteriors are allocated to incident "
            "edges by DEM base error probability responsibility"
        ),
        "source_result": str(args.source_result),
        "semantic_profiles": SEMANTIC_PROFILES,
        "summary": summary,
        "claim_boundary": {
            "dem_edge_probability_semantics_built": True,
            "dem_edge_probability_semantics_performed": True,
            "synthetic_flag_likelihoods_consumed": True,
            "real_flag_events_claimed": False,
            "production_decoder_claimed": False,
            "threshold_claimed": False,
            "new_code_claimed": False,
            "hardware_result_claimed": False,
            "calibrated_device_claimed": False,
            "quantum_advantage_claimed": False,
            "what_is_supported": (
                "The B2 injection interface now uses DEM edge probabilities to map "
                "flagged detector posteriors onto incident decoder edges instead of a "
                "flat neighboring-edge shift."
            ),
            "what_is_not_supported": (
                "The flag events remain synthetic and uncalibrated; this is not a "
                "production decoder, threshold result, hardware result, or new code."
            ),
        },
        "profile_results": profile_results,
    }
    report["validation_errors"] = validate(report)
    return report


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# B2 DEM-Informed Detector-To-Edge Semantics Gate v0.1",
        "",
        f"Status: **{report['status']}**",
        "",
        "## Summary",
        "",
        f"- Method: {report['method']}",
        f"- Model status: {report['model_status']}",
        f"- Source result: {report['source_result']}",
        f"- Source challenge count: {summary['source_challenge_count']}",
        f"- Semantic profiles: {summary['semantic_profile_count']}",
        f"- Total profile shots: {summary['total_profile_shots']}",
        f"- Baseline total failures across profiles: {summary['baseline_total_failures']}",
        f"- Best profile: {summary['best_profile']}",
        f"- Best profile injected failures: {summary['best_profile_injected_failures']}",
        f"- Best profile failure delta: {summary['best_profile_failure_delta']}",
        f"- Best profile fixed / introduced failures: {summary['best_profile_fixed_failures']} / {summary['best_profile_introduced_failures']}",
        f"- Best profile changed predictions: {summary['best_profile_changed_predictions']}",
        f"- Best profile max adjusted edge probability: {summary['best_profile_max_adjusted_edge_probability']:.6g}",
        f"- Improvement gate passed: {summary['improvement_gate_passed']}",
        f"- All-challenge non-regression gate passed: {summary['all_challenge_nonregression_gate_passed']}",
        f"- Route demotion recommended: {summary['route_demotion_recommended']}",
        f"- Calibrated flag data used: {summary['calibrated_flag_data_used']}",
        f"- Real hardware trace used: {summary['real_hardware_trace_used']}",
        f"- Validation errors: {report['validation_errors']}",
        "",
        "## Profile Results",
        "",
        "| profile | shots | baseline failures | injected failures | delta | fixed | introduced | changed predictions | mean adjusted edges/shot | max adjusted p(edge) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for profile, row in summary["by_profile"].items():
        lines.append(
            f"| {profile} | {row['shots']} | {row['baseline_failures']} | "
            f"{row['injected_failures']} | {row['failure_delta']} | "
            f"{row['fixed_failures']} | {row['introduced_failures']} | "
            f"{row['changed_predictions']} | {row['mean_adjusted_edges_per_shot']:.6g} | "
            f"{row['max_adjusted_edge_probability']:.6g} |"
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
            "The next gate still requires calibrated leakage/flag observations or a",
            "hardware-like leakage model. This DEM-informed semantic layer is only a",
            "decoder-interface pressure test over synthetic flags.",
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
        default=Path("results/B2_dem_informed_detector_edge_semantics_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B2_dem_informed_detector_edge_semantics_gate.md"),
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
