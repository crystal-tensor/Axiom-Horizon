#!/usr/bin/env python3
"""Build a B2 per-shot decoder trace packet for the T-B2-009 input gap."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import pymatching

from b2_shot_conditioned_erasure_decoder_boundary import DEFAULT_PROFILES, posterior_leakage_probability
from b2_stim_heralded_erasure_stress import base_circuit, inject_tick_noise, wilson_interval


METHOD = "b2_per_shot_decoder_trace_packet_v0"
STATUS = "per_shot_trace_packet_available_decoder_injection_still_missing"
MODEL_STATUS = "stim_sampled_detector_bitstrings_with_synthetic_flag_events_not_posterior_decoder"
VERSION = "0.1"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def bool_bitstring(bits: np.ndarray) -> str:
    return "".join("1" if bool(bit) else "0" for bit in bits)


def stable_challenge_id(row: dict[str, Any], index: int) -> str:
    fields = [
        row.get("risk_budget"),
        row.get("profile"),
        row.get("memory_basis"),
        row.get("physical_error"),
        row.get("leakage_rate_per_tick"),
        row.get("false_positive_rate_per_tick"),
        row.get("target_logical_error"),
        row.get("candidate_distance"),
    ]
    digest = hashlib.sha1("|".join(map(str, fields)).encode("utf-8")).hexdigest()[:10]
    return f"b2_trace_{index:02d}_{digest}"


def profile_detection_efficiency(profile_name: str) -> float:
    for profile in DEFAULT_PROFILES:
        if profile["name"] == profile_name:
            return float(profile["detection_efficiency"])
    raise KeyError(f"unknown calibration profile: {profile_name}")


def select_challenge_rows(payload: dict[str, Any], max_challenges: int) -> list[dict[str, Any]]:
    rows = payload.get("adjusted_survivor_rows", [])
    strict = [
        row
        for row in rows
        if row.get("risk_budget") == "strict_decoder_penalty"
        and row.get("decoder_adjusted_surviving_d5_d7_improvement") is True
    ]
    conservative = [
        row
        for row in rows
        if row.get("risk_budget") == "conservative_decoder_penalty"
        and row.get("decoder_adjusted_surviving_d5_d7_improvement") is True
    ]
    candidates = strict or conservative or rows
    deduped: list[dict[str, Any]] = []
    seen = set()
    for row in candidates:
        key = (
            row.get("memory_basis"),
            row.get("physical_error"),
            row.get("leakage_rate_per_tick"),
            row.get("false_positive_rate_per_tick"),
            row.get("target_logical_error"),
            row.get("candidate_distance"),
            row.get("profile"),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped[:max_challenges]


def synthetic_flag_probability(row: dict[str, Any]) -> float:
    leakage_rate = float(row["leakage_rate_per_tick"])
    false_positive_rate = float(row["false_positive_rate_per_tick"])
    detection_efficiency = profile_detection_efficiency(str(row["profile"]))
    # This is deliberately conservative and clearly marked synthetic: it creates
    # detector-indexed flag events for interface testing, not calibrated leakage data.
    return min(0.25, max(0.0, detection_efficiency * leakage_rate + false_positive_rate))


def synthetic_flag_events(
    row: dict[str, Any],
    detector_count: int,
    rounds: int,
    shots: int,
    seed: int,
) -> list[list[dict[str, Any]]]:
    rng = np.random.default_rng(seed)
    p_flag = synthetic_flag_probability(row)
    posterior = posterior_leakage_probability(
        leakage_rate=float(row["leakage_rate_per_tick"]),
        false_positive_rate=float(row["false_positive_rate_per_tick"]),
        detection_efficiency=profile_detection_efficiency(str(row["profile"])),
    )
    all_events: list[list[dict[str, Any]]] = []
    for _shot in range(shots):
        flags = np.flatnonzero(rng.random(detector_count) < p_flag)
        shot_events = [
            {
                "detector_id": int(detector_id),
                "tick_index_proxy": int(detector_id % max(1, rounds)),
                "posterior_leakage_probability_given_flag": posterior,
            }
            for detector_id in flags
        ]
        all_events.append(shot_events)
    return all_events


def run_challenge(row: dict[str, Any], challenge_index: int, shots: int, seed: int) -> dict[str, Any]:
    challenge_seed = seed + challenge_index * 1009
    distance = int(row["candidate_distance"])
    basis = str(row["memory_basis"])
    physical_error = float(row["physical_error"])
    effective_erasure_rate = float(row["leakage_rate_per_tick"]) + float(
        row["false_positive_rate_per_tick"]
    )

    build_started = time.perf_counter()
    circuit = inject_tick_noise(
        base_circuit(distance=distance, physical_error=physical_error, basis=basis),
        mode="heralded_erasure_proxy",
        leakage_rate=effective_erasure_rate,
    )
    dem = circuit.detector_error_model(decompose_errors=True, approximate_disjoint_errors=True)
    matching = pymatching.Matching.from_detector_error_model(dem)
    build_seconds = time.perf_counter() - build_started

    sample_started = time.perf_counter()
    detection_events, observables = circuit.compile_detector_sampler(seed=challenge_seed).sample(
        shots,
        separate_observables=True,
    )
    sample_seconds = time.perf_counter() - sample_started

    decode_started = time.perf_counter()
    predictions = matching.decode_batch(detection_events)
    decode_seconds = time.perf_counter() - decode_started

    failures = np.any(predictions != observables, axis=1)
    failure_count = int(np.count_nonzero(failures))
    wilson_low, wilson_high = wilson_interval(failure_count, shots)
    flag_events = synthetic_flag_events(
        row=row,
        detector_count=int(circuit.num_detectors),
        rounds=distance,
        shots=shots,
        seed=challenge_seed + 17,
    )
    flag_counts = [len(events) for events in flag_events]
    challenge_id = stable_challenge_id(row, challenge_index)
    trace_rows = []
    for shot_index in range(shots):
        trace_rows.append(
            {
                "challenge_id": challenge_id,
                "shot_index": shot_index,
                "detector_bitstring": bool_bitstring(detection_events[shot_index]),
                "observable_bitstring": bool_bitstring(observables[shot_index]),
                "predicted_observable_bitstring": bool_bitstring(predictions[shot_index]),
                "logical_failure": bool(failures[shot_index]),
                "synthetic_flag_events": flag_events[shot_index],
            }
        )

    return {
        "challenge": {
            "challenge_id": challenge_id,
            "source_risk_budget": row.get("risk_budget"),
            "source_profile": row.get("profile"),
            "memory_basis": basis,
            "physical_error": physical_error,
            "leakage_rate_per_tick": float(row["leakage_rate_per_tick"]),
            "false_positive_rate_per_tick": float(row["false_positive_rate_per_tick"]),
            "effective_erasure_rate_per_tick": effective_erasure_rate,
            "target_logical_error": float(row["target_logical_error"]),
            "baseline_distance": int(row["baseline_distance"]),
            "candidate_distance": distance,
            "raw_volume_reduction_vs_baseline": row.get("raw_volume_reduction_vs_baseline"),
            "decoder_adjusted_volume_reduction": row.get("decoder_adjusted_volume_reduction"),
            "posterior_leakage_probability_given_flag": row.get(
                "posterior_leakage_probability_given_flag"
            ),
            "seed": challenge_seed,
        },
        "circuit_summary": {
            "stim_task": f"surface_code:rotated_memory_{basis}",
            "rounds": distance,
            "physical_qubits_in_stim_circuit": int(circuit.num_qubits),
            "detectors": int(circuit.num_detectors),
            "observables": int(circuit.num_observables),
            "dem_terms": len(str(dem).splitlines()),
            "matching_nodes": int(matching.num_nodes),
            "matching_edges": int(matching.num_edges),
        },
        "trace_summary": {
            "shots": shots,
            "logical_failures": failure_count,
            "logical_error_rate": failure_count / shots if shots else 0.0,
            "wilson_95_low": wilson_low,
            "wilson_95_high": wilson_high,
            "synthetic_flag_probability_per_detector": synthetic_flag_probability(row),
            "synthetic_flag_event_count": int(sum(flag_counts)),
            "mean_synthetic_flag_events_per_shot": (
                float(sum(flag_counts)) / len(flag_counts) if flag_counts else 0.0
            ),
            "max_synthetic_flag_events_per_shot": max(flag_counts) if flag_counts else 0,
            "build_seconds": build_seconds,
            "sample_seconds": sample_seconds,
            "decode_seconds": decode_seconds,
            "decoder_runtime_seconds_per_shot": decode_seconds / shots if shots else 0.0,
        },
        "shot_traces": trace_rows,
    }


def validate(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    summary = report["summary"]
    claims = report["claim_boundary"]
    if summary["challenge_count"] <= 0:
        errors.append("challenge_count must be positive")
    if summary["total_shot_traces"] != summary["challenge_count"] * summary["shots_per_challenge"]:
        errors.append("total_shot_traces must equal challenge_count * shots_per_challenge")
    if summary["per_shot_detector_bitstrings_persisted"] is not True:
        errors.append("per-shot detector bitstrings must be persisted")
    if summary["synthetic_detector_tick_flag_events_persisted"] is not True:
        errors.append("synthetic detector/tick flag events must be persisted")
    if summary["posterior_likelihood_decoder_injection_performed"] is not False:
        errors.append("this packet must not claim posterior decoder injection")
    if summary["real_hardware_or_calibrated_flag_events"] is not False:
        errors.append("this packet must not claim real hardware or calibrated flag events")
    if len(report.get("challenge_packets", [])) != summary["challenge_count"]:
        errors.append("challenge packet count mismatch")
    for packet in report.get("challenge_packets", []):
        detector_count = packet["circuit_summary"]["detectors"]
        if len(packet.get("shot_traces", [])) != summary["shots_per_challenge"]:
            errors.append(f"{packet['challenge']['challenge_id']} shot trace count mismatch")
        for trace in packet.get("shot_traces", [])[:5]:
            if len(trace.get("detector_bitstring", "")) != detector_count:
                errors.append(f"{packet['challenge']['challenge_id']} detector bitstring length mismatch")
    for key in [
        "circuit_level_decoder_claimed",
        "posterior_likelihood_decoder_claimed",
        "production_decoder_claimed",
        "threshold_claimed",
        "new_code_claimed",
        "hardware_result_claimed",
        "calibrated_device_claimed",
    ]:
        if claims.get(key) is not False:
            errors.append(f"{key} must remain False")
    if claims.get("per_shot_trace_packet_built") is not True:
        errors.append("claim boundary must disclose per-shot trace packet construction")
    return errors


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    source_payload = load_json(args.source_result)
    challenge_rows = select_challenge_rows(source_payload, max_challenges=args.max_challenges)
    packets = [
        run_challenge(row=row, challenge_index=index + 1, shots=args.shots, seed=args.seed)
        for index, row in enumerate(challenge_rows)
    ]
    total_flag_events = sum(
        packet["trace_summary"]["synthetic_flag_event_count"] for packet in packets
    )
    total_failures = sum(packet["trace_summary"]["logical_failures"] for packet in packets)
    max_detector_count = max((packet["circuit_summary"]["detectors"] for packet in packets), default=0)
    max_decode_runtime = max(
        (packet["trace_summary"]["decoder_runtime_seconds_per_shot"] for packet in packets),
        default=0.0,
    )
    summary = {
        "source_method": source_payload.get("method"),
        "source_status": source_payload.get("status"),
        "source_adjusted_survivor_rows": len(source_payload.get("adjusted_survivor_rows", [])),
        "challenge_count": len(packets),
        "shots_per_challenge": args.shots,
        "total_shot_traces": sum(len(packet["shot_traces"]) for packet in packets),
        "total_logical_failures": total_failures,
        "max_detector_count": max_detector_count,
        "total_synthetic_flag_events": total_flag_events,
        "mean_synthetic_flag_events_per_shot": (
            total_flag_events / (len(packets) * args.shots) if packets and args.shots else 0.0
        ),
        "max_decoder_runtime_seconds_per_shot": max_decode_runtime,
        "per_shot_detector_bitstrings_persisted": True,
        "stim_observable_bitstrings_persisted": True,
        "synthetic_detector_tick_flag_events_persisted": True,
        "real_hardware_or_calibrated_flag_events": False,
        "posterior_likelihood_decoder_injection_performed": False,
        "decoder_contract_delta": {
            "per_shot_syndrome_bitstrings": "available_for_sampled_stim_challenge_rows",
            "detector_tick_indexed_flag_events": "synthetic_proxy_available_not_calibrated_or_hardware",
            "posterior_likelihood_injection_api": "missing",
            "calibrated_leakage_confusion_matrix": "missing",
        },
    }
    report = {
        "benchmark_id": "B2",
        "problem_id": 22,
        "title": "B2 per-shot decoder trace packet",
        "version": VERSION,
        "last_updated": args.last_updated,
        "status": STATUS,
        "method": METHOD,
        "model_status": MODEL_STATUS,
        "toolchain": (
            "Stim generated rotated surface-code memory circuits, PyMatching detector-error-model "
            "decoder replay, and synthetic detector-indexed flag events for interface testing"
        ),
        "source_result": str(args.source_result),
        "summary": summary,
        "claim_boundary": {
            "per_shot_trace_packet_built": True,
            "stim_detector_bitstrings_sampled": True,
            "synthetic_flag_events_built": True,
            "real_flag_events_claimed": False,
            "circuit_level_decoder_claimed": False,
            "posterior_likelihood_decoder_claimed": False,
            "production_decoder_claimed": False,
            "threshold_claimed": False,
            "new_code_claimed": False,
            "hardware_result_claimed": False,
            "calibrated_device_claimed": False,
            "what_is_supported": (
                "The current B2 route now has replayable per-shot detector bitstrings, "
                "observables, baseline PyMatching predictions, and synthetic detector/tick "
                "flag events for selected strict challenge rows."
            ),
            "what_is_not_supported": (
                "This is not posterior likelihood injection, not a production decoder, not "
                "calibrated leakage evidence, not a hardware result, and not a threshold or "
                "new-code claim."
            ),
        },
        "challenge_packets": packets,
    }
    report["validation_errors"] = validate(report)
    return report


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# B2 Per-Shot Decoder Trace Packet v0.1",
        "",
        f"Status: **{report['status']}**",
        "",
        "## Summary",
        "",
        f"- Method: {report['method']}",
        f"- Model status: {report['model_status']}",
        f"- Source result: {report['source_result']}",
        f"- Challenge count: {summary['challenge_count']}",
        f"- Shots per challenge: {summary['shots_per_challenge']}",
        f"- Total shot traces: {summary['total_shot_traces']}",
        f"- Total logical failures: {summary['total_logical_failures']}",
        f"- Max detector count: {summary['max_detector_count']}",
        f"- Total synthetic flag events: {summary['total_synthetic_flag_events']}",
        f"- Mean synthetic flag events per shot: {summary['mean_synthetic_flag_events_per_shot']:.6g}",
        f"- Max decoder runtime seconds per shot: {summary['max_decoder_runtime_seconds_per_shot']:.6g}",
        f"- Per-shot detector bitstrings persisted: {summary['per_shot_detector_bitstrings_persisted']}",
        f"- Synthetic detector/tick flag events persisted: {summary['synthetic_detector_tick_flag_events_persisted']}",
        f"- Posterior likelihood decoder injection performed: {summary['posterior_likelihood_decoder_injection_performed']}",
        f"- Real hardware or calibrated flag events: {summary['real_hardware_or_calibrated_flag_events']}",
        f"- Validation errors: {report['validation_errors']}",
        "",
        "## Challenge Packets",
        "",
        "| challenge | profile | basis | p | leakage | fp | d | shots | failures | detectors | synthetic flags | Wilson high |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for packet in report["challenge_packets"]:
        challenge = packet["challenge"]
        circuit = packet["circuit_summary"]
        trace = packet["trace_summary"]
        lines.append(
            f"| {challenge['challenge_id']} | {challenge['source_profile']} | "
            f"{challenge['memory_basis']} | {challenge['physical_error']:.4g} | "
            f"{challenge['leakage_rate_per_tick']:.4g} | "
            f"{challenge['false_positive_rate_per_tick']:.4g} | "
            f"{challenge['candidate_distance']} | {trace['shots']} | "
            f"{trace['logical_failures']} | {circuit['detectors']} | "
            f"{trace['synthetic_flag_event_count']} | {trace['wilson_95_high']:.6g} |"
        )
    lines.extend(
        [
            "",
            "## Contract Delta",
            "",
        ]
    )
    for key, value in summary["decoder_contract_delta"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
        ]
    )
    for key, value in report["claim_boundary"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Next Gate",
            "",
            "Use these per-shot detector traces as the input fixture for a posterior-likelihood",
            "decoder injection experiment. The B2 route remains demoted until the decoder",
            "consumes calibrated or explicitly modeled flag likelihoods and improves strict",
            "high-purity and all-profile robustness gates.",
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
        default=Path("results/B2_posterior_weighted_decoder_risk_ledger_v0.json"),
    )
    parser.add_argument("--shots", type=int, default=192)
    parser.add_argument("--max-challenges", type=int, default=3)
    parser.add_argument("--seed", type=int, default=220632)
    parser.add_argument("--last-updated", default="2026-06-18")
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B2_per_shot_decoder_trace_packet_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B2_per_shot_decoder_trace_packet.md"),
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
