#!/usr/bin/env python3
"""Screen a leakage-flagged erasure boundary for B2 target-volume pressure."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


METHOD = "b2_leakage_flagged_erasure_boundary_v0"
STATUS = "leakage_flagged_erasure_boundary_proxy_not_new_code_claim"


def logical_error_threshold_law(
    physical_error: float,
    distance: int,
    threshold: float,
    prefactor: float,
) -> float:
    if physical_error >= threshold:
        return float("inf")
    exponent = (distance + 1) / 2
    return prefactor * (physical_error / threshold) ** exponent


def physical_qubits_rotated_surface_code(distance: int) -> int:
    return 2 * distance * distance - 1


def target_volume(distance: int, overhead: float) -> float:
    return physical_qubits_rotated_surface_code(distance) * distance * overhead


def best_distance_for_target(
    physical_error: float,
    target_logical_error: float,
    distances: list[int],
    threshold: float,
    prefactor: float,
) -> dict:
    candidates = []
    for distance in distances:
        logical_error = logical_error_threshold_law(
            physical_error=physical_error,
            distance=distance,
            threshold=threshold,
            prefactor=prefactor,
        )
        candidates.append(
            {
                "distance": distance,
                "logical_error_rate_estimate": logical_error,
            }
        )
    feasible = [row for row in candidates if row["logical_error_rate_estimate"] <= target_logical_error]
    if feasible:
        best = min(feasible, key=lambda row: (row["distance"], row["logical_error_rate_estimate"]))
        return {"met": True, **best}
    best_available = min(candidates, key=lambda row: row["logical_error_rate_estimate"])
    return {
        "met": False,
        "distance": None,
        "logical_error_rate_estimate": None,
        "best_available_distance": best_available["distance"],
        "best_available_logical_error_rate_estimate": best_available["logical_error_rate_estimate"],
    }


def effective_baseline_error(
    physical_error: float,
    leakage_fraction: float,
    unflagged_leakage_multiplier: float,
) -> float:
    return physical_error * (1.0 + leakage_fraction * (unflagged_leakage_multiplier - 1.0))


def effective_flagged_error(
    physical_error: float,
    leakage_fraction: float,
    detection_efficiency: float,
    unflagged_leakage_multiplier: float,
    flagged_erasure_penalty: float,
) -> float:
    undetected_penalty = (1.0 - detection_efficiency) * (unflagged_leakage_multiplier - 1.0)
    detected_penalty = detection_efficiency * flagged_erasure_penalty
    return physical_error * (1.0 + leakage_fraction * (undetected_penalty + detected_penalty))


def parse_float_list(value: str) -> list[float]:
    return [float(item.strip()) for item in value.split(",") if item.strip()]


def parse_int_list(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def build_report(
    physical_errors: list[float],
    leakage_fractions: list[float],
    detection_efficiencies: list[float],
    target_logical_errors: list[float],
    distances: list[int],
    threshold: float,
    prefactor: float,
    flag_overhead: float,
    unflagged_leakage_multiplier: float,
    flagged_erasure_penalty: float,
    improvement_threshold: float,
) -> dict:
    rows = []
    improved_rows = []
    for physical_error in physical_errors:
        for leakage_fraction in leakage_fractions:
            baseline_effective_error = effective_baseline_error(
                physical_error=physical_error,
                leakage_fraction=leakage_fraction,
                unflagged_leakage_multiplier=unflagged_leakage_multiplier,
            )
            for detection_efficiency in detection_efficiencies:
                candidate_effective_error = effective_flagged_error(
                    physical_error=physical_error,
                    leakage_fraction=leakage_fraction,
                    detection_efficiency=detection_efficiency,
                    unflagged_leakage_multiplier=unflagged_leakage_multiplier,
                    flagged_erasure_penalty=flagged_erasure_penalty,
                )
                for target_logical_error in target_logical_errors:
                    baseline = best_distance_for_target(
                        physical_error=baseline_effective_error,
                        target_logical_error=target_logical_error,
                        distances=distances,
                        threshold=threshold,
                        prefactor=prefactor,
                    )
                    candidate = best_distance_for_target(
                        physical_error=candidate_effective_error,
                        target_logical_error=target_logical_error,
                        distances=distances,
                        threshold=threshold,
                        prefactor=prefactor,
                    )
                    baseline_volume = (
                        target_volume(baseline["distance"], 1.0) if baseline.get("met") else None
                    )
                    candidate_volume = (
                        target_volume(candidate["distance"], flag_overhead)
                        if candidate.get("met")
                        else None
                    )
                    volume_reduction = None
                    improved = False
                    if baseline_volume and candidate_volume:
                        volume_reduction = baseline_volume / candidate_volume
                        improved = volume_reduction >= improvement_threshold
                    row = {
                        "physical_error": physical_error,
                        "leakage_fraction": leakage_fraction,
                        "detection_efficiency": detection_efficiency,
                        "target_logical_error": target_logical_error,
                        "baseline_effective_error": baseline_effective_error,
                        "candidate_effective_error": candidate_effective_error,
                        "baseline_met": baseline.get("met"),
                        "candidate_met": candidate.get("met"),
                        "baseline_distance": baseline.get("distance"),
                        "candidate_distance": candidate.get("distance"),
                        "baseline_volume": baseline_volume,
                        "candidate_volume": candidate_volume,
                        "volume_reduction": volume_reduction,
                        "improved": improved,
                        "candidate_distance_5_or_7": candidate.get("distance") in {5, 7},
                    }
                    rows.append(row)
                    if improved:
                        improved_rows.append(row)

    reductions = [row["volume_reduction"] for row in improved_rows if row["volume_reduction"] is not None]
    d5_d7_improvements = [row for row in improved_rows if row["candidate_distance_5_or_7"]]
    min_detection = min((row["detection_efficiency"] for row in improved_rows), default=None)
    high_efficiency_rows = [
        row for row in improved_rows if row["detection_efficiency"] >= 0.9 and row["candidate_distance_5_or_7"]
    ]
    validation_errors = []
    if not improved_rows:
        validation_errors.append("no target-volume boundary improvements found")
    if not d5_d7_improvements:
        validation_errors.append("no distance-5/7 candidate improvement rows found")
    if min(distances) < 5:
        validation_errors.append("screen should not use distance-3 candidates")
    if flag_overhead < 1.0:
        validation_errors.append("flag overhead must not reduce volume by construction")

    return {
        "benchmark_id": "B2",
        "title": "B2 leakage-flagged erasure boundary",
        "status": STATUS,
        "method": METHOD,
        "model_status": "analytic_leakage_proxy_not_circuit_level_decoder",
        "parameters": {
            "physical_errors": physical_errors,
            "leakage_fractions": leakage_fractions,
            "detection_efficiencies": detection_efficiencies,
            "target_logical_errors": target_logical_errors,
            "distances": distances,
            "threshold": threshold,
            "prefactor": prefactor,
            "flag_overhead": flag_overhead,
            "unflagged_leakage_multiplier": unflagged_leakage_multiplier,
            "flagged_erasure_penalty": flagged_erasure_penalty,
            "improvement_threshold": improvement_threshold,
        },
        "summary": {
            "configuration_count": len(rows),
            "baseline_met_count": sum(1 for row in rows if row["baseline_met"]),
            "candidate_met_count": sum(1 for row in rows if row["candidate_met"]),
            "improved_volume_count": len(improved_rows),
            "distance_5_7_improved_count": len(d5_d7_improvements),
            "high_efficiency_distance_5_7_improved_count": len(high_efficiency_rows),
            "max_volume_reduction": max(reductions) if reductions else None,
            "mean_volume_reduction_on_improved": (
                sum(reductions) / len(reductions) if reductions else None
            ),
            "minimum_detection_efficiency_with_improvement": min_detection,
        },
        "claim_boundary": {
            "new_code_claimed": False,
            "threshold_claimed": False,
            "calibrated_device_claimed": False,
            "circuit_level_decoder_claimed": False,
            "reduced_rounds_used": False,
            "non_aggressive_mechanism": True,
            "distance_3_candidate_used": False,
            "what_is_supported": (
                "In this analytic proxy, flagged leakage-to-erasure information can lower the "
                "distance and target-volume proxy for some d=5/d=7 candidate rows under the same "
                "surface-code threshold-law denominator."
            ),
            "what_is_not_supported": (
                "This is not a new code, threshold estimate, circuit-level decoder result, "
                "hardware-calibrated leakage model, or solved low-overhead QEC claim."
            ),
        },
        "validation_errors": validation_errors,
        "results": rows,
    }


def write_markdown(report: dict, path: Path) -> None:
    summary = report["summary"]
    claims = report["claim_boundary"]
    improved = [row for row in report["results"] if row["improved"]]
    improved = sorted(
        improved,
        key=lambda row: (
            -(row["volume_reduction"] or 0.0),
            row["physical_error"],
            row["leakage_fraction"],
            row["target_logical_error"],
        ),
    )
    lines = [
        "# B2 Leakage-Flagged Erasure Boundary v0.1",
        "",
        f"- Status: {report['status']}",
        f"- Method: {report['method']}",
        f"- Model status: {report['model_status']}",
        f"- Configurations: {summary['configuration_count']}",
        f"- Baseline met count: {summary['baseline_met_count']}",
        f"- Candidate met count: {summary['candidate_met_count']}",
        f"- Improved target-volume rows: {summary['improved_volume_count']}",
        f"- Improved rows with candidate distance 5 or 7: {summary['distance_5_7_improved_count']}",
        f"- High-efficiency distance-5/7 improvements: {summary['high_efficiency_distance_5_7_improved_count']}",
        f"- Maximum volume reduction: {summary['max_volume_reduction']}",
        f"- Mean volume reduction on improved rows: {summary['mean_volume_reduction_on_improved']}",
        f"- Minimum detection efficiency with improvement: {summary['minimum_detection_efficiency_with_improvement']}",
        f"- Validation errors: {report['validation_errors']}",
        "",
        "## Interpretation",
        "",
        claims["what_is_supported"],
        "",
        claims["what_is_not_supported"],
        "",
        "The screen does not reduce syndrome rounds. The only volume pressure comes from a",
        "higher flagging overhead and from distance changes induced by the leakage model.",
        "",
        "## Top Improved Rows",
        "",
        "| p | leakage | detection | target | baseline d | candidate d | baseline volume | candidate volume | reduction |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for row in improved[:16]:
        lines.append(
            "| "
            f"{row['physical_error']:.3g} | "
            f"{row['leakage_fraction']:.2f} | "
            f"{row['detection_efficiency']:.2f} | "
            f"{row['target_logical_error']:.3g} | "
            f"{row['baseline_distance']} | "
            f"{row['candidate_distance']} | "
            f"{row['baseline_volume']:.2f} | "
            f"{row['candidate_volume']:.2f} | "
            f"{row['volume_reduction']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Next Gate",
            "",
            "Replace this analytic proxy with a circuit-level leakage/erasure decoder experiment",
            "or a calibrated leakage model. A stronger baseline should kill the result if the",
            "flagging overhead, decoder assumptions, or leakage correlations erase the d=5/d=7",
            "distance pressure seen here.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--physical-errors", default="0.001,0.003,0.005,0.007,0.009")
    parser.add_argument("--leakage-fractions", default="0,0.03,0.06,0.10,0.15,0.20")
    parser.add_argument("--detection-efficiencies", default="0.50,0.75,0.90,0.97")
    parser.add_argument("--targets", default="0.1,0.05,0.01,0.001")
    parser.add_argument("--distances", default="5,7,9,11,13,15")
    parser.add_argument("--threshold", type=float, default=0.01)
    parser.add_argument("--prefactor", type=float, default=0.1)
    parser.add_argument("--flag-overhead", type=float, default=1.15)
    parser.add_argument("--unflagged-leakage-multiplier", type=float, default=8.0)
    parser.add_argument("--flagged-erasure-penalty", type=float, default=0.7)
    parser.add_argument("--improvement-threshold", type=float, default=1.25)
    parser.add_argument("--json-output", type=Path, default=Path("results/B2_leakage_flagged_erasure_boundary_v0.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("research/B2_leakage_flagged_erasure_boundary.md"))
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    distances = parse_int_list(args.distances)
    if any(distance < 5 or distance % 2 == 0 for distance in distances):
        raise SystemExit("distances must be odd integers >= 5 for this non-aggressive boundary screen")

    report = build_report(
        physical_errors=parse_float_list(args.physical_errors),
        leakage_fractions=parse_float_list(args.leakage_fractions),
        detection_efficiencies=parse_float_list(args.detection_efficiencies),
        target_logical_errors=parse_float_list(args.targets),
        distances=distances,
        threshold=args.threshold,
        prefactor=args.prefactor,
        flag_overhead=args.flag_overhead,
        unflagged_leakage_multiplier=args.unflagged_leakage_multiplier,
        flagged_erasure_penalty=args.flagged_erasure_penalty,
        improvement_threshold=args.improvement_threshold,
    )
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(report, indent=2 if args.pretty else None, sort_keys=True) + "\n",
        encoding="utf-8",
    )
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
