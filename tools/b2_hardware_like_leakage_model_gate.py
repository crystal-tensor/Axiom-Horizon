#!/usr/bin/env python3
"""Stress B2 posterior decoding with a hardware-like leakage observation model."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from b2_dem_informed_detector_edge_semantics_gate import (
    build_incidence,
    dem_informed_edge_probabilities,
    rebuild_matching_with_probabilities,
    wilson_interval_safe,
)
from b2_posterior_likelihood_decoder_injection_gate import (
    bitstring_to_array,
    build_base_matching,
    decode_prediction_int,
    observable_int,
)


METHOD = "b2_hardware_like_leakage_model_gate_v0"
STATUS = "hardware_like_leakage_model_negative_boundary"
MODEL_STATUS = "hardware_like_leakage_observation_model_not_calibrated_not_hardware"
VERSION = "0.1"


OBSERVATION_PROFILES = [
    {
        "name": "conservative_hardware_like_leakage",
        "detector_event_multiplier": 0.55,
        "false_positive_multiplier": 0.25,
        "beta": 0.20,
        "max_edge_probability": 0.35,
        "claim_level": "hardware_like_model_sensitivity",
    },
    {
        "name": "nominal_hardware_like_leakage",
        "detector_event_multiplier": 0.85,
        "false_positive_multiplier": 0.50,
        "beta": 0.45,
        "max_edge_probability": 0.45,
        "claim_level": "hardware_like_model_sensitivity",
    },
    {
        "name": "stress_hardware_like_leakage",
        "detector_event_multiplier": 1.20,
        "false_positive_multiplier": 1.00,
        "beta": 0.75,
        "max_edge_probability": 0.55,
        "claim_level": "stress_only",
    },
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def stable_unit_interval(*parts: object) -> float:
    material = "|".join(str(part) for part in parts).encode("utf-8")
    digest = hashlib.sha256(material).hexdigest()
    return int(digest[:16], 16) / float(16**16 - 1)


def detector_hotspot_factor(detector_id: int, shot_index: int) -> float:
    factor = 1.0
    if detector_id % 7 == 0:
        factor += 0.35
    if (detector_id + shot_index) % 11 == 0:
        factor += 0.25
    if detector_id % 17 == 0:
        factor += 0.15
    return factor


def model_posterior(
    challenge: dict[str, Any],
    profile: dict[str, Any],
    detector_id: int,
    shot_index: int,
    detector_event: bool,
) -> float:
    hotspot = detector_hotspot_factor(detector_id, shot_index)
    leakage_prior = min(
        0.25,
        float(challenge["leakage_rate_per_tick"])
        * float(profile["detector_event_multiplier"])
        * hotspot,
    )
    sensitivity = min(0.95, 0.52 + 0.18 * float(profile["detector_event_multiplier"]))
    false_positive = min(
        0.20,
        float(challenge["false_positive_rate_per_tick"])
        * float(profile["false_positive_multiplier"])
        * hotspot
        + 1e-6,
    )
    if detector_event:
        numerator = sensitivity * leakage_prior
        denominator = numerator + false_positive * (1.0 - leakage_prior)
    else:
        numerator = 0.18 * sensitivity * leakage_prior
        denominator = numerator + 3.0 * false_positive * (1.0 - leakage_prior)
    if denominator <= 0:
        return 0.0
    return min(0.97, max(0.02, numerator / denominator))


def generate_hardware_like_observations(
    challenge: dict[str, Any],
    profile: dict[str, Any],
    trace: dict[str, Any],
    detector_events: list[bool],
) -> dict[int, float]:
    observations: dict[int, float] = {}
    challenge_id = challenge["challenge_id"]
    shot_index = int(trace["shot_index"])
    effective_erasure = float(challenge["effective_erasure_rate_per_tick"])
    false_positive = float(challenge["false_positive_rate_per_tick"])
    for detector_id, detector_event in enumerate(detector_events):
        hotspot = detector_hotspot_factor(detector_id, shot_index)
        if detector_event:
            flag_probability = min(
                0.90,
                0.035
                + 8.0
                * effective_erasure
                * float(profile["detector_event_multiplier"])
                * hotspot,
            )
        else:
            flag_probability = min(
                0.25,
                1.5
                * false_positive
                * float(profile["false_positive_multiplier"])
                * hotspot,
            )
        draw = stable_unit_interval(profile["name"], challenge_id, shot_index, detector_id)
        if draw < flag_probability:
            observations[detector_id] = model_posterior(
                challenge=challenge,
                profile=profile,
                detector_id=detector_id,
                shot_index=shot_index,
                detector_event=bool(detector_event),
            )
    return observations


def evaluate_profile(
    packet: dict[str, Any],
    base_edges: list[tuple[int, int | None, dict[str, Any]]],
    incidence: dict[int, list[tuple[int, int | None, int, float]]],
    profile: dict[str, Any],
) -> dict[str, Any]:
    started = time.perf_counter()
    partitions: dict[str, dict[str, Any]] = {
        "model_selection": defaultdict(int),
        "holdout": defaultdict(int),
    }
    max_adjusted_edge_probability = 0.0
    total_adjusted_edges = 0
    total_model_flag_events = 0
    flagged_shots = 0
    changed_predictions = 0
    fixed_failures = 0
    introduced_failures = 0
    baseline_failures = 0
    injected_failures = 0
    cache: dict[tuple[tuple[tuple[int, float], ...], float, float], Any] = {}

    for trace in packet["shot_traces"]:
        detector_array = bitstring_to_array(trace["detector_bitstring"])
        detector_events = [bool(value) for value in detector_array]
        observable = observable_int(trace["observable_bitstring"])
        baseline_prediction = observable_int(trace["predicted_observable_bitstring"])
        baseline_failed = bool(trace["logical_failure"])
        baseline_failures += int(baseline_failed)

        model_observations = generate_hardware_like_observations(
            challenge=packet["challenge"],
            profile=profile,
            trace=trace,
            detector_events=detector_events,
        )
        if model_observations:
            flagged_shots += 1
        total_model_flag_events += len(model_observations)

        adjusted_probabilities, adjusted_edge_count = dem_informed_edge_probabilities(
            base_edges=base_edges,
            incidence=incidence,
            flagged_posteriors=model_observations,
            beta=float(profile["beta"]),
            max_edge_probability=float(profile["max_edge_probability"]),
        )
        if adjusted_probabilities:
            max_adjusted_edge_probability = max(
                max_adjusted_edge_probability,
                max(adjusted_probabilities.values()),
            )
        total_adjusted_edges += adjusted_edge_count
        cache_key = (
            tuple(sorted(model_observations.items())),
            float(profile["beta"]),
            float(profile["max_edge_probability"]),
        )
        if cache_key not in cache:
            cache[cache_key] = rebuild_matching_with_probabilities(
                base_edges=base_edges,
                adjusted_probabilities=adjusted_probabilities,
            )
        injected_prediction = decode_prediction_int(cache[cache_key].decode(detector_array))
        injected_failed = injected_prediction != observable
        injected_failures += int(injected_failed)
        changed = injected_prediction != baseline_prediction
        fixed = baseline_failed and not injected_failed
        introduced = (not baseline_failed) and injected_failed
        changed_predictions += int(changed)
        fixed_failures += int(fixed)
        introduced_failures += int(introduced)

        partition = "model_selection" if int(trace["shot_index"]) % 2 == 0 else "holdout"
        partitions[partition]["shots"] += 1
        partitions[partition]["baseline_failures"] += int(baseline_failed)
        partitions[partition]["injected_failures"] += int(injected_failed)
        partitions[partition]["changed_predictions"] += int(changed)
        partitions[partition]["fixed_failures"] += int(fixed)
        partitions[partition]["introduced_failures"] += int(introduced)
        partitions[partition]["model_flag_events"] += len(model_observations)

    shots = len(packet["shot_traces"])
    for row in partitions.values():
        row["failure_delta"] = row["injected_failures"] - row["baseline_failures"]
    _base_low, base_high = wilson_interval_safe(baseline_failures, shots)
    _inj_low, injected_high = wilson_interval_safe(injected_failures, shots)
    seconds = time.perf_counter() - started
    return {
        "challenge_id": packet["challenge"]["challenge_id"],
        "profile": profile["name"],
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
        "model_flag_events": total_model_flag_events,
        "mean_model_flags_per_shot": total_model_flag_events / shots if shots else 0.0,
        "mean_adjusted_edges_per_shot": total_adjusted_edges / shots if shots else 0.0,
        "max_adjusted_edge_probability": max_adjusted_edge_probability,
        "partitions": {key: dict(value) for key, value in partitions.items()},
        "decode_seconds": seconds,
        "decode_seconds_per_shot": seconds / shots if shots else 0.0,
    }


def summarize(profile_results: list[dict[str, Any]]) -> dict[str, Any]:
    by_profile: dict[str, dict[str, Any]] = {}
    for profile in sorted({row["profile"] for row in profile_results}):
        subset = [row for row in profile_results if row["profile"] == profile]
        shots = sum(row["shots"] for row in subset)
        holdout_shots = sum(row["partitions"]["holdout"]["shots"] for row in subset)
        holdout_baseline = sum(row["partitions"]["holdout"]["baseline_failures"] for row in subset)
        holdout_injected = sum(row["partitions"]["holdout"]["injected_failures"] for row in subset)
        by_profile[profile] = {
            "challenge_count": len(subset),
            "shots": shots,
            "baseline_failures": sum(row["baseline_failures"] for row in subset),
            "injected_failures": sum(row["injected_failures"] for row in subset),
            "failure_delta": sum(row["failure_delta"] for row in subset),
            "fixed_failures": sum(row["fixed_failures"] for row in subset),
            "introduced_failures": sum(row["introduced_failures"] for row in subset),
            "changed_predictions": sum(row["changed_predictions"] for row in subset),
            "model_flag_events": sum(row["model_flag_events"] for row in subset),
            "mean_model_flags_per_shot": (
                sum(row["mean_model_flags_per_shot"] * row["shots"] for row in subset) / shots
                if shots
                else 0.0
            ),
            "mean_adjusted_edges_per_shot": (
                sum(row["mean_adjusted_edges_per_shot"] * row["shots"] for row in subset) / shots
                if shots
                else 0.0
            ),
            "max_adjusted_edge_probability": max(
                row["max_adjusted_edge_probability"] for row in subset
            ),
            "holdout_shots": holdout_shots,
            "holdout_baseline_failures": holdout_baseline,
            "holdout_injected_failures": holdout_injected,
            "holdout_failure_delta": holdout_injected - holdout_baseline,
            "holdout_fixed_failures": sum(
                row["partitions"]["holdout"]["fixed_failures"] for row in subset
            ),
            "holdout_introduced_failures": sum(
                row["partitions"]["holdout"]["introduced_failures"] for row in subset
            ),
            "holdout_changed_predictions": sum(
                row["partitions"]["holdout"]["changed_predictions"] for row in subset
            ),
        }
    best_profile = min(
        by_profile.items(),
        key=lambda item: (
            item[1]["holdout_injected_failures"],
            item[1]["holdout_introduced_failures"],
            item[1]["injected_failures"],
        ),
    )[0]
    best = by_profile[best_profile]
    holdout_improvement_gate_passed = (
        best["holdout_injected_failures"] < best["holdout_baseline_failures"]
    )
    holdout_nonregression_gate_passed = all(
        row["partitions"]["holdout"]["injected_failures"]
        <= row["partitions"]["holdout"]["baseline_failures"]
        for row in profile_results
        if row["profile"] == best_profile
    )
    calibrated_or_hardware = False
    return {
        "source_challenge_count": len({row["challenge_id"] for row in profile_results}),
        "observation_profile_count": len(by_profile),
        "profile_result_count": len(profile_results),
        "total_profile_shots": sum(row["shots"] for row in profile_results),
        "holdout_profile_shots": sum(
            row["partitions"]["holdout"]["shots"] for row in profile_results
        ),
        "baseline_total_failures": sum(row["baseline_failures"] for row in profile_results),
        "best_profile": best_profile,
        "best_profile_injected_failures": best["injected_failures"],
        "best_profile_failure_delta": best["failure_delta"],
        "best_profile_fixed_failures": best["fixed_failures"],
        "best_profile_introduced_failures": best["introduced_failures"],
        "best_profile_changed_predictions": best["changed_predictions"],
        "best_profile_model_flag_events": best["model_flag_events"],
        "best_profile_max_adjusted_edge_probability": best["max_adjusted_edge_probability"],
        "best_profile_holdout_baseline_failures": best["holdout_baseline_failures"],
        "best_profile_holdout_injected_failures": best["holdout_injected_failures"],
        "best_profile_holdout_failure_delta": best["holdout_failure_delta"],
        "best_profile_holdout_fixed_failures": best["holdout_fixed_failures"],
        "best_profile_holdout_introduced_failures": best["holdout_introduced_failures"],
        "best_profile_holdout_changed_predictions": best["holdout_changed_predictions"],
        "hardware_like_leakage_model_used": True,
        "detector_bitstrings_consumed": True,
        "synthetic_flag_fixture_consumed": False,
        "calibrated_flag_data_used": False,
        "real_hardware_trace_used": False,
        "holdout_improvement_gate_passed": holdout_improvement_gate_passed,
        "holdout_nonregression_gate_passed": holdout_nonregression_gate_passed,
        "route_demotion_recommended": not (
            calibrated_or_hardware
            and holdout_improvement_gate_passed
            and holdout_nonregression_gate_passed
        ),
        "by_profile": by_profile,
    }


def validate(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    summary = report["summary"]
    claims = report["claim_boundary"]
    if summary["source_challenge_count"] != 3:
        errors.append("expected three source challenge rows")
    if summary["observation_profile_count"] != 3:
        errors.append("expected three observation profiles")
    if summary["total_profile_shots"] != 1728:
        errors.append("expected 1728 total profile shots")
    if summary["holdout_profile_shots"] != 864:
        errors.append("expected 864 holdout profile shots")
    if summary["hardware_like_leakage_model_used"] is not True:
        errors.append("hardware-like leakage model must be used")
    if summary["detector_bitstrings_consumed"] is not True:
        errors.append("detector bitstrings must be consumed")
    if summary["synthetic_flag_fixture_consumed"] is not False:
        errors.append("synthetic flag fixture must not be consumed")
    if summary["calibrated_flag_data_used"] is not False:
        errors.append("calibrated flag data must remain false")
    if summary["real_hardware_trace_used"] is not False:
        errors.append("real hardware trace must remain false")
    if summary["route_demotion_recommended"] is not True:
        errors.append("route must remain demoted without calibrated or real-hardware evidence")
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
    if claims.get("hardware_like_leakage_model_built") is not True:
        errors.append("claim boundary must disclose hardware-like model construction")
    return errors


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    source = load_json(args.source_result)
    profile_results: list[dict[str, Any]] = []
    for packet in source["challenge_packets"]:
        matching = build_base_matching(packet["challenge"])
        base_edges = matching.edges()
        incidence = build_incidence(base_edges)
        for profile in OBSERVATION_PROFILES:
            profile_results.append(evaluate_profile(packet, base_edges, incidence, profile))
    summary = summarize(profile_results)
    report = {
        "benchmark_id": "B2",
        "problem_id": 22,
        "title": "B2 hardware-like leakage observation model gate",
        "version": VERSION,
        "last_updated": args.last_updated,
        "status": STATUS,
        "method": METHOD,
        "model_status": MODEL_STATUS,
        "toolchain": (
            "Detector-bitstring driven hardware-like leakage observation model; "
            "model-derived flag posteriors are mapped to incident Stim/PyMatching "
            "DEM edges and evaluated on even/odd shot partitions"
        ),
        "source_result": str(args.source_result),
        "observation_profiles": OBSERVATION_PROFILES,
        "summary": summary,
        "claim_boundary": {
            "hardware_like_leakage_model_built": True,
            "hardware_like_leakage_model_used": True,
            "detector_bitstrings_consumed": True,
            "synthetic_flag_fixture_consumed": False,
            "real_flag_events_claimed": False,
            "production_decoder_claimed": False,
            "threshold_claimed": False,
            "new_code_claimed": False,
            "hardware_result_claimed": False,
            "calibrated_device_claimed": False,
            "quantum_advantage_claimed": False,
            "what_is_supported": (
                "The decoder interface can consume a deterministic hardware-like "
                "leakage observation model derived from detector bitstrings and "
                "challenge-level leakage/false-positive parameters."
            ),
            "what_is_not_supported": (
                "The model is not fitted to real device observations and does not "
                "constitute calibrated leakage data, a hardware trace, a production "
                "decoder, a threshold result, or a new code."
            ),
        },
        "profile_results": profile_results,
    }
    report["validation_errors"] = validate(report)
    return report


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# B2 Hardware-Like Leakage Observation Model Gate v0.1",
        "",
        f"Status: **{report['status']}**",
        "",
        "## Summary",
        "",
        f"- Method: {report['method']}",
        f"- Model status: {report['model_status']}",
        f"- Source result: {report['source_result']}",
        f"- Source challenge count: {summary['source_challenge_count']}",
        f"- Observation profiles: {summary['observation_profile_count']}",
        f"- Total profile shots: {summary['total_profile_shots']}",
        f"- Holdout profile shots: {summary['holdout_profile_shots']}",
        f"- Baseline total failures across profiles: {summary['baseline_total_failures']}",
        f"- Best profile: {summary['best_profile']}",
        f"- Best profile injected failures: {summary['best_profile_injected_failures']}",
        f"- Best profile failure delta: {summary['best_profile_failure_delta']}",
        f"- Best profile fixed / introduced failures: {summary['best_profile_fixed_failures']} / {summary['best_profile_introduced_failures']}",
        f"- Best profile changed predictions: {summary['best_profile_changed_predictions']}",
        f"- Best profile model flag events: {summary['best_profile_model_flag_events']}",
        f"- Best profile max adjusted edge probability: {summary['best_profile_max_adjusted_edge_probability']:.6g}",
        f"- Best profile holdout injected failures: {summary['best_profile_holdout_injected_failures']}",
        f"- Best profile holdout failure delta: {summary['best_profile_holdout_failure_delta']}",
        f"- Best profile holdout fixed / introduced failures: {summary['best_profile_holdout_fixed_failures']} / {summary['best_profile_holdout_introduced_failures']}",
        f"- Holdout improvement gate passed: {summary['holdout_improvement_gate_passed']}",
        f"- Holdout non-regression gate passed: {summary['holdout_nonregression_gate_passed']}",
        f"- Route demotion recommended: {summary['route_demotion_recommended']}",
        f"- Synthetic flag fixture consumed: {summary['synthetic_flag_fixture_consumed']}",
        f"- Calibrated flag data used: {summary['calibrated_flag_data_used']}",
        f"- Real hardware trace used: {summary['real_hardware_trace_used']}",
        f"- Validation errors: {report['validation_errors']}",
        "",
        "## Profile Results",
        "",
        "| profile | shots | baseline failures | injected failures | delta | fixed | introduced | changed | model flags | holdout injected | holdout delta | holdout introduced |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for profile, row in summary["by_profile"].items():
        lines.append(
            f"| {profile} | {row['shots']} | {row['baseline_failures']} | "
            f"{row['injected_failures']} | {row['failure_delta']} | "
            f"{row['fixed_failures']} | {row['introduced_failures']} | "
            f"{row['changed_predictions']} | {row['model_flag_events']} | "
            f"{row['holdout_injected_failures']} | {row['holdout_failure_delta']} | "
            f"{row['holdout_introduced_failures']} |"
        )
    lines.extend(["", "## Challenge/Profile Detail", ""])
    lines.extend(
        [
            "| challenge | profile | shots | baseline failures | injected failures | delta | fixed | introduced | changed | model flags |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in report["profile_results"]:
        lines.append(
            f"| {row['challenge_id']} | {row['profile']} | {row['shots']} | "
            f"{row['baseline_failures']} | {row['injected_failures']} | "
            f"{row['failure_delta']} | {row['fixed_failures']} | "
            f"{row['introduced_failures']} | {row['changed_predictions']} | "
            f"{row['model_flag_events']} |"
        )
    lines.extend(["", "## Claim Boundary", ""])
    for key, value in report["claim_boundary"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Next Gate",
            "",
            "The route remains demoted until the same interface is driven by real",
            "calibrated leakage/flag observations or independently supplied hardware",
            "traces, and until holdout improvement plus all-challenge non-regression",
            "both pass under that stronger evidence.",
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
        default=Path("results/B2_hardware_like_leakage_model_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B2_hardware_like_leakage_model_gate.md"),
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
